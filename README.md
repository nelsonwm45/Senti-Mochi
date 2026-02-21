# Senti-Mochi — AI-Powered Market Intelligence for Relationship Managers

<p align="center">
  <a href="https://drive.google.com/drive/folders/1X-BqEwcLJQJOMCNU3ULdVTsJWJAt4wuy?usp=sharing">📹 Demo Videos</a> •
  <a href="https://www.canva.com/design/DAHAcj5v1Vw/XmWQ_9IB6-VEQnc4vldz4w/edit?utm_content=DAHAcj5v1Vw&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton">📊 Presentation Deck</a>
</p>

---

## The Problem

Relationship Managers spend hours daily scanning fragmented news, manually interpreting financial reports, and preparing for client meetings — leading to inconsistent analysis, missed signals, and indefensible decisions.

## The Solution

Senti-Mochi gives RMs an end-to-end intelligence workflow that turns unstructured market signals into consistent, citation-backed, actionable insights.

### RM Workflow

```
1. Add Clients     →  Build your watchlist / portfolio
2. Auto-Ingest     →  System pulls news from The Edge, The Star, NST
3. Sentiment Tags  →  Every article AI-analyzed with sentiment scoring
4. Deep Analysis   →  Upload annual/sustainability reports to trigger
                       multi-agent courtroom-style debate
5. Meeting Notes   →  Generate structured talking points from the latest analysis
```

### Impact

| Task | Before | After |
|---|---|---|
| Daily Market Scanning | 30–45 min | **5–10 min** |
| Client Risk Assessment | 2–3 hours | **30 min** |
| Client Communication Prep | 30–45 min | **5–10 min** |

✅ Defensible decisions with full citations &nbsp;·&nbsp; ✅ Single source of truth &nbsp;·&nbsp; ✅ Confident client conversations

---

## Key Features

**📰 Sentiment-Tagged News Feed** — Company-specific news with AI sentiment, alerts, summaries, and WhatsApp/email quick actions.

**📋 Company Watchlist** — Standardized financial metrics for side-by-side comparison. Pin up to 3 companies for at-a-glance monitoring.

**⚖️ Multi-Agent Analysis Engine** — Courtroom-style debate workflow (LangGraph):
1. **Intelligence Gathering** — Financial, News, and Claims agents collect data with tagged citations `[N#]` `[F#]` `[D#]`
2. **Briefing** — Findings consolidated into structured briefs
3. **Cross-Examination** — Government (pro) vs Opposition (skeptic) agents debate
4. **Judgment** — Judge agent synthesizes, verifies citations, and produces the final report

Supports persona-based analysis with sector-specific KPIs.

**📝 Meeting Notes** — Auto-generate structured talking points for client engagements based on the latest analysis.

**📄 Document Uploads** — Upload PDFs, DOCX, XLSX (annual reports, sustainability reports) to enrich company context.

---

## 🛠 Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS, Zustand, Recharts, Framer Motion |
| **Backend** | FastAPI, SQLModel, PostgreSQL + pgvector, Celery + Redis, MinIO (S3), Alembic |
| **AI** | LangGraph, LangChain, Groq / Cerebras / Google Gemini, sentence-transformers, RAG |
| **Ingestion** | Scrapy, newspaper3k, yfinance, PyMuPDF, pytesseract |
| **Infra** | Docker Compose (7 services), JWT + Google OAuth, Prometheus, SlowAPI |

---

## 🚀 Getting Started

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- [Make](https://www.gnu.org/software/make/) (optional)

### Setup

```bash
git clone <repository-url>
cd Mochi
cp backend/.env.example backend/.env
# Edit backend/.env — set GROQ_API_KEY, CEREBRAS_API_KEY, GOOGLE_CLIENT_ID/SECRET, SECRET_KEY
make build && make up
```

For development with hot-reload: `make dev`

### Access

| Service | URL |
|---|---|
| Frontend | [http://localhost:3000](http://localhost:3000) |
| API Docs | [http://localhost:8000/docs](http://localhost:8000/docs) |
| MinIO Console | [http://localhost:9001](http://localhost:9001) (`minioadmin` / `minioadmin`) |

---

## 📁 Project Structure

```
Mochi/
├── frontend/           # Next.js app (dashboard, watchlist, chat, company analysis)
├── backend/
│   ├── app/
│   │   ├── agents/     # Multi-agent analysis engine (LangGraph)
│   │   ├── routers/    # API endpoints
│   │   ├── services/   # RAG, sentiment, ingestion, embedding
│   │   └── tasks/      # Celery async tasks
│   └── alembic/        # Database migrations
├── docker-compose.yml  # 7-service orchestration
└── Makefile            # Dev commands (up, down, build, dev, reset-db, etc.)
```
