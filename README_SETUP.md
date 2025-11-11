# B2B Chatbot Platform - Individual Services Setup

## 📁 Project Structure

```
/CB/
├── odoo_service/
│   ├── docker-compose.yml      # Odoo + PostgreSQL
│   ├── env.example             # Odoo environment variables
│   ├── Dockerfile
│   ├── config/
│   └── custom_addons/
│
└── fastapi_service/
    ├── docker-compose.yml      # FastAPI + PostgreSQL + Ollama
    ├── env.example             # FastAPI environment variables
    ├── Dockerfile
    ├── init.sql                # Database initialization
    └── app/
```

## 🚀 Setup Instructions

### 1. Setup Odoo Service

```bash
cd odoo_service
cp env.example .env
# Edit .env with your passwords
docker-compose up -d
```

**Access:** http://localhost:8069

### 2. Setup FastAPI Service

```bash
cd fastapi_service
cp env.example .env
# Edit .env with your passwords
docker-compose up -d
```

**Access:** http://localhost:8000/docs

## 🔧 Service Details

### Odoo Service
- **Port**: 8069
- **Database**: PostgreSQL on port 5433
- **Container Names**: `odoo_app`, `odoo_db`
- **Network**: `odoo_network`

### FastAPI Service
- **Port**: 8000
- **Database**: PostgreSQL on port 5432 (with pgvector)
- **Ollama**: Port 11434
- **Container Names**: `fastapi_app`, `fastapi_db`, `fastapi_ollama`
- **Network**: `fastapi_network`

## 📋 Commands

### Start Individual Services

**Odoo:**
```bash
cd odoo_service
docker-compose up -d
```

**FastAPI:**
```bash
cd fastapi_service
docker-compose up -d
```

### View Logs
```bash
# In respective service directory
docker-compose logs -f
```

### Stop Services
```bash
# In respective service directory
docker-compose down
```

### Rebuild Services
```bash
# In respective service directory
docker-compose up -d --build
```

## 🔗 Service Communication

Since services are now separate, they communicate via:
- **Odoo → FastAPI**: HTTP calls to `http://localhost:8000`
- **FastAPI → Odoo**: HTTP calls to `http://localhost:8069`

Make sure both services are running for full functionality.

## 🗄️ Databases

Each service has its own PostgreSQL instance:
- **Odoo**: Standard PostgreSQL (port 5433)
- **FastAPI**: PostgreSQL with pgvector extension (port 5432)

## ⚙️ Configuration

Edit the respective `.env` files in each service directory:

**odoo_service/.env:**
- Odoo database credentials
- FastAPI URL for integration

**fastapi_service/.env:**
- FastAPI database credentials
- Odoo URL for integration
- Embedding model settings

## 🎯 Next Steps

1. Start both services
2. Access Odoo and install `chatbot_platform` module
3. Create chatbots and test the integration
4. FastAPI will handle the vector operations and RAG pipeline
