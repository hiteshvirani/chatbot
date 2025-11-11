# End-to-End Testing Results

## Test Date: 2025-11-11

### Services Status
- ✅ **Odoo**: Running on port 8069
- ❌ **FastAPI**: Not running (PyTorch/transformers compatibility issue)
- ✅ **PostgreSQL (Odoo)**: Running on port 5434
- ✅ **PostgreSQL (FastAPI)**: Running on port 5432

---

## Test 1: Chatbot Creation with Document ✅

**Command:**
```bash
curl -X POST http://localhost:8069/api/chatbot/create \
  -F "db=odoo_c" \
  -F "login=admin" \
  -F "password=admin" \
  -F "name=Embedding Test Chatbot" \
  -F "description=Testing document embedding flow" \
  -F "is_public=true" \
  -F "links=[]" \
  -F "files=@/tmp/test_embedding.txt"
```

**Result:**
```json
{
    "success": true,
    "chatbot_id": 20,
    "api_key": "YOUR_API_KEY_HERE",
    "document_ids": [5],
    "link_ids": []
}
```

**Status:** ✅ PASSED - Chatbot and document created successfully in Odoo

---

## Test 2: Document Sync to FastAPI ❌

**Expected Flow:**
1. Odoo creates document
2. Odoo extracts text content
3. Odoo calls FastAPI `/api/internal/document/{id}/embed`
4. FastAPI processes and embeds document
5. FastAPI stores embeddings in pgvector

**Actual Result:**
```
ERROR: Error syncing document 5: HTTPConnectionPool(host='fastapi', port=8000): 
Max retries exceeded with url: /api/internal/document/5/embed 
(Caused by NameResolutionError: Failed to resolve 'fastapi')
```

**Issues Found:**
1. ❌ Odoo trying to connect to `fastapi:8000` (Docker service name) but services are on different networks
2. ❌ FastAPI not running due to PyTorch/transformers compatibility issue

**Status:** ❌ FAILED - Sync not working

---

## Issues Fixed

### 1. FastAPI URL Resolution ✅
- **Problem:** Odoo was using hardcoded `http://fastapi:8000` which doesn't resolve
- **Fix:** Updated all model files to use `FASTAPI_URL` environment variable first, then fallback to `http://host.docker.internal:8000`
- **Files Changed:**
  - `odoo_service/custom_addons/chatbot_platform/models/chatbot_document.py`
  - `odoo_service/custom_addons/chatbot_platform/models/chatbot_link.py`
  - `odoo_service/custom_addons/chatbot_platform/models/chatbot.py`

### 2. FastAPI Config Validation ✅
- **Problem:** Pydantic rejecting extra environment variables
- **Fix:** Added `extra = "ignore"` to Settings config
- **File:** `fastapi_service/app/config.py`

---

## Issues Remaining

### 1. FastAPI PyTorch/Transformers Compatibility ❌
**Error:**
```
AttributeError: module 'torch.utils._pytree' has no attribute 'register_pytree_node'
```

**Root Cause:** Version incompatibility between:
- `torch==2.1.0+cpu`
- `sentence-transformers==2.2.2`
- `transformers` (dependency of sentence-transformers)

**Solution Options:**
1. Update PyTorch to compatible version
2. Add Ollama support as alternative embedding method
3. Use older sentence-transformers version

**Priority:** HIGH - Blocks all embedding functionality

---

## Next Steps

1. ✅ Fix FastAPI URL resolution in Odoo (DONE)
2. ⏳ Fix FastAPI PyTorch dependencies
3. ⏳ Test document sync: Odoo → FastAPI
4. ⏳ Verify embeddings stored in pgvector
5. ⏳ Test full RAG flow: Query → Embedding → Vector Search → Response

---

## Test Commands

### Test Document Sync
```bash
# Create chatbot with document
curl -X POST http://localhost:8069/api/chatbot/create \
  -F "db=odoo_c" \
  -F "login=admin" \
  -F "password=admin" \
  -F "name=Test" \
  -F "files=@test.txt"

# Check Odoo logs
docker-compose -f odoo_service/docker-compose.yml logs odoo | grep -i sync

# Check FastAPI logs
docker-compose -f fastapi_service/docker-compose.yml logs fastapi | grep -i embed
```

### Test pgvector
```bash
# Connect to FastAPI database
docker exec -it fastapi_db psql -U chatbot_user -d chatbot_db

# Check embeddings
SELECT chatbot_id, source_type, source_id, chunk_index, 
       LENGTH(content) as content_length 
FROM chatbot_embeddings 
ORDER BY created_at DESC 
LIMIT 10;
```

---

## Configuration Notes

- **Odoo FastAPI URL:** Set via `FASTAPI_URL` environment variable (default: `http://host.docker.internal:8000`)
- **FastAPI Internal Key:** Set via `FASTAPI_INTERNAL_KEY` environment variable
- **Odoo Internal Key:** Must match FastAPI's `INTERNAL_API_KEY` setting

