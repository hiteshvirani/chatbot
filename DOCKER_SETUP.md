# Docker Setup Guide

## Overview
This document provides detailed instructions for setting up the B2B Chatbot Platform using Docker and Docker Compose.

## Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 8GB RAM
- 20GB free disk space

## Project Structure
```
project-root/
├── docker-compose.yml          # Main compose file
├── .env                        # Environment variables
├── .env.example                # Example env file
├── odoo_service/
│   ├── Dockerfile
│   └── custom_addons/          # Mounted to Odoo
├── fastapi_service/
│   ├── Dockerfile
│   └── app/                    # Application code
└── postgres_service/
    └── init.sql                # Database initialization
```

## Docker Compose Configuration

### Main docker-compose.yml
```yaml
version: '3.8'

services:
  # PostgreSQL with pgvector
  db:
    image: pgvector/pgvector:pg16
    container_name: chatbot_db
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-chatbot_db}
      POSTGRES_USER: ${POSTGRES_USER:-chatbot_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres_service/init.sql:/docker-entrypoint-initdb.d/01-init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-chatbot_user}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - chatbot_network

  # Odoo Service
  odoo:
    build:
      context: ./odoo_service
      dockerfile: Dockerfile
    container_name: chatbot_odoo
    depends_on:
      db:
        condition: service_healthy
    environment:
      HOST: db
      USER: ${ODOO_DB_USER:-odoo}
      PASSWORD: ${ODOO_DB_PASSWORD}
      POSTGRES_HOST: db
      POSTGRES_PORT: 5432
      POSTGRES_USER: ${ODOO_DB_USER:-odoo}
      POSTGRES_PASSWORD: ${ODOO_DB_PASSWORD}
      POSTGRES_DB: ${ODOO_DB_NAME:-postgres}
      FASTAPI_URL: http://fastapi:8000
      FASTAPI_INTERNAL_KEY: ${FASTAPI_INTERNAL_KEY}
    volumes:
      - ./odoo_service/custom_addons:/mnt/extra-addons
      - ./odoo_service/config:/etc/odoo
      - odoo_data:/var/lib/odoo
      - odoo_filestore:/var/lib/odoo/filestore
    ports:
      - "8069:8069"
    networks:
      - chatbot_network
    command: odoo -c /etc/odoo/odoo.conf

  # FastAPI Service
  fastapi:
    build:
      context: ./fastapi_service
      dockerfile: Dockerfile
    container_name: chatbot_fastapi
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-chatbot_user}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB:-chatbot_db}
      ODOO_URL: http://odoo:8069
      ODOO_API_KEY: ${ODOO_API_KEY}
      OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-http://ollama:11434}
      EMBEDDING_MODEL: ${EMBEDDING_MODEL:-all-MiniLM-L6-v2}
      EMBEDDING_DIMENSION: ${EMBEDDING_DIMENSION:-384}
      CHUNK_SIZE: ${CHUNK_SIZE:-1000}
      CHUNK_OVERLAP: ${CHUNK_OVERLAP:-200}
      INTERNAL_API_KEY: ${FASTAPI_INTERNAL_KEY}
    volumes:
      - ./fastapi_service/app:/app
      - ./fastapi_service/uploads:/app/uploads
    ports:
      - "8000:8000"
    networks:
      - chatbot_network
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Ollama Service (Optional - can run separately)
  ollama:
    image: ollama/ollama:latest
    container_name: chatbot_ollama
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    networks:
      - chatbot_network
    environment:
      - OLLAMA_HOST=0.0.0.0

volumes:
  postgres_data:
  odoo_data:
  odoo_filestore:
  ollama_data:

networks:
  chatbot_network:
    driver: bridge
```

## Odoo Dockerfile

### odoo_service/Dockerfile
```dockerfile
FROM odoo:17

# Install system dependencies
USER root
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for custom modules
RUN pip3 install --no-cache-dir \
    requests \
    python-dotenv

# Switch back to odoo user
USER odoo

# Set working directory
WORKDIR /var/lib/odoo

# Expose Odoo port
EXPOSE 8069
```

## FastAPI Dockerfile

### fastapi_service/Dockerfile
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## PostgreSQL Initialization

