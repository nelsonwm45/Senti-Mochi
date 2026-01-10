"""
Migration script to add avatar_url column to users table

Run this script to update existing databases:
python add_avatar_column.py
"""

import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://mochi_user:mochi_password@localhost:5432/mochi_db'
)

def run_migration():
    """Add avatar_url column to users table if it doesn't exist"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if column already exists
            check_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='avatar_url';
            """)
            result = conn.execute(check_sql)
            
            if result.fetchone() is None:
                # Column doesn't exist, add it
                add_column_sql = text("""
                    ALTER TABLE users 
                    ADD COLUMN avatar_url VARCHAR NULL;
                """)
                conn.execute(add_column_sql)
                conn.commit()
                print("✅ Successfully added avatar_url column to users table")
            else:
                print("ℹ️  avatar_url column already exists in users table")
                
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("Running database migration...")
    run_migration()
    print("Migration complete!")
