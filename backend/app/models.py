from typing import Optional
from sqlmodel import Field, SQLModel
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Text, JSON
from uuid import UUID, uuid4
from datetime import datetime, timezone
from enum import Enum

# Enums
class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"

class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

# User Model (Enhanced)
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole = Field(default=UserRole.USER)
    tenant_id: Optional[UUID] = Field(default=None, index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClientProfile(SQLModel, table=True):
    __tablename__ = "client_profiles"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    financial_goals: Optional[str] = None
    risk_tolerance: Optional[str] = None
    assets_value: Optional[float] = None
    # Embedding for AI analysis (using pgvector)
    embedding: Optional[list[float]] = Field(default=None, sa_column=Column(Vector(384)))

# Document Model
class Document(SQLModel, table=True):
    __tablename__ = "documents"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    filename: str
    content_type: str
    file_size: int
    s3_key: str
    status: DocumentStatus = Field(default=DocumentStatus.PENDING)
    metadata_: dict = Field(default={}, sa_column=Column(JSON))
    version: int = Field(default=1)
    is_deleted: bool = Field(default=False)
    upload_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processing_started: Optional[datetime] = None
    processing_completed: Optional[datetime] = None
    error_message: Optional[str] = None

# DocumentChunk Model (for RAG)
class DocumentChunk(SQLModel, table=True):
    __tablename__ = "document_chunks"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    document_id: UUID = Field(foreign_key="documents.id", index=True)
    content: str = Field(sa_column=Column(Text))
    page_number: Optional[int] = None
    chunk_index: int
    token_count: int
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    embedding: list[float] = Field(sa_column=Column(Vector(384)))  # Local SentenceTransformer
    metadata_: dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# AuditLog Model
class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    action: str  # "UPLOAD", "QUERY", "DELETE", "DOWNLOAD"
    resource_type: str  # "DOCUMENT", "CHAT", "USER"
    resource_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    metadata_: dict = Field(default={}, sa_column=Column(JSON))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

# ChatMessage Model
class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    session_id: UUID = Field(index=True)
    role: str  # "user" or "assistant"
    content: str = Field(sa_column=Column(Text))
    citations: dict = Field(default={}, sa_column=Column(JSON))
    token_count: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
