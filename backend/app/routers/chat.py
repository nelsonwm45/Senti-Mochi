from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
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

class CitationInfo(BaseModel):
    sourceNumber: int
    filename: str
    pageNumber: Optional[int]
    chunkId: str
    similarity: float

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
    
    # Log audit event
    audit_log = AuditLog(
        user_id=current_user.id,
        action="QUERY",
        resource_type="CHAT",
        metadata_={"query": request.query[:100]}  # Truncate for privacy
    )
    session.add(audit_log)
    session.commit()
    
    # Embed query
    query_embedding = rag_service.embed_query(request.query)
    
    # Convert document IDs if provided
    document_ids = None
    if request.documentIds:
        document_ids = [UUID(doc_id) for doc_id in request.documentIds]
    
    # Vector search with SECURITY CHECK - only user's documents
    chunks = rag_service.vector_search(
        query_embedding=query_embedding,
        user_id=current_user.id,  # Critical security parameter
        document_ids=document_ids,
        limit=request.maxResults
    )
    
    # Proceed even if chunks is empty to allow for general chat
    # if not chunks: ... (removed strict check)
    
    # Build context
    context = rag_service.build_context(chunks)
    
    # Generate session ID for this conversation
    session_id = uuid4()
    
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
                citations={"chunks": [str(c["id"]) for c in chunks]}
            )
            session.add(assistant_message)
            session.commit()
        
        return StreamingResponse(stream_generator(), media_type="text/plain")
    
    else:
        # Non-streaming response
        result = rag_service.generate_response(request.query, context)
        
        # Save assistant message
        assistant_message = ChatMessage(
            user_id=current_user.id,
            session_id=session_id,
            role="assistant",
            content=result["response"],
            citations={"chunks": [str(c["id"]) for c in chunks]},
            token_count=result.get("tokens_used")
        )
        session.add(assistant_message)
        session.commit()
        
        # Format citations
        citations = []
        for i, chunk in enumerate(chunks):
            citations.append(CitationInfo(
                sourceNumber=i + 1,
                filename=chunk["filename"],
                pageNumber=chunk["page_number"],
                chunkId=str(chunk["id"]),
                similarity=chunk["similarity"]
            ))
        
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
