import sys
import os

# Add the parent directory to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import text, Session
from app.database import engine, create_db_and_tables

def purge_and_reset_schema():
    print("Starting database purge and schema migration...")
    
    with Session(engine) as session:
        # Drop tables in dependency order (Leaf -> Root)
        # We value Users and Tenants, so we keep them.
        # We drop everything else to ensure strict isolation schema is applied.
        
        tables_to_drop = [
            "report_chunks",
            "news_chunks",
            "analysis_jobs",
            "financial_statements",
            "watchlists",
            "analysis_reports",
            "news_articles",
            "document_chunks",
            "documents",
            "companies"
        ]
        
        for table in tables_to_drop:
            print(f"Dropping table: {table}")
            try:
                session.exec(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                session.commit()
            except Exception as e:
                print(f"Error dropping {table}: {e}")
                session.rollback()

    print("Tables dropped. Re-creating schema...")
    create_db_and_tables()
    print("Schema migration complete.")

if __name__ == "__main__":
    purge_and_reset_schema()
