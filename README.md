# B2B Chatbot Platform

A multi-tenant B2B chatbot platform where users can create chatbots, add documents/links, and embed them on their websites with API key authentication.

## Features

- **User Management**: Create and manage chatbots through Odoo
- **Document Processing**: Upload documents (PDF, DOCX, TXT) and automatically generate embeddings
- **Link Processing**: Add web links, scrape content, and generate embeddings
- **RAG Pipeline**: Retrieval-Augmented Generation using LangChain, Ollama, and pgvector
- **API Key Authentication**: Secure access with unique API keys per chatbot
- **Embeddable Widgets**: Easy integration into any website via iframe or JavaScript
- **Automatic Synchronization**: Real-time sync between Odoo and pgvector
- **Multi-tenant**: Isolated data per user

## Architecture

- **Odoo Service**: User interface and chatbot management
- **FastAPI Service**: Public API, RAG pipeline, and vector operations
- **PostgreSQL + pgvector**: Vector database for embeddings
- **Ollama**: Local LLM runtime

## Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB+ RAM
- 20GB+ disk space

### Setup

1. **Clone the repository**
   ```bash
   cd /home/messi/messi/HH/CB
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your secure passwords
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize Odoo**
   - Access http://localhost:8069
   - Create database
   - Install `chatbot_platform` module

5. **Verify services**
   ```bash
   # Check FastAPI
   curl http://localhost:8000/health
   
   # Check Odoo
   curl http://localhost:8069
   ```

## Documentation

- **[PLAN.md](PLAN.md)**: Comprehensive implementation plan
- **[DOCKER_SETUP.md](DOCKER_SETUP.md)**: Detailed Docker setup guide
- **[API_SPECIFICATION.md](API_SPECIFICATION.md)**: Complete API documentation
- **[SYNCHRONIZATION_FLOW.md](SYNCHRONIZATION_FLOW.md)**: Odoo ↔ FastAPI sync details

## Project Structure

```
project-root/
├── PLAN.md                      # Main implementation plan
├── DOCKER_SETUP.md              # Docker setup guide
├── API_SPECIFICATION.md         # API documentation
├── SYNCHRONIZATION_FLOW.md      # Sync flow details
├── README.md                    # This file
├── docker-compose.yml           # Docker Compose configuration
├── .env.example                 # Environment variables template
├── odoo_service/                # Odoo service
│   ├── Dockerfile
│   ├── custom_addons/           # Custom Odoo modules
│   └── config/                  # Odoo configuration
├── fastapi_service/             # FastAPI service
│   ├── Dockerfile
│   ├── app/                     # Application code
│   └── requirements.txt
└── postgres_service/            # PostgreSQL initialization
    └── init.sql
```

## Services

### Odoo (Port 8069)
- User interface for chatbot management
- Document and link management
- API key generation
- Webhook triggers to FastAPI

### FastAPI (Port 8000)
- Public chatbot endpoints
- Internal sync endpoints
- RAG pipeline
- Vector operations

### PostgreSQL (Port 5432)
- Main database
- pgvector extension for embeddings
- Session storage

### Ollama (Port 11434)
- LLM inference
- Embedding generation (optional)

## Usage

### Creating a Chatbot

1. Log in to Odoo
2. Navigate to Chatbots menu
3. Create new chatbot
4. System generates API key automatically
5. Copy embed code for your website

### Adding Documents

1. Open chatbot
2. Go to Documents tab
3. Upload document (PDF, DOCX, TXT)
4. System automatically:
   - Extracts text
   - Generates embeddings
   - Stores in pgvector

### Embedding Chatbot

Use the generated embed code in your website:

**Iframe:**
```html
<iframe 
  src="http://localhost:8000/api/public/chatbot/123/widget?api_key=YOUR_API_KEY_HERE..."
  width="400"
  height="600">
</iframe>
```

**JavaScript:**
```html
<script>
  window.chatbotConfig = {
    chatbotId: 123,
    apiKey: 'YOUR_API_KEY_HERE...',
    baseUrl: 'http://localhost:8000'
  };
  // Load widget script
</script>
```

## API Endpoints

### Public Endpoints
- `POST /api/public/chatbot/{chatbot_id}/chat` - Chat with chatbot
- `GET /api/public/chatbot/{chatbot_id}/widget` - Get widget HTML
- `GET /api/public/chatbot/{chatbot_id}/health` - Health check

### Internal Endpoints
- `POST /api/internal/document/{id}/embed` - Embed document
- `POST /api/internal/link/{id}/embed` - Embed link
- `DELETE /api/internal/chatbot/{id}/source/{type}/{source_id}` - Delete source
- `DELETE /api/internal/chatbot/{id}/cleanup` - Cleanup chatbot

See [API_SPECIFICATION.md](API_SPECIFICATION.md) for complete documentation.

## Development

### Running in Development Mode

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Restart service
docker-compose restart fastapi
docker-compose restart odoo
```

### Adding New Features

1. **Odoo Module**: Add to `odoo_service/custom_addons/chatbot_platform/`
2. **FastAPI**: Add to `fastapi_service/app/`
3. **Database**: Add migrations to `postgres_service/`

### Testing

```bash
# Run tests in FastAPI container
docker-compose exec fastapi pytest

# Test API endpoints
curl -X POST http://localhost:8000/api/public/chatbot/1/chat \
  -H "X-API-Key: YOUR_API_KEY_HERE..." \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

## Configuration

### Environment Variables

See `.env.example` for all configuration options:

- Database credentials
- API keys
- Model settings
- Service URLs

### Odoo Configuration

Edit `odoo_service/config/odoo.conf` for Odoo-specific settings.

## Troubleshooting

### Services Not Starting
- Check Docker logs: `docker-compose logs`
- Verify environment variables
- Check port conflicts

### Sync Issues
- Check FastAPI logs: `docker-compose logs fastapi`
- Verify internal API key
- Check network connectivity between services

### Database Issues
- Verify PostgreSQL is healthy: `docker-compose ps`
- Check database credentials
- Review init scripts

## Security

- API keys are hashed (SHA-256) before storage
- HTTPS recommended for production
- Domain restrictions available
- Rate limiting enabled
- Input validation on all endpoints

## License

[Your License Here]

## Support

For issues and questions, please refer to the documentation files or create an issue.

---

**Version**: 1.0.0  
**Last Updated**: 2024-01-15

