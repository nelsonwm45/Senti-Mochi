# Multi-Agent Investment Analysis Implementation Plan

## 1. Overview
This feature implements a multi-agent system to provide qualitative investment analysis for companies. It uses a **Supervisor-Worker-Judge** architecture to simulate an investment committee debate, utilizing **Groq (Llama-3)** for high-speed data extraction and **Gemini 1.5 Pro** for high-context reasoning and synthesis.

## 2. Architecture

### Workflow Diagram
```mermaid
graph TD
    User[User clicks 'Analyze Now'] --> API[POST /api/analysis/start]
    API --> Workflow[Workflow Orchestrator (LangGraph)]
    Workflow -->|Parallel| News[News Agent (Groq)]
    Workflow -->|Parallel| Claims[Claims Agent (Groq)]
    Workflow -->|Parallel| Financials[Financial Agent (code/Groq)]
    
    News -->|Context| Debate[Debate Loop]
    Claims -->|Context| Debate
    Financials -->|Context| Debate
    
    Debate -->|Challenge/Response| Judge[Judge Agent (Gemini)]
    
    Judge -->|Final Report| DB[(Database)]
    DB --> Frontend[Frontend Display]
```

### Agent Roles
1.  **Workflow Orchestrator (Code/LangGraph):**
    *   **Role:** Traffic Controller (Deterministic).
    *   **Action:** Triggers both News and Claims agents in parallel for every analysis. Passes results to the Judge.
2.  **News Agent (Groq/Llama-3-70b):**
    *   **Role:** Researcher.
    *   **Input:** Existing news articles from DB (last 30-90 days).
    *   **Action:** Summarize sentiment, key events, and market perception.
3.  **Claims Agent (Groq/Llama-3-70b):**
    *   **Role:** Analyst.
    *   **Input:** Text from Annual Reports/PDFs (if available) or company description.
    *   **Action:** Extract management claims, future outlook, and potential risks.
4.  **Financial Agent (Python + Groq):**
    *   **Role:** Quantitative Analyst.
    *   **Input:** Structured Financial Statements (Income/Balance/CashFlow) from DB.
    *   **Action:** Calculate key ratios (YoY Growth, Margins). Use LLM to generate a narrative summary of financial health (e.g., "Revenue is growing but margins are compressing").
5.  **Judge Agent (Gemini 1.5 Pro):**
    *   **Role:** Synthesizer & Decision Maker.
    *   **Input:** Outputs from News & Claims agents.
    *   **Action:** Conducts a "debate" (checking for contradictions), then generates the final Investment Report with a Buy/Sell/Hold rating and Confidence Score.

## 3. Data Model
New table `analysis_report` in `backend/app/models.py`:

```python
class AnalysisReport(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    company_id: UUID = Field(foreign_key="company.id")
    current_price: float
    rating: str  # BUY, SELL, HOLD
    confidence_score: int  # 0-100
    summary: str  # Markdown text
    bull_case: str
    bear_case: str
    risk_factors: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # Metadata for the debate or agent logs could be stored in a JSON field if needed
    agent_logs: List[Dict] = Field(default=[], sa_column=Column(JSON))

class NewsChunk(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    news_id: UUID = Field(foreign_key="news_articles.id", index=True)
    content: str = Field(sa_column=Column(Text))
    chunk_index: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

## 4. Implementation Steps

### Phase 1: Backend Infrastructure
- [ ] **1.1 Dependencies:** Add `langgraph` and `langchain-google-genai` to `backend/requirements.txt`.
- [ ] **1.2 Database:** Update `models.py` with `AnalysisReport` and `NewsChunk` models. Run Alembic migration.
- [ ] **1.3 API Keys:** Ensure `GEMINI_API_KEY` and `GROQ_API_KEY` are loaded in `config.py`.
- [ ] **1.4 Migration Script:** Create a script to back-fill chunks for existing news articles.

### Phase 2: Agent Implementation
- [ ] **2.1 Agent Base:** Create `backend/app/agents/base.py` for common LLM setup.
- [ ] **2.2 News Agent:** Create `backend/app/agents/news_agent.py`. Implement logic to fetch news from DB and summarize.
- [ ] **2.3 Claims Agent:** Create `backend/app/agents/claims_agent.py`.
- [ ] **2.4 Financial Agent:** Create `backend/app/agents/financial_agent.py`. Implement ratio calculation and trend summary.
- [ ] **2.5 Judge Agent:** Create `backend/app/agents/judge.py`.
- [ ] **2.6 Workflow:** Create `backend/app/agents/workflow.py` using LangGraph to connect the nodes.

### Phase 3: API Integration
- [ ] **3.1 Endpoint:** Create `backend/app/routers/analysis.py`.
    *   `POST /analysis/{company_id}`: Triggers the background task (Celery or Async).
    *   `GET /analysis/{company_id}/status`: Stream progress or poll status.
    *   `GET /analysis/{company_id}/history`: Retrieve past reports.
- [ ] **3.2 Main:** Register new router in `main.py`.

### Phase 4: Frontend Implementation
- [ ] **4.1 UI Components:**
    *   `AnalysisButton`: "Analyze Now" button with loading state.
    *   `AgentTerminal`: A component to show "Supervisor: Thinking...", "News Agent: Found 5 articles..." logs in real-time (or polled).
    *   `AnalysisReportCard`: Beautiful display of the final markdown report.
- [ ] **4.2 Integration:**
    *   Update `CompanyDetails.tsx` to include the Analyze workflow.
    *   Add `AnalysisHistory` tab or modal.

## 5. Verification Plan

### Automated Tests
*   **Unit Tests:** Create `tests/test_agents.py` to test each agent in isolation (mocking the LLM responses).
*   **Integration Test:** Create `tests/test_analysis_api.py` to verify the DB storage and retrieval of reports.

### Manual Verification
1.  **Environment:** Ensure `.env` has valid keys.
2.  **Trigger:** Go to a Company Page (e.g., Company XYZ). Click "Analyze Now".
3.  **Observation:** Watch the "AgentTerminal" populate with steps.
4.  **Result:** Verify a Report Card appears after ~30-60s.
5.  **Persistence:** Refresh page. Verify the report is still there (or in History).
6.  **Debate:** Check logs to see if the Judge actually referenced the News/Claims inputs.
