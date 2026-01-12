from fastapi import FastAPI
from app.database import create_db_and_tables
from app.middleware.tenant_isolation import TenantMiddleware
from app.middleware.audit import AuditMiddleware
from app.routers import auth, users, google_auth, documents, chat, health, webhooks, company, watchlist, news
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Finance AI Platform with RAG",
    description="Secure finance API with document ingestion and RAG-powered chat",
    version="1.0.0"
)

# ... (app init)

origins = [
    "http://localhost:3000",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Tenant Isolation Middleware
app.add_middleware(TenantMiddleware)
# Add Audit Middleware
app.add_middleware(AuditMiddleware)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(google_auth.router)
app.include_router(documents.router)  # New: Document management
app.include_router(chat.router)       # New: RAG chat
app.include_router(company.router)    # New: Company 360
app.include_router(health.router)     # New: Health checks
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"]) # New: Feature 3.4
app.include_router(watchlist.router)
app.include_router(news.router)


@app.get("/")
def read_root():
    return {
        "message": "Welcome to Finance AI Platform API",
        "version": "1.0.0",
        "features": ["Authentication", "Document Management", "RAG Chat", "AI Financial Advice"]
    }

