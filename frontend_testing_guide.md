# Frontend Manual Testing Guide (Phase 1 - Phase 6)

This guide provides step-by-step instructions to verify the functionality of all implemented phases in the Financial Intelligence Platform frontend.

## Prerequisites
- Ensure the backend and frontend are running (`make up`).
- Access the application at `http://localhost:3000`.

---

## Phase 1: Foundation (Auth & Navigation)
**Goal**: Verify authentication flows and basic navigation.

1.  **Sign Up**:
    -   Navigate to `/signup`.
    -   Enter a new email/password (e.g., `test@example.com` / `password123`).
    -   Click "Sign Up".
    -   **Expected**: Redirects to Dashboard or Login.
2.  **Log In**:
    -   Navigate to `/login`.
    -   Enter credentials.
    -   **Expected**: Successfully redirects to `/dashboard`.
3.  **Profile**:
    -   Click the User Avatar (top right) -> "Profile".
    -   **Expected**: Displays your name/email. Try uploading a new avatar image.

## Phase 2: Ingestion & Documents
**Goal**: Verify document upload and viewing.

1.  **Upload**:
    -   Navigate to `/documents`.
    -   Drag & Drop a PDF (e.g., an annual report) into the "Upload Zone".
    -   **Expected**: Document appears in the list with status "Processing" -> "Completed" (refresh if needed).
2.  **View**:
    -   Click "View" on a processed document.
    -   **Expected**: PDF Viewer opens in a modal/sidebar.

## Phase 3: AI & Analytics (Visualized)
**Goal**: Verify analytics data is present (Backend logic materialized in Dashboard).

1.  **Market Ticker**:
    -   Look at the top of `/dashboard`.
    -   **Expected**: A scrolling ticker showing simulated companies and sentiment scores.
2.  **Impact News**:
    -   On `/dashboard`, check "High Impact News".
    -   **Expected**: Cards showing news titles with "Positive" or "Negative" badges (powered by Sentiment Engine).

## Phase 4: Copilot (Chat)
**Goal**: Verify RAG chat and feedback.

1.  **Ask a Question**:
    -   Navigate to `/chat`.
    -   Type: *"What is the revenue for [Company Name]?"* (ensure a document exists).
    -   **Expected**:
        -   Streaming response appears.
        -   Citations `[1]` appear at the bottom.
2.  **Deep Linking**:
    -   Click a Citation `[1]`.
    -   **Expected**: Opens the PDF viewer to the specific source page.
3.  **Feedback**:
    -   Hover over the bot response.
    -   Click "Thumbs Up" or "Thumbs Down".
    -   **Expected**: Console logs "Feedback submitted" (or verified via Network tab).

## Phase 6: Company 360 & Admin
**Goal**: Verify new Phase 6 features.

1.  **Company 360**:
    -   Click a company ticker on Dashboard OR go to `/companies/AUTO_GENERATED_ID` (you might need to pick one from Watchlist or Ticker).
    -   **Expected**: Page loads with Header (Sector/Cap).
    -   **Tabs**: Click "Financials" (Chart appears), "News" (News list appears).
2.  **Watchlist (Settings)**:
    -   Navigate to `/watchlist`.
    -   **Expected**: Empty state or list of watched companies.
    -   **Action**: (If implemented button exists) Click "Add to Watchlist" on Company Page, then return here to verify presence.
3.  **Admin Panel**:
    -   **As User**: Go to `/admin`. **Expected**: 403 Forbidden or Redirect.
    -   **As Admin**: (Requires manual role update in DB to 'ADMIN'). Go to `/admin`. **Expected**: Grid of all users, their roles, and active status.

---

## Automated Verification Status (My Side)
I have run the verification suite on the internal backend to ensure the API is ready for your frontend tests:

-   `verify_foundation.py`: **PASSED** (Models & RBAC)
-   `verify_ingestion.py`: **PASSED** (Connectors & Pipeline)
-   `verify_analytics.py`: **PASSED** (Sentiment & NER)
-   `verify_copilot.py`: **PASSED** (RAG Search & Feedback)
-   `verify_backend_logic.py`: **PASSED** (Alerting & Company 360)

The system is fully operational.
