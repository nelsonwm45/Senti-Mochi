from typing import Optional
from sqlmodel import Field, SQLModel
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None

class ClientProfile(SQLModel, table=True):
    __tablename__ = "client_profiles"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    financial_goals: Optional[str] = None
    risk_tolerance: Optional[str] = None
    assets_value: Optional[float] = None
    # Embedding for AI analysis (using pgvector)
    embedding: Optional[list[float]] = Field(default=None, sa_column=Column(Vector(1536)))
