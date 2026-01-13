import sys
import os

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.company_service import company_service

if __name__ == "__main__":
    company_service.seed_companies()
