
from sqlmodel import Session, select, func
from app.database import engine
from app.models import User, Document, DocumentChunk

def check_db():
    with Session(engine) as session:
        user_count = session.exec(select(func.count(User.id))).one()
        doc_count = session.exec(select(func.count(Document.id))).one()
        chunk_count = session.exec(select(func.count(DocumentChunk.id))).one()
        
        print(f"Users: {user_count}")
        users = session.exec(select(User)).all()
        for u in users:
            print(f"User: {u.email}, ID: {u.id}")
            
        print(f"Documents: {doc_count}")
        docs = session.exec(select(Document)).all()
        for d in docs:
            print(f"Doc: {d.filename}, ID: {d.id}, Owner: {d.user_id}, Status: {d.status}")

        print(f"Chunks: {chunk_count}")
        chunks = session.exec(select(DocumentChunk).limit(3)).all()
        for c in chunks:
            print(f"Chunk: {c.content[:50]}... (Token count: {c.token_count})")
            print(f"Embedding Len: {len(c.embedding)}")

if __name__ == "__main__":
    check_db()
