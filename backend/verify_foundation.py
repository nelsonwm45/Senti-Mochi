from sqlmodel import Session, select, func, inspect
from app.database import engine
from app.models import User, Company, Filing, NewsArticle, UserRole, Alert
from app.auth import require_role
from fastapi import HTTPException
from unittest.mock import MagicMock

def check_tables():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("\n--- Checking Data Models ---")
    print("Tables found:", tables)
    required = ["companies", "filings", "news_articles", "sentiment_analysis", "financial_ratios", "alerts"]
    missing = [t for t in required if t not in tables]
    if missing:
        print("MISSING TABLES:", missing)
    else:
        print("All Phase 1 tables exist.")

def test_rbac_logic():
    print("\n--- Checking RBAC Logic ---")
    # Simulate dependency check for requiring RM role
    checker = require_role(UserRole.RM)
    
    # Mock Admin User (should pass)
    admin = User(email="admin@test.com", hashed_password="x", role=UserRole.ADMIN)
    try:
        checker(admin)
        print("Admin access to RM route: ALLOWED (Correct)")
    except HTTPException:
        print("Admin access to RM route: DENIED (Fail)")

    # Mock RM User (should pass)
    rm = User(email="rm@test.com", hashed_password="x", role=UserRole.RM)
    try:
        checker(rm)
        print("RM access to RM route: ALLOWED (Correct)")
    except HTTPException:
        print("RM access to RM route: DENIED (Fail)")

    # Mock Normal User (should fail)
    normal = User(email="user@test.com", hashed_password="x", role=UserRole.USER)
    try:
        checker(normal)
        print("User access to RM route: ALLOWED (Fail)")
    except HTTPException:
        print("User access to RM route: DENIED (Correct)")

if __name__ == "__main__":
    check_tables()
    test_rbac_logic()
