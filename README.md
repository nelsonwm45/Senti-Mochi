# Mochi: AI-Powered Finance Platform

Mochi is a modern, full-stack finance application that leverages AI to provide personalized financial advice. It features a secure authentication system (including Google Login), a responsive UI with rich animations, and a robust backend integrated with LLMs.

## 🛠 Tech Stack

### Frontend
*   **Next.js 16**: The React framework for the web (App Router).
*   **React 19**: A JavaScript library for building user interfaces.
*   **TypeScript**: Statically typed superset of JavaScript.
*   **Framer Motion**: Production-ready animation library for React.
*   **Lucide React**: Beautiful & consistent icons.
*   **Axios**: Promise-based HTTP client for the browser.
*   **CSS Modules / Vanilla CSS**: Custom styling for maximum flexibility and modern design (Glassmorphism).

### Backend
*   **FastAPI**: Modern, fast (high-performance) web framework for building APIs with Python.
*   **Python 3.10**: The core programming language.
*   **SQLModel**: Library for interacting with SQL databases from Python code, combining SQLAlchemy and Pydantic.
*   **LangChain**: Framework for developing applications powered by Language Models.
*   **OpenAI API**: Integration for AI financial analysis (`gpt-3.5-turbo`).
*   **OAuth2 & JWT**: Secure authentication flow using `python-jose` and `passlib[bcrypt]`.
*   **HTTPX**: Fully featured HTTP client for Python (used for Google Auth).

### Database
*   **PostgreSQL 16**: The world's most advanced open source relational database.
*   **pgvector**: Open-source vector similarity search for Postgres (used for storing AI embeddings).

### DevOps & Infrastructure
*   **Docker**: Containerization platform.
*   **Docker Compose**: Tool for defining and running multi-container Docker applications.
*   **Make**: Automation tool for running tasks.

## 🚀 Getting Started

### Prerequisites
*   Docker & Docker Compose
*   Google Cloud Console Project (for Google Login)
*   OpenAI API Key

### Setup
1.  **Environment Variables**:
    Create a `.env` file in the `backend` directory (`backend/.env`) with the following:
    ```env
    DATABASE_URL=postgresql://user:password@db:5432/finance_db
    SECRET_KEY=your_secret_key
    OPENAI_API_KEY=your_openai_key
    GOOGLE_CLIENT_ID=your_google_client_id
    GOOGLE_CLIENT_SECRET=your_google_client_secret
    ```

2.  **Run with Make**:
    ```bash
    make build   # Build the containers
    make up      # Start the application
    ```

3.  **Access**:
    *   Frontend: `http://localhost:3000`
    *   Backend Docs: `http://localhost:8000/docs`

## 🔐 Credentials Safety
The `.env` file containing secrets is located in `backend/.env` and is **only** accessible by the backend container. The frontend container does not have access to these sensitive credentials.