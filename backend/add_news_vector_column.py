from sqlmodel import text, Session
from app.database import engine

def add_column():
    print("Adding embedding column to news_chunks table...")
    with Session(engine) as session:
        try:
            # Check if column exists first to avoid error
            check_sql = text("SELECT column_name FROM information_schema.columns WHERE table_name='news_chunks' AND column_name='embedding';")
            result = session.exec(check_sql).first()
            
            if result:
                print("Column 'embedding' already exists. Skipping.")
                return

            # Add column
            session.exec(text("ALTER TABLE news_chunks ADD COLUMN embedding vector(384);"))
            session.commit()
            print("Successfully added 'embedding' column.")
        except Exception as e:
            print(f"Error: {e}")
            session.rollback()

if __name__ == "__main__":
    add_column()
