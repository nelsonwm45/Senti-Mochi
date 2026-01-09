import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from sqlmodel import SQLModel
from app.database import engine
from app.models import User, Document, DocumentChunk, ChatMessage, AuditLog, ClientProfile

def reset_db():
    print("Resetting database...")
    # Drop all tables
    SQLModel.metadata.drop_all(engine)
    print("Tables dropped.")
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    print("Tables recreated successfully.")

if __name__ == "__main__":
    reset_db()
