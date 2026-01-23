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
    # Instead, we will buffer the stream, re-index, and then yield the result.
    
    rag_service = RAGService()
    
    # Generate/Resolve session ID early for context lookback
    if request.sessionId and request.sessionId != "null" and request.sessionId != "undefined":
        try:
            session_id = UUID(request.sessionId)
        except ValueError:
            session_id = uuid4()
    else:
        session_id = uuid4()
    
    # Check session message limit to prevent overload
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
    
    # Context Lookback: Check previous user message for additional context
    # This handles comparison questions like "How does it compare to Y?" (where X was previous)
    
    last_msg = session.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .where(ChatMessage.role == "user")
        .order_by(ChatMessage.created_at.desc())
        .limit(1)
    ).first()
    
    if last_msg:
         # We found a previous message. Let's see if it had companies.
         print(f"Context Lookback: Checking previous message '{last_msg.content[:50]}...'")
         prev_companies = company_service.find_companies_by_text(last_msg.content, session)
         
         if prev_companies:
             print(f"Context Lookback: Found previous companies: {[c.name for c in prev_companies]}")
             
             # Initialize companies list if None
             if companies is None:
                 companies = []
                 
             # Merge lists, avoiding duplicates
             existing_ids = {c.id for c in companies}
             for prev_comp in prev_companies:
                 if prev_comp.id not in existing_ids:
                     companies.append(prev_comp)
                     existing_ids.add(prev_comp.id)
    
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
        if companies:
            # Pass query_embedding to enable Semantic News Search
            structured_chunks = rag_service.get_structured_chunks_for_companies(
                companies, 
                session, 
                query_embedding=query_embedding
            )
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
    
    # Fetch recent chat history for context
    # Limit to last 10 messages to avoid overflowing context window

    
    # Sort by time asc for conversation flow
    # If we fetch all, just sort. If we limit, use subquery or Python slice.
    # Simple approach: fetch all (sessions usually short) or fetch last 20
    # Let's fetch last 10 by time descending, then reverse in Python
    history_msgs = session.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    ).all()
    history_msgs.reverse() # Now in chronological order
    
    chat_history = [
        {"role": msg.role, "content": msg.content}
        for msg in history_msgs
    ]
    
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
            # Pass chat_history to stream
            async for chunk in rag_service.generate_response_stream(
                request.query, 
                context, 
                chat_history=chat_history
            ):
                full_response += chunk
                # We buffer everything, do not yield partial chunks yet if we want to reindex
                # If we yielded here, we couldn't change "Source 15" to "Source 1" later in the stream easily
            
            # Reindex citations (modifies full_response and reorders all_chunks)
            # This logic was previously only in the non-streaming block
            new_text, reordered_chunks = rag_service.reindex_citations(full_response, all_chunks)
            
            # Yield the full re-indexed text
            yield new_text
            
            # Save assistant message AFTER streaming completes
            # Note: We must save the *reordered* chunks in the citations
            
            # Format citations for storage
            citations = []
            for i, chunk in enumerate(reordered_chunks):
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

            assistant_message = ChatMessage(
                user_id=current_user.id,
                session_id=session_id,
                role="assistant",
                content=new_text,
                citations={"sources": [c.dict() for c in citations]}
            )
            session.add(assistant_message)
            session.commit()
        
        return StreamingResponse(stream_generator(), media_type="text/plain")
    
    else:
        # Non-streaming response
        # Pass chat_history
        try:
            result = rag_service.generate_response(
                request.query, 
                context, 
                chat_history=chat_history
            )
        except Exception as e:
            # Handle rate limits specifically if possible, otherwise generic error
            error_msg = str(e)
            if "429" in error_msg or "Rate limit" in error_msg:
                raise HTTPException(
                    status_code=429,
                    detail="AI model rate limit exceeded. Please try again in 1 hour."
                )
            print(f"Error generating response: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing request: {str(e)}"
            )
        
        # Reindex citations to be sequential (1, 2, 3...)
        # This reorders all_chunks so that the first cited source becomes Source 1 (chunks[0])
        result["response"], all_chunks = rag_service.reindex_citations(result["response"], all_chunks)
        
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
