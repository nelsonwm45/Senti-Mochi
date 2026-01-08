from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.database import get_session
from app.models import Document, User, DocumentStatus, AuditLog
from app.auth import get_current_user
from app.services.storage import S3StorageService
from app.tasks.document_tasks import process_document_task
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Response models using camelCase
class DocumentResponse(BaseModel):
    id: str
    userId: str
    filename: str
    contentType: str
    fileSize: int
    status: str
    uploadDate: str
    processingStarted: Optional[str] = None
    processingCompleted: Optional[str] = None
    errorMessage: Optional[str] = None
    
    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Upload a document for processing
    
    - Accepts PDF, DOCX files
    - Queues async processing job
    - Returns document metadata
    """
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"  # Added for easier testing
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not supported. Use PDF, DOCX, or TXT."
        )
    
    # Validate file size (max 50MB)
    file_bytes = await file.read()
    file_size = len(file_bytes)
    if file_size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 50MB limit"
        )
    
    # Upload to S3
    storage = S3StorageService()
    s3_key = storage.upload_file(file.file, file.filename, file.content_type)
    
    # Create document record
    document = Document(
        user_id=current_user.id,
        filename=file.filename,
        content_type=file.content_type,
        file_size=file_size,
        s3_key=s3_key,
        status=DocumentStatus.PENDING
    )
    
    session.add(document)
    session.commit()
    session.refresh(document)
    
    # Log audit event
    audit_log = AuditLog(
        user_id=current_user.id,
        action="UPLOAD",
        resource_type="DOCUMENT",
        resource_id=document.id,
        metadata_={"filename": file.filename, "size": file_size}
    )
    session.add(audit_log)
    session.commit()
    
    # Queue processing task
    process_document_task.delay(str(document.id))
    
    return DocumentResponse(
        id=str(document.id),
        userId=str(document.user_id),
        filename=document.filename,
        contentType=document.content_type,
        fileSize=document.file_size,
        status=document.status.value,
        uploadDate=document.upload_date.isoformat(),
        processingStarted=document.processing_started.isoformat() if document.processing_started else None,
        processingCompleted=document.processing_completed.isoformat() if document.processing_completed else None,
        errorMessage=document.error_message
    )

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List user's documents with pagination and filtering"""
    query = select(Document).where(
        Document.user_id == current_user.id,
        Document.is_deleted == False
    )
    
    if status:
        query = query.where(Document.status == status)
    
    # Get total count
    total_query = select(func.count()).select_from(Document).where(
        Document.user_id == current_user.id,
        Document.is_deleted == False
    )
    total = session.exec(total_query).one()
    
    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(Document.upload_date.desc())
    documents = session.exec(query).all()
    
    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=str(doc.id),
                userId=str(doc.user_id),
                filename=doc.filename,
                contentType=doc.content_type,
                fileSize=doc.file_size,
                status=doc.status.value,
                uploadDate=doc.upload_date.isoformat(),
                processingStarted=doc.processing_started.isoformat() if doc.processing_started else None,
                processingCompleted=doc.processing_completed.isoformat() if doc.processing_completed else None,
                errorMessage=doc.error_message
            )
            for doc in documents
        ],
        total=total
    )

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get document details"""
    document = session.get(Document, document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Security check
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return DocumentResponse(
        id=str(document.id),
        userId=str(document.user_id),
        filename=document.filename,
        contentType=document.content_type,
        fileSize=document.file_size,
        status=document.status.value,
        uploadDate=document.upload_date.isoformat(),
        processingStarted=document.processing_started.isoformat() if document.processing_started else None,
        processingCompleted=document.processing_completed.isoformat() if document.processing_completed else None,
        errorMessage=document.error_message
    )

@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Soft delete a document"""
    document = session.get(Document, document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Security check
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Soft delete
    document.is_deleted = True
    session.add(document)
    
    # Log audit event
    audit_log = AuditLog(
        user_id=current_user.id,
        action="DELETE",
        resource_type="DOCUMENT",
        resource_id=document.id,
        metadata_={"filename": document.filename}
    )
    session.add(audit_log)
    session.commit()
    
    return {"message": "Document deleted successfully"}

@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Reprocess a failed document"""
    document = session.get(Document, document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Security check
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if document.status != DocumentStatus.FAILED:
        raise HTTPException(
            status_code=400,
            detail="Only failed documents can be reprocessed"
        )
    
    # Reset status and queue processing
    document.status = DocumentStatus.PENDING
    document.error_message = None
    session.add(document)
    session.commit()
    
    process_document_task.delay(str(document.id))
    
    return {"message": "Document reprocessing queued"}
