# Secure Finance RAG Implementation

**Project**: Secure Finance API with RAG (Retrieval-Augmented Generation) capabilities

## Overview
Complete backend and frontend implementation for a secure, multi-tenant finance platform with:
- Document ingestion and processing
- Vector-based semantic search
- RAG-powered AI chat assistant
- Comprehensive audit logging
- Role-based access control (RBAC)

## Phases

### ✅ [Phase 1: Backend Foundation](./phase1/)
**Status**: Complete (with Groq integration)

**What was built**:
- Enhanced database models (UUID, RBAC, pgvector)
- Document upload & storage (S3/MinIO)
- Async processing with Celery
- Text extraction (PDF, DOCX, TXT)
- Vector embeddings (fallback implementation)
- Groq LLM integration (llama-3.1-70b-versatile)
- RAG service with security filtering
- REST API endpoints
- Health checks & monitoring

**Documentation**: See [phase1/README.md](./phase1/README.md)

### 🔜 Phase 2: Frontend & Agentic UI
**Status**: Not started

**Planned features**:
- Document upload interface with drag-and-drop
- Real-time processing status
- Agentic thought process visualization
- Chat interface with streaming responses
- Citation display and source linking
- Analytics dashboard

### 🔜 Phase 3: Universal Core Features
**Planned**:
- Advanced authentication (MFA, SSO)
- Tenant management
- Admin dashboard
- Advanced analytics
- Export functionality

### 🔜 Phase 4: DevOps & Deployment
**Planned**:
- CI/CD pipelines
- Production deployment
- Monitoring & alerting
- Backup & disaster recovery

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL 16 with pgvector
- **LLM**: Groq (llama-3.1-70b-versatile)
- **Task Queue**: Celery + Redis
- **Storage**: MinIO (S3-compatible)
- **ORM**: SQLModel

### Frontend (Planned)
- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **Animations**: Framer Motion
- **State**: React Query

### Infrastructure
- **Containerization**: Docker Compose
- **Vector DB**: pgvector extension
- **Cache**: Redis

## Quick Start

See [phase1/README.md](./phase1/README.md) for detailed setup instructions.

```bash
# Clone and navigate
cd /home/ubuntu/Mochi

# Start all services
docker compose up -d

# Run Phase 1 tests
cd docs/secure-finance-rag/phase1
./test_phase1.sh
```

## Current Limitations

1. **Embeddings**: Using simple hash-based fallback (not semantic)
   - **Impact**: Vector search doesn't capture meaning
   - **Solution**: Plan to integrate sentence-transformers or proper embedding service

2. **Groq API**: No native embedding support yet
   - **Workaround**: Using fallback for now
   - **Alternative**: Can switch to OpenAI for embeddings only

## Environment Configuration

Required environment variables (see `backend/.env.example`):
- `GROQ_API_KEY` - For LLM chat completions
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Celery task queue
- `S3_ENDPOINT` - MinIO/S3 storage

## Security Features

- ✅ User isolation (queries only access own documents)
- ✅ JWT authentication
- ✅ RBAC (User, Admin, Auditor roles)
- ✅ Audit logging
- ✅ Soft deletes
- ✅ Input validation

## Contributing

This is an internal project for the Mochi platform. Each phase is documented separately with implementation plans and walkthroughs.

## License

Proprietary - Internal use only
