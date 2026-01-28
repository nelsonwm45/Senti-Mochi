from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel

from app.database import get_session
from app.models import User, ChatMessage, AuditLog
from app.auth import get_current_user
from app.services.rag import RAGService

router = APIRouter(prefix="/chat", tags=["chat"])

# Request/Response models using camelCase
class QueryRequest(BaseModel):
    query: str
    documentIds: Optional[List[str]] = None
    maxResults: int = 5
    stream: bool = False
    sessionId: Optional[str] = None

class CitationInfo(BaseModel):
    sourceNumber: int
    filename: str
    pageNumber: Optional[int]
    chunkId: str
    similarity: float
    text: str
    url: Optional[str] = None
    startLine: Optional[int] = None
    endLine: Optional[int] = None

class QueryResponse(BaseModel):
    response: str
    citations: List[CitationInfo]
    sessionId: str
    tokensUsed: Optional[int] = None

class ChatHistoryResponse(BaseModel):
    messages: List[dict]
    total: int

@router.post("/query")
async def query(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Agentic RAG chat query endpoint.

    Uses a LangGraph multi-agent workflow:
      Router (Gemini Flash) -> [Domain Agents] -> Token Pruner -> Generation (Groq Llama-3)

    Falls back to the legacy naive RAG path if the agentic pipeline errors.
    """
    rag_service = RAGService()

    # ── Session ID ──────────────────────────────────────────────────────
    if request.sessionId and request.sessionId not in ("null", "undefined"):
        try:
            session_id = UUID(request.sessionId)
        except ValueError:
            session_id = uuid4()
    else:
        session_id = uuid4()

    # ── Session message limit ───────────────────────────────────────────
    MAX_MESSAGES_PER_SESSION = 50
    message_count = session.exec(
        select(func.count()).select_from(ChatMessage).where(
            ChatMessage.session_id == session_id
        )
    ).one()

    if message_count >= MAX_MESSAGES_PER_SESSION:
        raise HTTPException(
            status_code=429,
            detail=f"Session has reached maximum message limit ({MAX_MESSAGES_PER_SESSION}). Please start a new chat."
        )

    # ── Audit log ───────────────────────────────────────────────────────
    audit_log = AuditLog(
        user_id=current_user.id,
        action="QUERY",
        resource_type="CHAT",
        resource_id=session_id,
        metadata_={"query": request.query[:100]}
    )
    session.add(audit_log)
        try:
            session.commit()
        except Exception as audit_err:
            print(f"[QUERY] Audit log commit failed: {audit_err}")
            session.rollback()

    # ── Embed query ─────────────────────────────────────────────────────
    query_embedding = rag_service.embed_query(request.query)

    # ── Detect companies (with context lookback) ────────────────────────
    from app.services.company_service import company_service
    companies = company_service.find_companies_by_text(request.query, session)

    last_msg = session.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .where(ChatMessage.role == "user")
        .order_by(ChatMessage.created_at.desc())
        .limit(1)
    ).first()

    if last_msg:
        prev_companies = company_service.find_companies_by_text(last_msg.content, session)
        if prev_companies:
            if companies is None:
                companies = []
            existing_ids = {c.id for c in companies}
            for prev_comp in prev_companies:
                if prev_comp.id not in existing_ids:
                    companies.append(prev_comp)
                    existing_ids.add(prev_comp.id)

    company_ids = [c.id for c in companies] if companies else None

    # ── Chat history ────────────────────────────────────────────────────
    history_msgs = session.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    ).all()
    history_msgs.reverse()

    chat_history = [
        {"role": msg.role, "content": msg.content}
        for msg in history_msgs
    ]

    # ── Save user message ───────────────────────────────────────────────
    user_message = ChatMessage(
        user_id=current_user.id,
        session_id=session_id,
        role="user",
        content=request.query
    )
    session.add(user_message)
        try:
            session.commit()
        except Exception as msg_err:
            print(f"[QUERY] User message commit failed: {msg_err}")
            session.rollback()

    # ── Document IDs ────────────────────────────────────────────────────
    document_ids = None
    if request.documentIds:
        document_ids = [UUID(doc_id) for doc_id in request.documentIds]

    # ====================================================================
    # AGENTIC RAG PIPELINE
    # ====================================================================
    try:
        from app.services.chat_workflow import run_chat_agentic

        agentic_result = run_chat_agentic(
            query=request.query,
            user_id=str(current_user.id),
            user_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
            analysis_persona=current_user.analysis_persona.value if hasattr(current_user.analysis_persona, "value") else str(current_user.analysis_persona),
            query_embedding=query_embedding,
            chat_history=chat_history,
            company_ids=[str(c) for c in company_ids] if company_ids else None,
            document_ids=[str(d) for d in document_ids] if document_ids else None,
            max_results=request.maxResults,
        )

        response_text = agentic_result.get("response", "")
        all_chunks = agentic_result.get("retrieved_docs", [])
        tokens_used = agentic_result.get("token_count")

    except Exception as e:
        # ── Fallback to legacy naive RAG ────────────────────────────────
        print(f"[Agentic RAG] Pipeline failed, falling back to legacy: {e}")

        chunks = rag_service.vector_search(
            query_embedding=query_embedding,
            user_id=current_user.id,
            document_ids=document_ids,
            company_ids=company_ids,
            limit=request.maxResults
        )

        try:
            structured_chunks = (
                rag_service.get_structured_chunks_for_companies(companies, session, query_embedding=query_embedding)
                if companies else []
            )
        except Exception:
            structured_chunks = []

        all_chunks = structured_chunks + chunks
        context = rag_service.build_context(all_chunks)

        result = rag_service.generate_response(
            request.query, context, chat_history=chat_history
        )
        response_text = result["response"]
        tokens_used = result.get("tokens_used")

    # ── Reindex citations ───────────────────────────────────────────────
    response_text, all_chunks = rag_service.reindex_citations(response_text, all_chunks)

    # ── Build citation objects ──────────────────────────────────────────
    citations = []
    for i, chunk in enumerate(all_chunks):
        citations.append(CitationInfo(
            sourceNumber=i + 1,
            filename=chunk.get("filename", "Unknown"),
            pageNumber=chunk.get("page_number"),
            chunkId=str(chunk.get("id", "")),
            similarity=chunk.get("similarity", 0.0),
            text=chunk.get("content", ""),
            startLine=chunk.get("start_line"),
            endLine=chunk.get("end_line"),
            url=chunk.get("url")
        ))

    # ── Save assistant message ──────────────────────────────────────────
    assistant_message = ChatMessage(
        user_id=current_user.id,
        session_id=session_id,
        role="assistant",
        content=response_text,
        citations={"sources": [c.dict() for c in citations]},
        token_count=tokens_used
    )
    session.add(assistant_message)
        try:
            session.commit()
        except Exception as save_err:
            print(f"[QUERY] Assistant message commit failed: {save_err}")
            session.rollback()

    # ── Handle streaming (buffered re-index) vs non-streaming ───────────
    if request.stream:
        async def stream_generator():
            yield response_text
        return StreamingResponse(stream_generator(), media_type="text/plain")

    return QueryResponse(
        response=response_text,
        citations=citations,
        sessionId=str(session_id),
        tokensUsed=tokens_used
    )

@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_session)
):
    """Get chat history for user or specific session"""
    query = select(ChatMessage).where(ChatMessage.user_id == current_user.id)
    
    if session_id:
        query = query.where(ChatMessage.session_id == UUID(session_id))
    
    # Get total count
    total_query = select(func.count()).select_from(ChatMessage).where(
        ChatMessage.user_id == current_user.id
    )
    if session_id:
        total_query = total_query.where(ChatMessage.session_id == UUID(session_id))
    
    total = db_session.exec(total_query).one()
    
    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(ChatMessage.created_at.desc())
    messages = db_session.exec(query).all()
    
    return ChatHistoryResponse(
        messages=[
            {
                "id": str(msg.id),
                "sessionId": str(msg.session_id),
                "role": msg.role,
                "content": msg.content,
                "citations": msg.citations,
                "createdAt": msg.created_at.isoformat()
            }
            for msg in messages
        ],
        total=total
    )

@router.post("/feedback")
async def submit_feedback(
    message_id: str,
    rating: int,  # 1 for thumbs up, -1 for thumbs down
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Submit feedback on a chat response"""
    message = session.get(ChatMessage, UUID(message_id))
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Security check
    if message.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Log feedback as audit event
    audit_log = AuditLog(
        user_id=current_user.id,
        action="FEEDBACK",
        resource_type="CHAT",
        resource_id=message.id,
        metadata_={"rating": rating}
    )
    session.add(audit_log)
    session.commit()
    
    return {"message": "Feedback recorded successfully"}

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a chat session and all its messages"""
    try:
        sess_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")
        
    # Check if session exists and belongs to user
    # We check if there are ANY messages for this session/user
    statement = select(ChatMessage).where(
        ChatMessage.session_id == sess_uuid,
        ChatMessage.user_id == current_user.id
    )
    result = session.exec(statement).first()
    
    if not result:
        # Either session doesn't exist or belongs to another user
        # We can just return success to be idempotent or 404
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Delete all messages
    delete_stmt = select(ChatMessage).where(
        ChatMessage.session_id == sess_uuid,
        ChatMessage.user_id == current_user.id
    )
    messages = session.exec(delete_stmt).all()
    for msg in messages:
        session.delete(msg)
        
    # Log deletion
    audit_log = AuditLog(
        user_id=current_user.id,
        action="DELETE",
        resource_type="CHAT",
        resource_id=sess_uuid
    )
    session.add(audit_log)
    
    session.commit()
    return {"message": "Session deleted successfully"}
