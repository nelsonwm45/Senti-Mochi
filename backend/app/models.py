from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
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
    
    watchlist: list["Watchlist"] = Relationship(back_populates="user")

class ClientProfile(SQLModel, table=True):
    __tablename__ = "client_profiles"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    financial_goals: Optional[str] = None
    risk_tolerance: Optional[str] = None
    assets_value: Optional[float] = None
    # Embedding for AI analysis (using pgvector)
    embedding: Optional[list[float]] = Field(default=None, sa_column=Column(Vector(384)))

class Company(SQLModel, table=True):
    __tablename__ = "companies"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    ticker: str = Field(unique=True, index=True)
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    website_url: Optional[str] = None
    
    # Relationships
    documents: list["Document"] = Relationship(back_populates="company")
    watchlists: list["Watchlist"] = Relationship(back_populates="company")
    financials: list["FinancialStatement"] = Relationship(back_populates="company")
    news_articles: list["NewsArticle"] = Relationship(back_populates="company")
    analysis_reports: list["AnalysisReport"] = Relationship(back_populates="company")

class FinancialStatement(SQLModel, table=True):
    __tablename__ = "financial_statements"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    company_id: UUID = Field(foreign_key="companies.id", index=True)
    period: str  # "2023-12-31"
    statement_type: str  # "balance_sheet", "income_statement", "cash_flow"
    data: dict = Field(default={}, sa_column=Column(JSON))
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    company: "Company" = Relationship(back_populates="financials")

class NewsArticle(SQLModel, table=True):
    __tablename__ = "news_articles"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    company_id: UUID = Field(foreign_key="companies.id", index=True)
    source: str # "bursa", "star", "nst"
    native_id: str = Field(unique=True, index=True) # Original ID from source - UNIQUE to prevent duplicates
    title: str
    url: str
    published_at: datetime
    content: Optional[str] = Field(sa_column=Column(Text))
    
    # Sentiment Analysis Fields
    sentiment_score: Optional[float] = None  # -1.0 to 1.0 (negative to positive)
    sentiment_label: Optional[str] = None    # "positive", "negative", "neutral"
    sentiment_confidence: Optional[float] = None  # 0.0 to 1.0
    analyzed_at: Optional[datetime] = None   # When sentiment was calculated
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    company: "Company" = Relationship(back_populates="news_articles")
    chunks: list["NewsChunk"] = Relationship(back_populates="news_article")

class NewsChunk(SQLModel, table=True):
    __tablename__ = "news_chunks"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    news_id: UUID = Field(foreign_key="news_articles.id", index=True)
    content: str = Field(sa_column=Column(Text))
    chunk_index: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    embedding: list[float] = Field(default=None, sa_column=Column(Vector(384)))  # Local SentenceTransformer

    news_article: "NewsArticle" = Relationship(back_populates="chunks")

# Watchlist Model
class Watchlist(SQLModel, table=True):
    __tablename__ = "watchlists"
    user_id: UUID = Field(foreign_key="users.id", primary_key=True)
    company_id: UUID = Field(foreign_key="companies.id", primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: "User" = Relationship(back_populates="watchlist")
    company: "Company" = Relationship(back_populates="watchlists")

# Document Model
class Document(SQLModel, table=True):
    __tablename__ = "documents"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    company_id: Optional[UUID] = Field(default=None, foreign_key="companies.id", index=True)
    company: Optional[Company] = Relationship(back_populates="documents")
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



# AnalysisReport Model
class AnalysisReport(SQLModel, table=True):
    __tablename__ = "analysis_reports"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    company_id: UUID = Field(foreign_key="companies.id", index=True)
    current_price: Optional[float] = None
    rating: str  # BUY, SELL, HOLD
    confidence_score: int  # 0-100
    summary: str = Field(sa_column=Column(Text)) # Markdown text
    bull_case: str = Field(sa_column=Column(Text))
    bear_case: str = Field(sa_column=Column(Text))
    risk_factors: str = Field(sa_column=Column(Text))
    
    # ESG Analysis Data (JSON) to match Frontend UI
    esg_analysis: dict = Field(default={}, sa_column=Column(JSON))

    # Financial Analysis Data (JSON)
    financial_analysis: dict = Field(default={}, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Store agent steps/debate logs for transparency
    agent_logs: list[dict] = Field(default=[], sa_column=Column(JSON))

    company: "Company" = Relationship(back_populates="analysis_reports")
