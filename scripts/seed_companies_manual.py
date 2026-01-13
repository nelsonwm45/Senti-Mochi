import sys
import os
# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.company_service import company_service

if __name__ == "__main__":
    print("Running seed...")
    company_service.seed_companies()
    print("Seed complete.")
