from sqlmodel import Session, select
from app.database import engine
from app.models import DocumentChunk
import sys

def inspect_chunks():
    with Session(engine) as session:
        statement = select(DocumentChunk).order_by(DocumentChunk.created_at.desc()).limit(10)
        chunks = session.exec(statement).all()
        
        print(f"Found {len(chunks)} recent chunks")
        for chunk in chunks:
            print(f"ID: {chunk.id}")
            print(f"Document ID: {chunk.document_id}")
            print(f"Lines: {chunk.start_line} - {chunk.end_line}")
            print(f"Content Preview: {chunk.content[:50]}...")
            print("-" * 30)

if __name__ == "__main__":
    inspect_chunks()
