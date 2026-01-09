
from sqlalchemy import text
from app.database import engine

def check_dimension():
    with engine.connect() as conn:
        # Check column definition in Postgres
        result = conn.execute(text("SELECT atttypmod FROM pg_attribute WHERE attrelid = 'document_chunks'::regclass AND attname = 'embedding';"))
        dim = result.scalar()
        print(f"Embedding Layout: {dim}") # 1536 dimensions -> 1536, 384 -> 384. (Note: pgvector stores dim as typmod)

if __name__ == "__main__":
    check_dimension()
