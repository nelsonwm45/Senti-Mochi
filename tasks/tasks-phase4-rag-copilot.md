## Relevant Files

- `backend/app/services/rag_service.py` (New/Refactor) - Core RAG logic.
- `backend/app/routers/chat.py` - Chat endpoints.
- `backend/app/models.py` - DocumentChunk model updates.

### Notes

- Ensure `DocumentChunk` is linked to `Filing` or `NewsArticle`.
- Citations must be precise: `[Source: Annual Report 2023, Page 45]`.

## Tasks

- [x] 0.0 Create feature branch
  - [x] 0.1 Create branch `feature/phase4-copilot`
- [x] 1.0 Vector Database Setup
  - [x] 1.1 Optimise chunking strategy for Financial Reports (preserve paragraphs/tables).
  - [x] 1.2 Re-index existing content with new metadata strategies.
- [x] 2.0 Retrieval Pipeline
  - [x] 2.1 Implement hybrid search (Keyword + Semantic) for specific company names.
  - [x] 2.2 Add filters for Date Range and Document Type.
- [x] 3.0 Citation Engine
  - [x] 3.1 Refine System Prompt to enforce strict citation format.
  - [x] 3.2 Implement "Step-by-Step" reasoning in output stream.
- [x] 4.0 Feedback Loop
  - [x] 4.1 Add API to accept Thumbs Up/Down for messages.
  - [x] 4.2 Log feedback to `AuditLog` or dedicated `Feedback` table for tuning.
