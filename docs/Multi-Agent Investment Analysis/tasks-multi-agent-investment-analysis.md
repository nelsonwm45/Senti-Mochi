# Task List: Multi-Agent Investment Analysis

## Relevant Files
- `backend/app/models.py`: Database models (AnalysisReport, NewsChunk).
- `backend/app/agents/base.py`: Base LLM configuration.
- `backend/app/agents/news_agent.py`: News summarization agent.
- `backend/app/agents/claims_agent.py`: PDF/Claims analysis agent.
- `backend/app/agents/financial_agent.py`: Financial ratio/narrative agent.
- `backend/app/agents/judge.py`: Debate and reporting agent.
- `backend/app/agents/workflow.py`: Orchestrator logic.
- `backend/app/routers/analysis.py`: API endpoints.
- `frontend/src/components/CompanyDetails/AnalysisTab.tsx`: Frontend integration.

## Tasks

- [ ] 0.0 Create feature branch
  - [ ] 0.1 Create and checkout new branch `feature/multi-agent-analysis`

### Phase 1: Backend Infrastructure
- [x] 1.0 Setup Infrastructure & Data Models
  - [x] 1.1 Add dependencies (`langgraph`, `langchain-google-genai`) to `backend/requirements.txt`
  - [x] 1.2 Update `backend/app/models.py` to include `AnalysisReport` table
  - [x] 1.3 Update `backend/app/models.py` to include `NewsChunk` table
  - [x] 1.4 Generate Alembic migration script (`alembic revision --autogenerate`)
  - [x] 1.5 Apply database migrations (`alembic upgrade head`)
  - [x] 1.6 Verify `GEMINI_API_KEY` and `GROQ_API_KEY` loading in `backend/app/core/config.py`
  - [x] 1.7 Create migration script `scripts/backfill_news_chunks.py` to chunk existing news articles
  - [x] 1.8 Run backfill script

### Phase 2: Agent Implementation
- [x] 2.0 Implement Base & Worker Agents
  - [x] 2.1 Create `backend/app/agents/base.py` (LLM clients for Groq/Gemini)
  - [x] 2.2 Implement `backend/app/agents/news_agent.py`
    - [x] Fetch relevant news chunks from DB
    - [x] Generate summary with citations
  - [x] 2.3 Implement `backend/app/agents/claims_agent.py`
    - [x] Vector search on `DocumentChunk`
    - [x] Extract management claims
  - [x] 2.4 Implement `backend/app/agents/financial_agent.py`
    - [x] Fetch structured financials from `FinancialStatement`
    - [x] Calculate ratios
    - [x] Generate quantitative narrative

- [x] 3.0 Implement Orchestration & Judge
  - [x] 3.1 Implement `backend/app/agents/judge.py`
    - [x] Define "Debate" prompt structure (Reviewing input from workers)
    - [x] Generate final Markdown report
  - [x] 3.2 Implement `backend/app/agents/workflow.py`
    - [x] Define LangGraph state
    - [x] Create graph: Start -> Parallel(News, Claims, Financials) -> Judge -> End
    - [x] execute_workflow function

### Phase 3: API Integration
- [x] 4.0 Create API Endpoints
  - [x] 4.1 Create `backend/app/routers/analysis.py`
  - [x] 4.2 Implement `POST /api/analysis/{company_id}` (Trigger)
  - [x] 4.3 Implement `GET /api/analysis/{company_id}/history` (List past reports)
  - [x] 4.4 Implement `GET /api/analysis/report/{report_id}` (Get specific report details)
  - [x] 4.5 Register router in `backend/app/main.py`

### Phase 4: Frontend Implementation (Optional / External Developer)
- [ ] 5.0 Frontend Components (Assigned to External Developer)
  - [ ] 5.1 Create `frontend/src/types/Analysis.ts` (Interfaces for reports)
  - [ ] 5.2 Create `frontend/src/api/analysisService.ts` (Axios calls)
  - [ ] 5.3 Create `AnalysisTerminal.tsx` component (Visualizing agent steps)
  - [ ] 5.4 Create `AnalysisReport.tsx` component (Markdown display of final report)
  - [ ] 5.5 Create `AnalysisHistory.tsx` component (List view)

- [ ] 6.0 Integration (Assigned to External Developer)
  - [ ] 6.1 Update `CompanyDetails.tsx` to add "AI Analysis" tab
  - [ ] 6.2 Integrate "Analyze Now" button and state management
  - [ ] 6.3 Test full flow

### Phase 5: Verification
- [ ] 7.0 Verification
  - [ ] 7.1 Verify News Agent uses `NewsChunk` effectively
  - [ ] 7.2 Verify Citations link correctly
  - [ ] 7.3 Verify Report saves to DB and persists on refresh
