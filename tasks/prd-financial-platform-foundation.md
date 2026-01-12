# Product Requirements Document: Financial Intelligence Platform - Phase 1 (Foundation)

## 1. Introduction
The goal is to evolve the existing `Mochi` document analysis application into a full-scale **Financial Intelligence Platform**. This platform will assist Relationship Managers (RMs) and Credit Analysts in monitoring the Malaysian market (Bursa Malaysia), analyzing financial filings, and tracking sentiment.
**Phase 1** focuses strictly on the **Foundation & Architecture**: defining the data models, solidifying the tech stack, establishing CI/CD, and configuring core security (RBAC).

## 2. Goals
-   **Data Structure**: Establish a robust relational and vector database schema to support complex financial data (Companies, Filings, News, Financials).
-   **Security**: Implement Role-Based Access Control (RBAC) to differentiate between Users (RMs), Analysts, Risk Officers, and Admins.
-   **Infrastructure**: Set up a professional CI/CD pipeline and code quality standards.
-   **Evolution**: Refactor the existing "generic document" system to support specialized financial architectures.

## 3. User Stories
-   **Developer**: I need a clear database schema for `Companies` and `Filings` so that I can build assemblers and scrapers in Phase 2.
-   **System Admin**: I need to assign specific roles (e.g., "Risk Officer") to users so they can access sensitive audit logs.
-   **DevOps**: I want every commit to be automatically linted and tested (CI) to prevent regressions in the existing codebase.
-   **Analyst**: I need the system to support "Wealth Management" contexts (Client Profiles) alongside "Market Data" (Companies).

## 4. Functional Requirements

### 4.1 Data Modeling (PostgreSQL + PGVector)
The Database schema must be updated/migrated to include the following models. *Extend existing models where possible.*

1.  **Company**
    -   Attributes: `id`, `name`, `ticker` (unique), `sector`, `sub_sector`, `market_cap`, `summary`, `created_at`.
    -   Relationships: Has many `Filings`, `NewsArticles`.
2.  **Filing** (Specialized `Document`?)
    -   Attributes: `id`, `company_id`, `type` (Annual Report, QR, General Announcement), `publication_date`, `pdf_url`, `content_summary`.
    -   *Note*: Can inherit from or link to existing `Document` table for vector storage.
3.  **NewsArticle**
    -   Attributes: `id`, `company_id` (optional, can be null if general market news), `source_name` (The Edge, Star, etc.), `title`, `url`, `published_at`, `content`.
4.  **SentimentAnalysis**
    -   Attributes: `id`, `source_id` (Polymorphic: linked to News or Filing), `score` (Positive/Neutral/Adverse), `confidence_score`, `rationale` (text explanation).
5.  **FinancialRatio**
    -   Attributes: `id`, `company_id`, `filing_id` (source), `period` (Q1 2024), `ratio_name` (e.g., 'Current Ratio'), `value` (float).
6.  **Alert**
    -   Attributes: `id`, `user_id`, `condition_json` (e.g., `{sentiment: 'Adverse', keyword: 'Resignation'}`), `is_active`.
7.  **User / ClientProfile** (Existing)
    -   Keep existing `ClientProfile` logic for Wealth Management use cases.

### 4.2 Tech Stack & Repo Setup
-   **Backend**: Python FastAPI (Existing). Maintain structure.
-   **Frontend**: Next.js (Existing).
-   **Database**: PostgreSQL 16 + pgvector (Existing).
-   **CI/CD**:
    -   Create `.github/workflows/ci.yml`.
    -   Steps: Checkout, Install Python deps, Run `ruff` (Lint), Run `pytest` (Tests), Build Docker (Dry run).
    -   Branching Strategy: `main` (Production), `dev` (Staging), `feature/*` (Development).

### 4.3 Security & RBAC
-   **Roles**: Define the following roles in `UserRole` enum:
    -   `ADMIN`: Full access.
    -   `RM` (Relationship Manager): Can manage Client Profiles, View Market Data.
    -   `ANALYST`: Can view Market Data, Edit Ratios/tags.
    -   `RISK`: Read-only access to specific high-risk alerts/logs.
-   **Implementation**:
    -   Update `auth.py` dependencies to check `current_user.role`.
    -   Ensure `ClientProfile` access is scoped to the owning RM (or shared based on rules).

### 4.4 Secret Management
-   Standardize `.env` usage.
-   Ensure sensitive keys (DB passwords, Secret Keys, future API keys) are not hardcoded.

## 5. Non-Goals (Out of Scope for Phase 1)
-   **Ingestion Logic**: Writing the actual scrapers for Bursa/The Edge (Phase 2).
-   **UI Implementation**: Building the Dashboard or Stock views (Phase 6).
-   **RAG Logic**: Advanced vector retrieval or chat (Phase 4), though schemas will support it.
-   **Deployment**: Production deployment is Phase 7, but CI/CD setup is Phase 1.

## 6. Success Metrics
-   [ ] All new database models are defined in `models.py` and Alembic migrations generated successfully.
-   [ ] GitHub Actions CI pipeline passes on a new PR.
-   [ ] Unit tests created for Role-Based Access Control (verifying an RM cannot access Admin routes).
-   [ ] Project structure allows for "Business Logic" separation (financials vs core).
