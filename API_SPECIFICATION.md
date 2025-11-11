# API Specification

## Base URLs
- **FastAPI**: `http://localhost:8000` (development) / `https://api.yourdomain.com` (production)
- **Odoo**: `http://localhost:8069` (development) / `https://odoo.yourdomain.com` (production)

## Authentication

### Authentication Methods
1. **Header** (Recommended): `X-API-Key: YOUR_API_KEY_HERE`
2. **Query Parameter**: `?api_key=YOUR_API_KEY_HERE`
3. **Request Body**: `{"api_key": "YOUR_API_KEY_HERE"}`

### Internal API Authentication
- Header: `X-Odoo-API-Key: {internal_api_key}`
- Used for Odoo → FastAPI communication

---

## Public Endpoints

### POST /api/public/chatbot/{chatbot_id}/chat
Send a message to the chatbot and receive a response.

**Path Parameters:**
- `chatbot_id` (integer, required): The chatbot ID

**Headers:**
```
X-API-Key: YOUR_API_KEY_HERE
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "What is in document X?",
  "session_id": "optional_session_123"
}
```

**Response 200 OK:**
```json
{
  "response": "Based on document X, the content includes...",
  "sources": [
    {
      "type": "document",
      "id": 1,
      "name": "document1.pdf",
      "relevance_score": 0.95
    },
    {
      "type": "link",
      "id": 2,
      "url": "https://example.com",
      "relevance_score": 0.87
    }
  ],
  "session_id": "session_123",
  "metadata": {
    "model": "llama2",
    "tokens_used": 150,
    "response_time_ms": 1200
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or missing API key
- `403 Forbidden`: API key doesn't match chatbot, chatbot inactive, or domain not allowed
- `404 Not Found`: Chatbot not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

---

### GET /api/public/chatbot/{chatbot_id}/widget
Get the embeddable widget HTML page.

**Path Parameters:**
- `chatbot_id` (integer, required): The chatbot ID

**Query Parameters:**
- `api_key` (string, required): API key for authentication

**Example Request:**
```
GET /api/public/chatbot/123/widget?api_key=YOUR_API_KEY_HERE
```

**Response 200 OK:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Chatbot Widget</title>
    <style>/* Widget styles */</style>
</head>
<body>
    <div id="chatbot-widget">
        <!-- Widget interface -->
    </div>
    <script>
        // Widget JavaScript
        const chatbotConfig = {
            chatbotId: 123,
            apiKey: 'YOUR_API_KEY_HERE',
            baseUrl: 'http://localhost:8000'
        };
        // Initialize widget
    </script>
</body>
</html>
```

**Error Responses:**
- `401 Unauthorized`: Invalid API key
- `403 Forbidden`: Access denied
- `404 Not Found`: Chatbot not found

---

### GET /api/public/chatbot/{chatbot_id}/health
Health check endpoint (no authentication required).

**Path Parameters:**
- `chatbot_id` (integer, required): The chatbot ID

**Response 200 OK:**
```json
{
  "status": "healthy",
  "chatbot_id": 123,
  "chatbot_status": "active",
  "embeddings_count": 150
}
```

**Response 503 Service Unavailable:**
```json
{
  "status": "unhealthy",
  "chatbot_id": 123,
  "chatbot_status": "inactive",
  "error": "Chatbot is not active"
}
```

---

## Internal Endpoints (Odoo → FastAPI)

### POST /api/internal/document/{document_id}/embed
Process and embed a document into pgvector.

**Path Parameters:**
- `document_id` (integer, required): Document ID from Odoo

**Headers:**
```
X-Odoo-API-Key: {internal_api_key}
Content-Type: application/json
```

**Request Body:**
```json
{
  "chatbot_id": 123,
  "content": "Extracted text content from document...",
  "metadata": {
    "filename": "document.pdf",
    "file_type": "pdf",
    "file_size": 1024000,
    "uploaded_at": "2024-01-15T10:30:00Z"
  }
}
```

**Response 200 OK:**
```json
{
  "status": "success",
  "document_id": 456,
  "chatbot_id": 123,
  "embeddings_count": 5,
  "chunks_created": 5,
  "message": "Document embedded successfully"
}
```

**Response 400 Bad Request:**
```json
{
  "status": "error",
  "error": "Invalid content or metadata",
  "details": "Content cannot be empty"
}
```

**Response 401 Unauthorized:**
```json
{
  "status": "error",
  "error": "Invalid internal API key"
}
```

---

### POST /api/internal/link/{link_id}/embed
Process and embed a link's content into pgvector.

**Path Parameters:**
- `link_id` (integer, required): Link ID from Odoo

**Headers:**
```
X-Odoo-API-Key: {internal_api_key}
Content-Type: application/json
```

**Request Body:**
```json
{
  "chatbot_id": 123,
  "url": "https://example.com/article",
  "content": "Scraped content from URL...",
  "metadata": {
    "title": "Article Title",
    "scraped_at": "2024-01-15T10:30:00Z"
  }
}
```

**Response 200 OK:**
```json
{
  "status": "success",
  "link_id": 789,
  "chatbot_id": 123,
  "embeddings_count": 3,
  "chunks_created": 3,
  "message": "Link embedded successfully"
}
```

---

### DELETE /api/internal/chatbot/{chatbot_id}/source/{source_type}/{source_id}
Delete embeddings for a specific source from pgvector.

