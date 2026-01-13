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

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

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
    RAG-powered chat query endpoint
    
    - Embeds user query
    - Performs vector similarity search (security: only user's documents)
    - Generates LLM response with citations
    - Optionally streams response
    """
    rag_service = RAGService()
    
    # Generate/Resolve session ID early for context lookback
    if request.sessionId:
        try:
            session_id = UUID(request.sessionId)
        except ValueError:
            session_id = uuid4()
    else:
        session_id = uuid4()
    
    # Log audit event
    audit_log = AuditLog(
        user_id=current_user.id,
        action="QUERY",
        resource_type="CHAT",
        resource_id=session_id, # Link audit to session
        metadata_={"query": request.query[:100]}
    )
    session.add(audit_log)
    session.commit()
    
    # Embed query
    query_embedding = rag_service.embed_query(request.query)
    
    # Convert document IDs if provided
    document_ids = None
    if request.documentIds:
        document_ids = [UUID(doc_id) for doc_id in request.documentIds]
    
    # Detect Companies for context filtering
    from app.services.company_service import company_service
    companies = company_service.find_companies_by_text(request.query, session)
    
    # Context Lookback: If no companies found, check previous user message
    # This handles follow-up questions like "Which one is better?"
    if not companies:
         last_msg = session.exec(
             select(ChatMessage)
             .where(ChatMessage.session_id == session_id)
             .where(ChatMessage.role == "user")
             .order_by(ChatMessage.created_at.desc())
         ).first()
         
         if last_msg:
             print(f"Context Lookback: Checking previous message '{last_msg.content[:50]}...'")
             companies = company_service.find_companies_by_text(last_msg.content, session)
    
    company_ids = [c.id for c in companies] if companies else None
    
    # Vector search with SECURITY CHECK - only user's documents
    # And optional company filtering
    chunks = rag_service.vector_search(
        query_embedding=query_embedding,
        user_id=current_user.id,  # Critical security parameter
        document_ids=document_ids,
        company_ids=company_ids,
        limit=request.maxResults
    )
    
    # Proceed even if chunks is empty to allow for general chat
    # if not chunks: ... (removed strict check)
    
    # Build structured chunks from DB (Financials, News)
    # These effectively act as "Source 1", "Source 2" etc.
    try:
        # Pass companies directly if we have them, otherwise query
        if companies:
            # We already have the companies, lets fetch chunks for them directly
            # But get_structured_chunks takes query. 
            # Let's refactor get_structured_chunks or just pass the query?
            # Passing the original query "Which is better" won't work if we used lookback.
            # We should pass the NAMES of the found companies or update get_structured_chunks to accept companies list.
            # For minimal change, let's construct a synthetic query or update the service.
            # Updating service is cleaner.
            structured_chunks = rag_service.get_structured_chunks_for_companies(companies, session)
        else:
             structured_chunks = []
    except Exception as e:
        print(f"Error fetching structured chunks: {e}")
        structured_chunks = []
    
    # Combine chunks: Structured first (priority), then Vector Results
    all_chunks = structured_chunks + chunks
    
    # Build context from ALL chunks
    context = rag_service.build_context(all_chunks)
    
    # Session ID logic removed from here (moved to top)
    
    # Save user message
    user_message = ChatMessage(
        user_id=current_user.id,
        session_id=session_id,
        role="user",
        content=request.query
    )
    session.add(user_message)
    session.commit()
    
    # Handle streaming vs non-streaming
    if request.stream:
        # Streaming response
        async def stream_generator():
            full_response = ""
            async for chunk in rag_service.generate_response_stream(request.query, context):
                full_response += chunk
                yield chunk
            
            # Save assistant message after streaming completes
            assistant_message = ChatMessage(
                user_id=current_user.id,
                session_id=session_id,
                role="assistant",
                content=full_response,
                citations={"chunks": [str(c["id"]) for c in all_chunks]}
            )
            session.add(assistant_message)
            session.commit()
        
        return StreamingResponse(stream_generator(), media_type="text/plain")
    
    else:
        # Non-streaming response
        result = rag_service.generate_response(request.query, context)
        
        # Format citations
        citations = []
        for i, chunk in enumerate(all_chunks):
            citations.append(CitationInfo(
                sourceNumber=i + 1,
                filename=chunk["filename"],
                pageNumber=chunk["page_number"],
                chunkId=str(chunk["id"]),
                similarity=chunk["similarity"],
                text=chunk["content"],
                startLine=chunk.get("start_line"),
                endLine=chunk.get("end_line")
            ))

        # Save assistant message
        assistant_message = ChatMessage(
            user_id=current_user.id,
            session_id=session_id,
            role="assistant",
            content=result["response"],
            # Save full citation details for history reconstruction
            citations={"sources": [c.dict() for c in citations]}, 
            token_count=result.get("tokens_used")
        )
        session.add(assistant_message)
        session.commit()
        
        # Format citations (already done above)
        
        return QueryResponse(
            response=result["response"],
            citations=citations,
            sessionId=str(session_id),
            tokensUsed=result.get("tokens_used")
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
