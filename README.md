# Mochi: AI-Powered Market Intelligence Platform

## Problem Statement

Market signals are abundant but fragmented and unstructured across sources such as Bursa filings, news, and PDFs. While existing solutions may help with isolated tasks (e.g., pulling live information or extracting text), they operate in silos and fail to support an end-to-end, traceable decision workflow. As a result, teams are forced to rely on manual interpretation under time pressure, leading to:

- **Inconsistent sentiment and labeling**, where different analysts reach different conclusions from the same information
- **Key financial data trapped in PDFs**, making it difficult to standardize ratios and compare performance across companies and time
- **Weak alerting**, either missing early warning signals or overwhelming users with false positives
- **Low defensibility of decisions**, due to the lack of citations, clear analytical rationale, RBAC, audit trails, and proper data retention and privacy controls

Because these gaps exist across the workflow rather than in any single step, existing tools fail to deliver consistent, trusted intelligence—resulting in slower decisions, higher operational costs, and increased risk exposure.

## Our Solution

Our product provides an end-to-end market intelligence workflow that helps bank teams cut through noisy, unstructured market signals and make consistent, defensible decisions.

### Workflow Overview

**Watchlists**
Users add Bursa-listed companies to a watchlist so the system monitors only relevant entities.

**Source Ingestion**
News, announcements, and reports are preiodically pulled from credible sources such as Bursa, NST, and The Star.

**Processing & Storage**
All documents are parsed, enriched (sentiment, entities), and stored in a vector database to support search, analysis, and traceability.

### Key Capabilities

**Dashboard News Feed**
- Company-specific news tagged with consistent sentiment (positive / negative / neutral)
- Alerts for critical or attention-worthy issues
- AI summaries with links back to original sources
- Quick actions to draft client emails or WhatsApp messages

**Company Watchlist**
- Standardized financial metrics for side-by-side comparison across companies and time
- Support for manual document uploads to enrich company context

**AI Copilot**
- Ask questions about companies or industries
- Answers generated only from ingested data
- Full citations provided for every insight

### Who It's For

- **Relationship Managers / Coverage Teams**: Get fast, reliable context before client engagements.
- **Market Intelligence & Research Analysts**: Reduce manual scanning and work from consistent, structured signals.
- **Credit & Risk Stakeholders**: Access standardized financial data and defend decisions with clear evidence trails.

## 📹 Demo Video

[View Demo Video](https://youtu.be/mFSPfLC2hdc)

## 📊 Presentation Deck

[View Presentation Deck](https://www.canva.com/design/DAG-SVuKCNs/NKoCQBp7AqrFnBOZn2Y4Qg/edit?utm_content=DAG-SVuKCNs&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)

## 🛠 Tech Stack

### Frontend
- **Next.js + React**: Modern web framework with server-side rendering
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling

### Backend
- **FastAPI**: High-performance Python web framework
- **PostgreSQL**: Robust relational database
- **Celery + Redis**: Asynchronous task processing and caching

### AI / Intelligence
- **Local embeddings + LLM**: On-device AI processing
- **RAG**: Retrieval-Augmented Generation for smart document retrieval

### Documents
- **PDF processing**: Advanced document parsing and extraction

### Infra & Security
- **Docker**: Containerized deployment
- **JWT auth**: Secure authentication

## 🚀 Getting Started

### Prerequisites
*   [Docker](https://docs.docker.com/get-docker/) & Docker Compose
*   [Make](https://www.gnu.org/software/make/) (optional, but recommended for running commands)

### Setup Instructions

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd Mochi
    ```

2.  **Environment Configuration**
    Create a `.env` file in the `backend` directory based on the example.
    ```bash
    cp backend/.env.example backend/.env
    ```
    
    **Critical: Update `backend/.env` with your real keys:**
    *   `GROQ_API_KEY`: Get one from [console.groq.com](https://console.groq.com/).
    *   `GOOGLE_CLIENT_ID` / `SECRET`: Required if you want Google Login to work.
    *   `SECRET_KEY`: Generate a random string for security (e.g., `openssl rand -hex 32`).

3.  **Run the Application**
    We use `Makefile` to simplify Docker commands.

    **Build and Start:**
    ```bash
    make build
    make up
    ```
    *(Or using Docker directly: `docker compose up --build -d`)*

4.  **Access the Application**
    *   **Frontend**: [http://localhost:3000](http://localhost:3000)
    *   **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
    *   **MinIO Console**: [http://localhost:9001](http://localhost:9001) (User/Pass: `minioadmin`)