**Path Parameters:**
- `chatbot_id` (integer, required): Chatbot ID
- `source_type` (string, required): `document` or `link`
- `source_id` (integer, required): Source ID from Odoo

**Headers:**
```
X-Odoo-API-Key: {internal_api_key}
```

**Response 200 OK:**
```json
{
  "status": "success",
  "chatbot_id": 123,
  "source_type": "document",
  "source_id": 456,
  "deleted_count": 5,
  "message": "Embeddings deleted successfully"
}
```

**Response 404 Not Found:**
```json
{
  "status": "error",
  "error": "No embeddings found for the specified source"
}
```

---

### DELETE /api/internal/chatbot/{chatbot_id}/cleanup
Delete all embeddings and sessions for a chatbot (used when chatbot is deleted).

**Path Parameters:**
- `chatbot_id` (integer, required): Chatbot ID

**Headers:**
```
X-Odoo-API-Key: {internal_api_key}
```

**Response 200 OK:**
```json
{
  "status": "success",
  "chatbot_id": 123,
  "embeddings_deleted": 150,
  "sessions_deleted": 25,
  "message": "Chatbot data cleaned up successfully"
}
```

---

### POST /api/internal/chatbot/{chatbot_id}/sync
Full synchronization of chatbot data (re-process all documents and links).

**Path Parameters:**
- `chatbot_id` (integer, required): Chatbot ID

**Headers:**
```
X-Odoo-API-Key: {internal_api_key}
Content-Type: application/json
```

**Request Body:**
```json
{
  "documents": [
    {
      "id": 456,
      "content": "Document content...",
      "metadata": {"filename": "doc1.pdf"}
    }
  ],
  "links": [
    {
      "id": 789,
      "content": "Link content...",
      "metadata": {"url": "https://example.com"}
    }
  ]
}
```

**Response 200 OK:**
```json
{
  "status": "success",
  "chatbot_id": 123,
  "documents_processed": 5,
  "links_processed": 3,
  "total_embeddings": 40,
  "message": "Synchronization completed"
}
```

---

## Webhook Endpoints (Alternative Sync Method)

### POST /api/webhook/chatbot/{chatbot_id}/updated
Webhook endpoint for chatbot updates.

**Path Parameters:**
- `chatbot_id` (integer, required): Chatbot ID

**Headers:**
```
X-Webhook-Signature: {signature}
Content-Type: application/json
```

**Request Body:**
```json
{
  "event": "chatbot.updated",
  "chatbot_id": 123,
  "changes": {
    "status": "active",
    "is_public": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Error Response Format

All error responses follow this format:

```json
{
  "status": "error",
  "error": "Error type",
  "message": "Human-readable error message",
  "details": "Additional error details (optional)",
  "code": "ERROR_CODE"
}
```

### Common Error Codes
- `INVALID_API_KEY`: API key is invalid or missing
- `CHATBOT_NOT_FOUND`: Chatbot ID does not exist
- `CHATBOT_INACTIVE`: Chatbot is not active
- `DOMAIN_NOT_ALLOWED`: Request origin domain is not in allowed list
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INVALID_CONTENT`: Content validation failed
- `EMBEDDING_FAILED`: Failed to generate embeddings
- `VECTOR_STORE_ERROR`: Database operation failed
- `INTERNAL_ERROR`: Server error

---

## Rate Limiting

### Limits
- **Per API Key**: 100 requests/minute
- **Per Chatbot**: 1000 requests/hour
- **Per IP**: 10000 requests/hour

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705312800
```

### Rate Limit Exceeded Response
```json
{
  "status": "error",
  "error": "Rate limit exceeded",
  "message": "You have exceeded the rate limit of 100 requests per minute",
  "retry_after": 30
}
```

---

## Request/Response Examples

### cURL Examples

#### Public Chat
```bash
curl -X POST "http://localhost:8000/api/public/chatbot/123/chat" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, what can you help me with?",
    "session_id": "session_123"
  }'
```

#### Embed Document (Internal)
```bash
curl -X POST "http://localhost:8000/api/internal/document/456/embed" \
  -H "X-Odoo-API-Key: internal_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "chatbot_id": 123,
    "content": "Document content here...",
    "metadata": {
      "filename": "document.pdf",
      "file_type": "pdf"
    }
  }'
```

#### Delete Source (Internal)
```bash
curl -X DELETE "http://localhost:8000/api/internal/chatbot/123/source/document/456" \
  -H "X-Odoo-API-Key: internal_key_here"
```

---

## WebSocket Support (Future)

### WS /api/public/chatbot/{chatbot_id}/chat/stream
Streaming chat endpoint for real-time responses.

**Authentication:** Same as REST endpoints (API key in query or header)

**Message Format:**
```json
{
  "type": "message",
  "content": "User message here"
}
```

**Response Format:**
```json
{
  "type": "chunk",
  "content": "Partial response",
  "done": false
}
```

---

## Versioning

Current API version: `v1`

Version can be specified in:
- URL: `/api/v1/public/chatbot/...`
- Header: `API-Version: v1`

Default: `v1` (if not specified)

---

## Changelog

### v1.0.0 (2024-01-15)
- Initial API specification
- Public chat endpoints
- Internal sync endpoints
- Widget endpoint

---

**Last Updated**: 2024-01-15  
**API Version**: 1.0.0

