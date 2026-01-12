from sqlmodel import Session, text
from app.database import engine

def add_summary_column():
    with Session(engine) as session:
        print("Adding summary column to news_articles...")
        try:
            session.exec(text("ALTER TABLE news_articles ADD COLUMN summary TEXT"))
            session.commit()
            print("Column added successfully.")
        except Exception as e:
            print(f"Column might already exist or error: {e}")

if __name__ == "__main__":
    add_summary_column()
