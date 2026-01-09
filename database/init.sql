-- Initialize database with pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create indexes for vector similarity search
-- These will be added after tables are created by SQLModel

-- Index for document_chunks embedding (IVFFlat for faster similarity search)
-- Note: This should be created after inserting some data for better performance
-- CREATE INDEX document_chunks_embedding_idx ON document_chunks 
-- USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Additional indexes for common queries
-- CREATE INDEX IF NOT EXISTS idx_documents_user_status ON documents(user_id, status) WHERE is_deleted = false;
-- CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON document_chunks(document_id);
-- CREATE INDEX IF NOT EXISTS idx_chat_messages_user_session ON chat_messages(user_id, session_id);
-- CREATE INDEX IF NOT EXISTS idx_audit_logs_user_time ON audit_logs(user_id, timestamp DESC);
