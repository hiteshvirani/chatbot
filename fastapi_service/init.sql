-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create chatbot_embeddings table
CREATE TABLE IF NOT EXISTS chatbot_embeddings (
    id SERIAL PRIMARY KEY,
    chatbot_id INTEGER NOT NULL,
    source_type VARCHAR(20) NOT NULL, -- 'document', 'link', 'prompt'
    source_id INTEGER NOT NULL, -- ID from Odoo
    content TEXT NOT NULL,
    content_chunk_index INTEGER DEFAULT 0, -- For chunked documents
    embedding vector(384), -- Dimension depends on model (all-MiniLM-L6-v2 = 384)
    metadata JSONB, -- Store filename, url, chunk info, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_chatbot_embeddings_chatbot_id ON chatbot_embeddings(chatbot_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_embeddings_source ON chatbot_embeddings(chatbot_id, source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_embeddings_vector ON chatbot_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create chatbot_sessions table
CREATE TABLE IF NOT EXISTS chatbot_sessions (
    id SERIAL PRIMARY KEY,
    chatbot_id INTEGER NOT NULL,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    conversation_history JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chatbot_sessions_chatbot ON chatbot_sessions(chatbot_id, session_id);

-- Create api_key_usage table for analytics
CREATE TABLE IF NOT EXISTS api_key_usage (
    id SERIAL PRIMARY KEY,
    chatbot_id INTEGER NOT NULL,
    api_key_hash VARCHAR(64) NOT NULL,
    endpoint VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_key_usage_chatbot ON api_key_usage(chatbot_id, created_at);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO chatbot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO chatbot_user;
