# B2B Chatbot Platform - Comprehensive Implementation Plan

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Technology Stack](#technology-stack)
3. [Docker Setup](#docker-setup)
4. [Project Structure](#project-structure)
5. [Database Schema](#database-schema)
6. [Odoo Module Design](#odoo-module-design)
7. [FastAPI Service Design](#fastapi-service-design)
8. [Synchronization Flow](#synchronization-flow)
9. [API Endpoints](#api-endpoints)
10. [Security Implementation](#security-implementation)
11. [Implementation Steps](#implementation-steps)

---

## System Architecture

### Overview
A multi-tenant B2B chatbot platform where users can create chatbots, add documents/links, and embed them on their websites with API key authentication.

### Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                        User's Website                        │
│  <iframe src=".../chatbot/{id}/widget?api_key=...">         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ HTTP Request (API Key)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Service                          │
│  - Public Chat Endpoints                                    │
│  - RAG Pipeline (LangChain + Ollama)                       │
│  - Vector Search (pgvector)                                 │
└───────┬───────────────────────────────┬─────────────────────┘
        │                               │
        │ Query Embeddings              │ Store/Update Embeddings
        │                               │
        ▼                               ▼
┌──────────────────┐          ┌──────────────────────────────┐
│  PostgreSQL +    │          │      Odoo Service            │
│  pgvector        │◄─────────┤  - Chatbot Management        │
│                  │  Sync    │  - Document Management       │
│  - Embeddings    │  Webhook │  - API Key Management       │
│  - Metadata      │          │  - User Interface            │
└──────────────────┘          └──────────────────────────────┘
```

### Component Responsibilities

**Odoo Service:**
- User management and authentication
- Chatbot CRUD operations
- Document/Link/Prompt management
- API key generation and management
- Webhook triggers to FastAPI for sync operations
- UI for chatbot management

**FastAPI Service:**
- Public chatbot endpoints (chat, widget)
- Document processing and embedding generation
- Vector storage in pgvector
- RAG pipeline execution
- API key validation
- Domain restriction enforcement

**PostgreSQL + pgvector:**
- Store document embeddings
- Vector similarity search
- Metadata storage
- Session management

---

## Technology Stack

### Backend Services
- **Odoo**: ERP system for user and chatbot management
- **FastAPI**: Python web framework for API services
- **PostgreSQL**: Relational database
- **pgvector**: PostgreSQL extension for vector operations

### AI/ML Stack
- **Ollama**: Local LLM runtime
- **LangChain**: RAG pipeline orchestration
- **sentence-transformers**: Embedding generation (alternative to Ollama embeddings)

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration

### Additional Libraries
- **PyPDF2**: PDF text extraction
- **python-docx**: Word document processing
- **BeautifulSoup4**: Web scraping for links
- **requests**: HTTP client
- **psycopg2**: PostgreSQL adapter

---

## Docker Setup

### Docker Compose Structure
All services will run in separate Docker containers with proper networking and volume mounts.

### Services Configuration

#### 1. PostgreSQL Service
- **Image**: `pgvector/pgvector:pg16`
- **Port**: `5432`
- **Volumes**: 
  - Data persistence
  - Init scripts for pgvector extension
- **Environment Variables**:
  - `POSTGRES_DB`: chatbot_db
  - `POSTGRES_USER`: chatbot_user
  - `POSTGRES_PASSWORD`: (from env file)

#### 2. Odoo Service
- **Image**: `odoo:17` (or latest)
- **Port**: `8069`
- **Volumes**:
  - `./odoo_service/custom_addons:/mnt/extra-addons` (custom modules)
  - `./odoo_service/config:/etc/odoo` (config files)
  - `./odoo_service/data:/var/lib/odoo` (data persistence)
- **Environment Variables**:
  - `HOST`: db (PostgreSQL service name)
  - `USER`: odoo
  - `PASSWORD`: (from env file)
  - `FASTAPI_URL`: http://fastapi:8000

#### 3. FastAPI Service
- **Base Image**: `python:3.11-slim`
- **Port**: `8000`
- **Volumes**:
  - `./fastapi_service/app:/app` (application code)
  - `./fastapi_service/uploads:/app/uploads` (document storage)
- **Environment Variables**:
  - `DATABASE_URL`: postgresql://user:pass@db:5432/chatbot_db
  - `ODOO_URL`: http://odoo:8069
  - `ODOO_API_KEY`: (for Odoo API calls)
  - `OLLAMA_BASE_URL`: http://ollama:11434
  - `EMBEDDING_MODEL`: all-minilm-l6-v2

#### 4. Ollama Service (Optional - can run separately)
- **Image**: `ollama/ollama:latest`
- **Port**: `11434`
- **Volumes**: Model storage

---

## Project Structure

```
project-root/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── PLAN.md
│
├── odoo_service/
│   ├── Dockerfile
│   ├── docker-compose.override.yml
│   ├── config/
│   │   └── odoo.conf
│   ├── custom_addons/
│   │   └── chatbot_platform/
│   │       ├── __init__.py
│   │       ├── __manifest__.py
│   │       ├── models/
│   │       │   ├── __init__.py
│   │       │   ├── chatbot.py
│   │       │   ├── chatbot_document.py
│   │       │   ├── chatbot_link.py
│   │       │   ├── chatbot_prompt.py
│   │       │   └── chatbot_api_key.py
│   │       ├── views/
│   │       │   ├── __init__.py
│   │       │   ├── chatbot_views.xml
│   │       │   ├── document_views.xml
│   │       │   └── menu_views.xml
│   │       ├── controllers/
│   │       │   ├── __init__.py
│   │       │   └── api_controller.py
│   │       ├── security/
│   │       │   ├── ir.model.access.csv
│   │       │   └── chatbot_security.xml
│   │       └── data/
│   │           └── chatbot_data.xml
│   └── data/
│       └── .gitkeep
│
├── fastapi_service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py
│   │   │   └── models.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py
│   │   │   └── chatbot.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── public.py
│   │   │   ├── internal.py
│   │   │   └── webhook.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── embedding_service.py
│   │   │   ├── vector_store.py
│   │   │   ├── rag_service.py
│   │   │   ├── document_processor.py
│   │   │   ├── sync_service.py
│   │   │   └── auth_service.py
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   └── auth.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logger.py
│   │       └── exceptions.py
│   └── uploads/
│       └── .gitkeep
│
└── postgres_service/
    ├── init.sql
    └── docker-entrypoint-initdb.d/
        └── 01-init-pgvector.sql
```

---

## Database Schema

### Odoo Models (PostgreSQL via Odoo ORM)

#### 1. chatbot.chatbot
```python
Fields:
- id: Integer (auto) - Primary key, used as chatbot_id
- name: Char(255) - Chatbot name
- user_id: Many2one(res.users) - Owner
- description: Text - Optional description
- api_key_hash: Char(64) - SHA-256 hash of API key
- api_key_prefix: Char(20) - Display prefix (e.g., "YOUR_API_KEY_HERE...")
- is_public: Boolean - Whether chatbot is publicly accessible
- allowed_domains: Text - Comma-separated allowed domains
- status: Selection - ['draft', 'active', 'archived']
- created_at: Datetime
- updated_at: Datetime
```

#### 2. chatbot.document
```python
Fields:
- id: Integer (auto)
- chatbot_id: Many2one(chatbot.chatbot) - Required
- name: Char(255) - File name
- file_path: Char(255) - Storage path
- file_type: Char(50) - pdf, docx, txt, etc.
- content: Text - Extracted text content
- file_size: Integer - Size in bytes
- processed: Boolean - Whether embedded in pgvector
- vector_sync_status: Selection - ['pending', 'synced', 'error']
- uploaded_at: Datetime
- updated_at: Datetime
```

#### 3. chatbot.link
```python
Fields:
- id: Integer (auto)
- chatbot_id: Many2one(chatbot.chatbot) - Required
- url: Char(512) - Link URL
- title: Char(255) - Page title
- content: Text - Scraped content
- processed: Boolean - Whether embedded in pgvector
- vector_sync_status: Selection - ['pending', 'synced', 'error']
- created_at: Datetime
- updated_at: Datetime
```

#### 4. chatbot.prompt
```python
Fields:
- id: Integer (auto)
- chatbot_id: Many2one(chatbot.chatbot) - Required
- prompt_text: Text - Prompt content
- prompt_type: Selection - ['system', 'user_template']
- order: Integer - Display order
- is_active: Boolean
- created_at: Datetime
```

#### 5. chatbot.api_key (for key management)
```python
Fields:
- id: Integer (auto)
- chatbot_id: Many2one(chatbot.chatbot) - Required
- key_hash: Char(64) - SHA-256 hash
- key_prefix: Char(20) - Display prefix
- name: Char(255) - User-friendly name
- is_active: Boolean
- last_used_at: Datetime
- expires_at: Datetime (optional)
- created_at: Datetime
```

### PostgreSQL + pgvector Schema

#### 1. chatbot_embeddings
```sql
CREATE TABLE chatbot_embeddings (
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

-- Indexes
CREATE INDEX idx_chatbot_embeddings_chatbot_id ON chatbot_embeddings(chatbot_id);
CREATE INDEX idx_chatbot_embeddings_source ON chatbot_embeddings(chatbot_id, source_type, source_id);
CREATE INDEX idx_chatbot_embeddings_vector ON chatbot_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

#### 2. chatbot_sessions
```sql
CREATE TABLE chatbot_sessions (
    id SERIAL PRIMARY KEY,
    chatbot_id INTEGER NOT NULL,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    conversation_history JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chatbot_sessions_chatbot ON chatbot_sessions(chatbot_id, session_id);
```

#### 3. api_key_usage (analytics)
```sql
CREATE TABLE api_key_usage (
    id SERIAL PRIMARY KEY,
    chatbot_id INTEGER NOT NULL,
    api_key_hash VARCHAR(64) NOT NULL,
    endpoint VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_api_key_usage_chatbot ON api_key_usage(chatbot_id, created_at);
```

---

## Odoo Module Design

### Module: chatbot_platform

#### Models Implementation

**chatbot.py** - Main chatbot model
- Inherits from `models.Model`
- Methods:
  - `generate_api_key()`: Generate and hash API key
  - `regenerate_api_key()`: Create new key, invalidate old
  - `get_embed_code()`: Generate iframe/JS embed code
  - `sync_to_fastapi()`: Trigger webhook to FastAPI

**chatbot_document.py** - Document model
- Inherits from `models.Model`
- Methods:
  - `_extract_text()`: Extract text from uploaded file
  - `sync_to_fastapi()`: Send to FastAPI for embedding
  - `unlink()`: Override to delete from pgvector on Odoo delete

**chatbot_link.py** - Link model
- Inherits from `models.Model`
- Methods:
  - `_scrape_content()`: Scrape content from URL
  - `sync_to_fastapi()`: Send to FastAPI for embedding
  - `unlink()`: Override to delete from pgvector

**chatbot_prompt.py** - Prompt model
- Inherits from `models.Model`
- Simple CRUD, no vector sync needed (used in RAG context)

#### Views

**chatbot_views.xml**
- Form view: Chatbot creation/editing
- Tree view: List of chatbots
- Kanban view: Visual chatbot cards
- Fields: API key display with copy button, embed code preview

**document_views.xml**
- Form view: Document upload
- Tree view: Document list with sync status
- Action buttons: "Sync to Vector DB", "Re-process"

#### Controllers

**api_controller.py**
- Webhook endpoint for FastAPI callbacks
- Internal API for Odoo → FastAPI communication

#### Security

**ir.model.access.csv**
- Access rules for chatbot models
- User can only access their own chatbots

**chatbot_security.xml**
- Record rules for multi-tenant isolation

---

## FastAPI Service Design

### Application Structure

#### main.py
- FastAPI app initialization
- Middleware setup (CORS, auth, rate limiting)
- Router registration
- Startup/shutdown events

#### config.py
- Environment variable management
- Database connection strings
- Service URLs
- Model configurations

### Routers

#### public.py - Public Endpoints
- `POST /api/public/chatbot/{chatbot_id}/chat`: Chat endpoint
- `GET /api/public/chatbot/{chatbot_id}/widget`: Widget HTML
- `GET /api/public/chatbot/{chatbot_id}/health`: Health check

#### internal.py - Internal Endpoints (Odoo → FastAPI)
- `POST /api/internal/chatbot/{chatbot_id}/sync`: Sync chatbot data
- `POST /api/internal/document/{document_id}/embed`: Embed document
- `POST /api/internal/link/{link_id}/embed`: Embed link
- `DELETE /api/internal/chatbot/{chatbot_id}/source/{source_type}/{source_id}`: Delete from vector DB

#### webhook.py - Webhook Endpoints
- `POST /api/webhook/chatbot/{chatbot_id}/updated`: Chatbot updated
- `POST /api/webhook/document/{document_id}/updated`: Document updated

### Services

#### embedding_service.py
- Generate embeddings using Ollama or sentence-transformers
- Batch processing
- Chunking for large documents

#### vector_store.py
- pgvector operations
- Insert embeddings
- Update embeddings
- Delete embeddings
- Similarity search

#### rag_service.py
- RAG pipeline orchestration
- Query embedding
- Vector retrieval
- Context formatting
- LLM response generation

#### document_processor.py
- PDF text extraction
- DOCX processing
- TXT file handling
- Link scraping
- Text cleaning and chunking

#### sync_service.py
- Handle sync operations from Odoo
- Create/Update/Delete in pgvector
- Error handling and retry logic
- Status reporting back to Odoo

#### auth_service.py
- API key validation
- Chatbot access verification
- Domain restriction checking

### Middleware

#### auth.py
- API key extraction from headers/query
- Validation middleware
- Rate limiting per API key

---

## Synchronization Flow

### Automatic Synchronization Triggers

#### 1. Document Created
```
User uploads document in Odoo
    ↓
Odoo: chatbot.document.create()
    ↓
Odoo: Extract text content
    ↓
Odoo: HTTP POST to FastAPI /api/internal/document/{id}/embed
    ↓
FastAPI: Process document → Generate embeddings → Store in pgvector
    ↓
FastAPI: Update Odoo document.vector_sync_status = 'synced'
```

#### 2. Document Updated
```
User updates document in Odoo
    ↓
Odoo: chatbot.document.write()
    ↓
Odoo: Check if file_path or content changed
    ↓
Odoo: HTTP POST to FastAPI /api/internal/document/{id}/embed
    ↓
FastAPI: 
    1. DELETE all embeddings for document_id from pgvector
    2. Re-process document
    3. Generate new embeddings
    4. INSERT new embeddings
    ↓
FastAPI: Update Odoo document.vector_sync_status = 'synced'
```

#### 3. Document Deleted
```
User deletes document in Odoo
    ↓
Odoo: chatbot.document.unlink()
    ↓
Odoo: HTTP DELETE to FastAPI /api/internal/chatbot/{chatbot_id}/source/document/{document_id}
    ↓
FastAPI: DELETE all embeddings where source_type='document' AND source_id={document_id}
    ↓
FastAPI: Return success
```

#### 4. Link Created/Updated/Deleted
Same flow as documents, but with `source_type='link'`

#### 5. Chatbot Deleted
```
User deletes chatbot in Odoo
    ↓
Odoo: chatbot.chatbot.unlink()
    ↓
Odoo: HTTP DELETE to FastAPI /api/internal/chatbot/{chatbot_id}/cleanup
    ↓
FastAPI: DELETE all embeddings where chatbot_id={chatbot_id}
    ↓
FastAPI: DELETE all sessions for chatbot_id
    ↓
FastAPI: Return success
```

### Error Handling

- **Retry Logic**: Failed syncs retry 3 times with exponential backoff
- **Status Tracking**: `vector_sync_status` field tracks sync state
- **Error Logging**: Log sync errors for debugging
- **Manual Retry**: Users can manually trigger sync from Odoo UI

### Webhook Implementation (Alternative)

Instead of Odoo calling FastAPI directly, can use webhooks:
- Odoo triggers webhook on model changes
- FastAPI webhook endpoint processes the event
- More decoupled but requires webhook queue management

---

## API Endpoints

### Public Endpoints (API Key Required)

#### POST /api/public/chatbot/{chatbot_id}/chat
**Request:**
```json
{
  "message": "What is in document X?",
  "session_id": "optional_session_123"
}
```
**Headers:**
```
X-API-Key: YOUR_API_KEY_HERE...
```
**Response:**
```json
{
  "response": "Based on document X, ...",
  "sources": [
    {"type": "document", "id": 1, "name": "document1.pdf"},
    {"type": "link", "id": 2, "url": "https://example.com"}
  ],
  "session_id": "session_123"
}
```

#### GET /api/public/chatbot/{chatbot_id}/widget
**Query Params:**
```
?api_key=YOUR_API_KEY_HERE...
```
**Response:** HTML page with chatbot widget

### Internal Endpoints (Odoo → FastAPI)

#### POST /api/internal/document/{document_id}/embed
**Request:**
```json
{
  "chatbot_id": 123,
  "content": "Extracted text content...",
  "metadata": {
    "filename": "document.pdf",
    "file_type": "pdf",
    "file_size": 1024000
  }
}
```
**Headers:**
```
X-Odoo-API-Key: {internal_api_key}
```
**Response:**
```json
{
  "status": "success",
  "embeddings_count": 5,
  "message": "Document embedded successfully"
}
```

#### DELETE /api/internal/chatbot/{chatbot_id}/source/{source_type}/{source_id}
**Headers:**
```
X-Odoo-API-Key: {internal_api_key}
```
**Response:**
```json
{
  "status": "success",
  "deleted_count": 5
}
```

---

## Security Implementation

### API Key Security

1. **Generation**: `YOUR_API_KEY_HERE{32_random_chars}`
2. **Storage**: SHA-256 hash only (never plain text)
3. **Validation**: Hash comparison on every request
4. **Rotation**: Users can regenerate keys (invalidates old)

### Authentication Flow

```
Request → Extract API Key
        → Hash API Key
        → Query database for chatbot with matching hash
        → Verify chatbot is active
        → Verify domain (if restricted)
        → Allow request
```

### Domain Restrictions

- Users can specify allowed domains in chatbot settings
- FastAPI checks `Referer` or `Origin` header
- Block requests from unauthorized domains

### Rate Limiting

- Per API key: 100 requests/minute
- Per chatbot: 1000 requests/hour
- Global: 10000 requests/hour per IP

---

## Implementation Steps

### Phase 1: Infrastructure Setup
1. Create project structure
2. Set up Docker Compose with all services
3. Configure PostgreSQL with pgvector
4. Test service connectivity

### Phase 2: Database Setup
1. Create Odoo models
2. Create pgvector tables
3. Set up migrations
4. Test database operations

### Phase 3: Odoo Module Development
1. Implement chatbot model
2. Implement document/link/prompt models
3. Create views and UI
4. Implement API key generation
5. Implement webhook triggers

### Phase 4: FastAPI Service Development
1. Set up FastAPI application structure
2. Implement database connection
3. Implement embedding service
4. Implement vector store operations
5. Implement RAG pipeline
6. Implement sync service

### Phase 5: Integration
1. Connect Odoo → FastAPI for sync
2. Test document create/update/delete flows
3. Test link create/update/delete flows
4. Implement error handling

### Phase 6: Public Endpoints
1. Implement public chat endpoint
2. Implement widget endpoint
3. Implement authentication middleware
4. Test with API keys

### Phase 7: Testing
1. Unit tests for each service
2. Integration tests for sync flows
3. End-to-end tests
4. Load testing

### Phase 8: Documentation
1. API documentation
2. Setup guide
3. User guide
4. Developer guide

---

## Environment Variables

### Odoo Service
```env
ODOO_DB_HOST=db
ODOO_DB_PORT=5432
ODOO_DB_USER=odoo
ODOO_DB_PASSWORD=odoo_password
FASTAPI_URL=http://fastapi:8000
FASTAPI_INTERNAL_KEY=internal_api_key_here
```

### FastAPI Service
```env
DATABASE_URL=postgresql://chatbot_user:chatbot_password@db:5432/chatbot_db
ODOO_URL=http://odoo:8069
ODOO_API_KEY=odoo_api_key_here
OLLAMA_BASE_URL=http://ollama:11434
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### PostgreSQL Service
```env
POSTGRES_DB=chatbot_db
POSTGRES_USER=chatbot_user
POSTGRES_PASSWORD=chatbot_password
```

---

## Next Steps

1. Review and approve this plan
2. Create project structure
3. Set up Docker Compose
4. Begin implementation following the phases

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Status**: Planning Phase

