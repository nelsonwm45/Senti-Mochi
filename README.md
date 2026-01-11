# Mochi: AI-Powered Finance Platform

Mochi is a modern, full-stack finance application that leverages AI to provide personalized financial advice and document analysis. It features a secure authentication system, a responsive UI with rich animations, and a robust backend integrated with advanced LLMs and RAG (Retrieval-Augmented Generation) capabilities.

## 🛠 Tech Stack & Justifications

### Frontend
*   **Next.js 16 (App Router)**: Chosen for its server-side rendering capabilities, SEO benefits, and the modern App Router architecture which simplifies routing and layouts.
*   **React 19**: The latest version of the library, enabling modern features like Server Actions and improved concurrent rendering.
*   **TypeScript**: Ensures type safety across the codebase, reducing runtime errors and improving developer experience.
*   **Tailwind CSS**: A utility-first CSS framework that speeds up development and ensures a consistent design system.
*   **Framer Motion**: Provides production-ready, high-performance animations (used for page transitions and component interactions) to give the application a premium feel.
*   **Lucide React**: A consistent and beautiful icon library.
*   **Axios**: For robust HTTP requests with interceptor support (useful for handling auth tokens).
*   **React Dropzone**: Simplified file drag-and-drop interactions.

### Backend
*   **FastAPI (Python 3.10)**: Selected for its high performance (asynchronous), automatic OpenAPI (Swagger) documentation generation, and ease of use with Python's rich AI/ML ecosystem.
*   **SQLModel**: A modern ORM that combines SQLAlchemy and Pydantic, reducing boilerplate code and making database interactions type-safe.
*   **Celery + Redis**: 
    *   **Celery**: Asynchronous task queue. Crucial for offloading long-running tasks like OCR (Tesseract) and PDF text extraction so the API remains responsive.
    *   **Redis**: High-performance message broker for Celery and caching layer.
*   **MinIO (S3 Compatible)**: Object storage for user documents. chosen for its S3 compatibility (easy to migrate to AWS S3 later) and ease of local deployment via Docker.
*   **PyMuPDF (fitz)**: Advanced PDF processing library that extracts both embedded text and images from PDF documents, enabling comprehensive document analysis.
*   **Tesseract OCR / Pytesseract**: Optical Character Recognition engine to extract text from images (PNG, JPG) and images embedded within PDFs, enabling the AI to "read" receipts, scanned documents, and image-based PDFs.
*   **Sentence Transformers (all-MiniLM-L6-v2)**: Local embedding model. Used to generate vector embeddings for RAG. It's fast, free, and runs locally without external API costs.
*   **Groq API (Llama 3.3)**: High-performance inference engine for the LLM. Chosen for its incredible speed, making the chat experience feel real-time.

### Database
*   **PostgreSQL 16**: A robust, industrial-strength relational database.
*   **pgvector**: Extension for vector similarity search. Allows us to store and query document embeddings directly within the database, simplifying the infrastructure (no need for a separate vector DB like Pinecone).

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

## 📂 Project Structure
```
Mochi/
├── backend/            # FastAPI Backend
│   ├── app/
│   │   ├── routers/    # API Endpoints
│   │   ├── services/   # Business Logic (RAG, Ingestion)
│   │   └── models.py   # Database Schemas
│   └── Dockerfile
├── frontend/           # Next.js Frontend
│   ├── src/
│   │   ├── app/        # App Router Pages
│   │   └── components/ # Reusable UI Components
│   └── Dockerfile
├── docker-compose.yml  # Container Orchestration
└── Makefile            # Shortcut Commands
```