### postgres_service/init.sql
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create database if not exists (handled by POSTGRES_DB env var)
-- But we can create additional databases here if needed

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE chatbot_db TO chatbot_user;
```

## Environment Variables

### .env.example
```env
# PostgreSQL Configuration
POSTGRES_DB=chatbot_db
POSTGRES_USER=chatbot_user
POSTGRES_PASSWORD=change_me_secure_password

# Odoo Configuration
ODOO_DB_USER=odoo
ODOO_DB_PASSWORD=change_me_odoo_password
ODOO_DB_NAME=postgres

# FastAPI Configuration
FASTAPI_INTERNAL_KEY=change_me_internal_api_key
ODOO_API_KEY=change_me_odoo_api_key

# Ollama Configuration
OLLAMA_BASE_URL=http://ollama:11434

# Embedding Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## Setup Instructions

### 1. Clone/Create Project
```bash
cd /home/messi/messi/HH/CB
```

### 2. Create Environment File
```bash
cp .env.example .env
# Edit .env with your secure passwords
```

### 3. Create Directory Structure
```bash
mkdir -p odoo_service/custom_addons
mkdir -p odoo_service/config
mkdir -p odoo_service/data
mkdir -p fastapi_service/app
mkdir -p fastapi_service/uploads
mkdir -p postgres_service
```

### 4. Build and Start Services
```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 5. Initialize Odoo Database
1. Access Odoo at http://localhost:8069
2. Create database with master password
3. Install chatbot_platform module

### 6. Verify Services
```bash
# Check PostgreSQL
docker-compose exec db psql -U chatbot_user -d chatbot_db -c "SELECT * FROM pg_extension WHERE extname='vector';"

# Check FastAPI
curl http://localhost:8000/health

# Check Odoo
curl http://localhost:8069
```

## Development Workflow

### Hot Reload
- FastAPI: Auto-reloads on code changes (--reload flag)
- Odoo: Restart container to load new modules
  ```bash
  docker-compose restart odoo
  ```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f fastapi
docker-compose logs -f odoo
docker-compose logs -f db
```

### Execute Commands in Containers
```bash
# FastAPI container
docker-compose exec fastapi bash
docker-compose exec fastapi python -m app.scripts.migrate

# Odoo container
docker-compose exec odoo odoo shell -d your_database

# PostgreSQL container
docker-compose exec db psql -U chatbot_user -d chatbot_db
```

### Database Backup
```bash
# Backup
docker-compose exec db pg_dump -U chatbot_user chatbot_db > backup.sql

# Restore
docker-compose exec -T db psql -U chatbot_user chatbot_db < backup.sql
```

## Troubleshooting

### Services Not Starting
1. Check logs: `docker-compose logs`
2. Verify environment variables in `.env`
3. Check port conflicts: `netstat -tulpn | grep -E '8069|8000|5432'`
4. Verify Docker resources: `docker system df`

### Database Connection Issues
1. Wait for PostgreSQL to be healthy: `docker-compose ps`
2. Check database credentials in `.env`
3. Verify network: `docker network inspect chatbot_chatbot_network`

### Module Not Loading in Odoo
1. Check volume mount: `docker-compose exec odoo ls -la /mnt/extra-addons`
2. Restart Odoo: `docker-compose restart odoo`
3. Check Odoo logs: `docker-compose logs odoo`

### FastAPI Import Errors
1. Check Python path in container
2. Verify requirements.txt installed
3. Check volume mount: `docker-compose exec fastapi ls -la /app`

## Production Considerations

### Security
- Change all default passwords
- Use secrets management (Docker secrets, Vault, etc.)
- Enable SSL/TLS for database connections
- Restrict network access
- Use read-only volumes where possible

### Performance
- Set resource limits in docker-compose.yml
- Use connection pooling
- Enable PostgreSQL query caching
- Use Redis for session management (optional)

### Monitoring
- Add health checks to all services
- Set up logging aggregation
- Monitor resource usage
- Set up alerts for service failures

## Cleanup

### Stop Services
```bash
docker-compose down
```

### Remove Volumes (WARNING: Deletes all data)
```bash
docker-compose down -v
```

### Remove Images
```bash
docker-compose down --rmi all
```

## Next Steps
After Docker setup is complete, proceed with:
1. Database schema creation
2. Odoo module development
3. FastAPI service implementation
4. Integration testing

