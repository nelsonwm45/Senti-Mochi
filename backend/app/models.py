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
    RM = "RM"
    ANALYST = "ANALYST"
    RISK = "RISK"

class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

# Tenant Model
class Tenant(SQLModel, table=True):
    __tablename__ = "tenants"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    storage_quota_gb: int = Field(default=10)
    monthly_token_limit: int = Field(default=100000)
    is_active: bool = Field(default=True)
    settings: dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    feedback_score: int = Field(default=0) # 0=None, 1=Up, -1=Down
    feedback_text: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Workflow Model
class Workflow(SQLModel, table=True):
    __tablename__ = "workflows"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    name: str
    trigger: dict = Field(default={}, sa_column=Column(JSON)) # {"type": "DOCUMENT_UPLOADED", "filters": {...}}
    actions: list[dict] = Field(default=[], sa_column=Column(JSON)) # [{"type": "EXTRACT_TOTAL"}, {"type": "WEBHOOK"}]
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# --- Financial Platform Models ---

class Company(SQLModel, table=True):
    __tablename__ = "companies"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    ticker: str = Field(unique=True, index=True)
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    market_cap: Optional[float] = None
    summary: Optional[str] = Field(sa_column=Column(Text))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Enum for Filing Types
class FilingType(str, Enum):
    ANNUAL_REPORT = "ANNUAL_REPORT"
    QUARTERLY_REPORT = "QUARTERLY_REPORT"
    FINANCIAL_STATEMENT = "FINANCIAL_STATEMENT"
    GENERAL_ANNOUNCEMENT = "GENERAL_ANNOUNCEMENT"
    OTHER = "OTHER"

class Filing(SQLModel, table=True):
    __tablename__ = "filings"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    company_id: UUID = Field(foreign_key="companies.id", index=True)
    document_id: Optional[UUID] = Field(foreign_key="documents.id", default=None)  # Link to existing Document for storage/chunks
    type: FilingType = Field(default=FilingType.GENERAL_ANNOUNCEMENT)
    publication_date: datetime
    content_summary: Optional[str] = Field(sa_column=Column(Text))
    pdf_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NewsArticle(SQLModel, table=True):
    __tablename__ = "news_articles"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    company_id: Optional[UUID] = Field(foreign_key="companies.id", default=None, index=True)
    source_name: str
    title: str
    url: str = Field(unique=True)
    published_at: datetime
    content: str = Field(sa_column=Column(Text))
    article_content: Optional[str] = Field(default=None, sa_column=Column(Text))
    summary: Optional[str] = Field(default=None, sa_column=Column(Text))
    sentiment_score: Optional[float] = None # Denormalized for quick access
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SentimentAnalysis(SQLModel, table=True):
    __tablename__ = "sentiment_analysis"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # Polymorphic linking could be done via separate nullable FKs or a generic content_type/object_id approach.
    # For simplicity/speed in Postgres, individual FKs are often cleaner.
    news_article_id: Optional[UUID] = Field(foreign_key="news_articles.id", default=None)
    filing_id: Optional[UUID] = Field(foreign_key="filings.id", default=None)
    
    score: str # "Positive", "Neutral", "Adverse"
    confidence_score: float
    rationale: str = Field(sa_column=Column(Text))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FinancialRatio(SQLModel, table=True):
    __tablename__ = "financial_ratios"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    company_id: UUID = Field(foreign_key="companies.id", index=True)
    filing_id: Optional[UUID] = Field(foreign_key="filings.id", default=None)
    period: str # e.g. "2023 Q4", "2024 FY"
    ratio_name: str # e.g. "Current Ratio"
    value: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Alert(SQLModel, table=True):
    __tablename__ = "alerts"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    condition: dict = Field(default={}, sa_column=Column(JSON)) # e.g. {"sentiment": "Adverse", "keyword": "Resignation"}
    is_active: bool = Field(default=True)
    last_triggered_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Watchlist(SQLModel, table=True):
    __tablename__ = "watchlists"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    company_id: UUID = Field(foreign_key="companies.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
