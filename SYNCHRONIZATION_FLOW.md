# Synchronization Flow Documentation

## Overview
This document details the automatic synchronization mechanism between Odoo and pgvector (via FastAPI) for chatbot documents and links.

## Architecture

```
┌─────────────────┐                    ┌─────────────────┐
│   Odoo Service  │                    │  FastAPI Service│
│                 │                    │                 │
│  User Action    │                    │                 │
│  (Create/Update/│                    │                 │
│   Delete)       │                    │                 │
│        │        │                    │                 │
│        │ HTTP   │                    │                 │
│        ├───────►│                    │                 │
│        │ POST   │                    │                 │
│        │        │                    │                 │
│        │        │                    │  Process &      │
│        │        │                    │  Generate       │
│        │        │                    │  Embeddings     │
│        │        │                    │        │        │
│        │        │                    │        │        │
│        │        │                    │        ▼        │
│        │        │                    │  ┌──────────┐   │
│        │        │                    │  │ pgvector │   │
│        │        │                    │  │ Database │   │
│        │        │                    │  └──────────┘   │
│        │        │                    │                 │
│        │ Status │                    │                 │
│        │◄───────┤                    │                 │
│        │ Update │                    │                 │
└────────┴────────┘                    └─────────────────┘
```

## Synchronization Triggers

### 1. Document Created

#### Flow
```
User uploads document in Odoo
    ↓
Odoo: chatbot.document.create()
    ↓
Odoo: Extract text content (PyPDF2, python-docx, etc.)
    ↓
Odoo: Set vector_sync_status = 'pending'
    ↓
Odoo: HTTP POST to FastAPI /api/internal/document/{id}/embed
    ↓
FastAPI: Receive request
    ↓
FastAPI: Validate internal API key
    ↓
FastAPI: Chunk document content (if large)
    ↓
FastAPI: Generate embeddings for each chunk
    ↓
FastAPI: Store embeddings in pgvector
    ↓
FastAPI: Return success response
    ↓
Odoo: Update document.vector_sync_status = 'synced'
    ↓
Odoo: Set document.processed = True
```

#### Odoo Implementation
```python
@api.model
def create(self, vals):
    # Create document record
    document = super().create(vals)
    
    # Extract text content
    content = self._extract_text(document.file_path)
    document.write({'content': content})
    
    # Trigger sync to FastAPI
    document.sync_to_fastapi()
    
    return document

def sync_to_fastapi(self):
    """Send document to FastAPI for embedding"""
    fastapi_url = self.env['ir.config_parameter'].get_param('fastapi.url')
    internal_key = self.env['ir.config_parameter'].get_param('fastapi.internal_key')
    
    payload = {
        'chatbot_id': self.chatbot_id.id,
        'content': self.content,
        'metadata': {
            'filename': self.name,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat()
        }
    }
    
    response = requests.post(
        f"{fastapi_url}/api/internal/document/{self.id}/embed",
        json=payload,
        headers={'X-Odoo-API-Key': internal_key},
        timeout=300  # 5 minutes for large documents
    )
    
    if response.status_code == 200:
        self.write({
            'vector_sync_status': 'synced',
            'processed': True
        })
    else:
        self.write({'vector_sync_status': 'error'})
        raise UserError(f"Failed to sync document: {response.text}")
```

#### FastAPI Implementation
```python
@router.post("/api/internal/document/{document_id}/embed")
async def embed_document(
    document_id: int,
    request: DocumentEmbedRequest,
    api_key: str = Header(..., alias="X-Odoo-API-Key")
):
    # Validate internal API key
    if not validate_internal_api_key(api_key):
        raise HTTPException(401, "Invalid internal API key")
    
    # Chunk document content
    chunks = chunk_text(request.content, chunk_size=1000, overlap=200)
    
    # Generate embeddings
    embeddings = await embedding_service.generate_embeddings(chunks)
    
    # Delete existing embeddings for this document (if updating)
    await vector_store.delete_by_source(
        chatbot_id=request.chatbot_id,
        source_type='document',
        source_id=document_id
    )
    
    # Store embeddings
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        await vector_store.insert_embedding(
            chatbot_id=request.chatbot_id,
            source_type='document',
            source_id=document_id,
            content=chunk,
            embedding=embedding,
            chunk_index=idx,
            metadata=request.metadata
        )
    
    return {
        "status": "success",
        "document_id": document_id,
        "embeddings_count": len(embeddings),
        "chunks_created": len(chunks)
    }
```

---

### 2. Document Updated

#### Flow
```
User updates document in Odoo
    ↓
Odoo: chatbot.document.write()
    ↓
Odoo: Check if file_path or content changed
    ↓
If changed:
    ↓
    Odoo: Re-extract text content
    ↓
    Odoo: Set vector_sync_status = 'pending'
    ↓
    Odoo: HTTP POST to FastAPI /api/internal/document/{id}/embed
    ↓
    FastAPI: DELETE all embeddings for document_id
    ↓
    FastAPI: Re-process document
    ↓
    FastAPI: Generate new embeddings
    ↓
    FastAPI: INSERT new embeddings
    ↓
    FastAPI: Return success
    ↓
    Odoo: Update vector_sync_status = 'synced'
```

#### Odoo Implementation
```python
def write(self, vals):
    # Check if file or content changed
    file_changed = 'file_path' in vals or 'content' in vals
    
    result = super().write(vals)
    
    if file_changed:
        # Re-extract content if file changed
        if 'file_path' in vals:
            content = self._extract_text(self.file_path)
            self.write({'content': content})
        
        # Re-sync to FastAPI
        self.sync_to_fastapi()
    
    return result
```

#### FastAPI Implementation
```python
# Same endpoint as create, but FastAPI handles deletion first
@router.post("/api/internal/document/{document_id}/embed")
async def embed_document(...):
    # ... validation ...
    
    # IMPORTANT: Delete existing embeddings first
    deleted_count = await vector_store.delete_by_source(
        chatbot_id=request.chatbot_id,
        source_type='document',
        source_id=document_id
    )
    
    # Then process and insert new embeddings
    # ... (same as create flow)
```

---

### 3. Document Deleted

#### Flow
```
User deletes document in Odoo
    ↓
Odoo: chatbot.document.unlink()
    ↓
Odoo: Check if document.processed = True
    ↓
If processed:
    ↓
    Odoo: HTTP DELETE to FastAPI /api/internal/chatbot/{chatbot_id}/source/document/{document_id}
    ↓
    FastAPI: DELETE all embeddings where source_type='document' AND source_id={document_id}
    ↓
    FastAPI: Return deleted_count
    ↓
Odoo: Continue with deletion
```

#### Odoo Implementation
```python
def unlink(self):
    """Override to delete from pgvector before Odoo deletion"""
    for record in self:
        if record.processed:
            # Delete from pgvector
            fastapi_url = self.env['ir.config_parameter'].get_param('fastapi.url')
            internal_key = self.env['ir.config_parameter'].get_param('fastapi.internal_key')
            
            try:
                response = requests.delete(
                    f"{fastapi_url}/api/internal/chatbot/{record.chatbot_id.id}/source/document/{record.id}",
                    headers={'X-Odoo-API-Key': internal_key},
                    timeout=30
                )
                
                if response.status_code != 200:
                    # Log error but don't block deletion
                    _logger.error(f"Failed to delete embeddings: {response.text}")
            except Exception as e:
                # Log error but don't block deletion
                _logger.error(f"Error deleting embeddings: {str(e)}")
    
    # Proceed with Odoo deletion
    return super().unlink()
```

#### FastAPI Implementation
```python
@router.delete("/api/internal/chatbot/{chatbot_id}/source/{source_type}/{source_id}")
async def delete_source_embeddings(
    chatbot_id: int,
    source_type: str,
    source_id: int,
    api_key: str = Header(..., alias="X-Odoo-API-Key")
):
    # Validate
    if not validate_internal_api_key(api_key):
        raise HTTPException(401, "Invalid internal API key")
    
    if source_type not in ['document', 'link']:
        raise HTTPException(400, "Invalid source_type")
    
    # Delete embeddings
    deleted_count = await vector_store.delete_by_source(
        chatbot_id=chatbot_id,
        source_type=source_type,
        source_id=source_id
    )
    
    if deleted_count == 0:
        raise HTTPException(404, "No embeddings found")
    
    return {
        "status": "success",
        "chatbot_id": chatbot_id,
        "source_type": source_type,
        "source_id": source_id,
        "deleted_count": deleted_count
    }
```

---

### 4. Link Created/Updated/Deleted

Same flow as documents, but with `source_type='link'`

#### Link-Specific Considerations
- **Created**: Scrape content → Embed
- **Updated**: Re-scrape → Delete old embeddings → Insert new
- **Deleted**: Delete embeddings

#### Odoo Link Model
```python
def sync_to_fastapi(self):
    """Send link to FastAPI for embedding"""
    # Scrape content if not already done
    if not self.content:
        self.content = self._scrape_content(self.url)
    
    fastapi_url = self.env['ir.config_parameter'].get_param('fastapi.url')
    internal_key = self.env['ir.config_parameter'].get_param('fastapi.internal_key')
    
    payload = {
        'chatbot_id': self.chatbot_id.id,
        'url': self.url,
        'content': self.content,
        'metadata': {
            'title': self.title,
            'scraped_at': self.created_at.isoformat()
        }
    }
    
    response = requests.post(
        f"{fastapi_url}/api/internal/link/{self.id}/embed",
        json=payload,
        headers={'X-Odoo-API-Key': internal_key},
        timeout=300
    )
    
    if response.status_code == 200:
        self.write({
            'vector_sync_status': 'synced',
            'processed': True
        })
    else:
        self.write({'vector_sync_status': 'error'})
```

---

### 5. Chatbot Deleted

#### Flow
```
User deletes chatbot in Odoo
    ↓
Odoo: chatbot.chatbot.unlink()
    ↓
Odoo: HTTP DELETE to FastAPI /api/internal/chatbot/{chatbot_id}/cleanup
    ↓
FastAPI: DELETE all embeddings for chatbot_id
    ↓
FastAPI: DELETE all sessions for chatbot_id
    ↓
FastAPI: Return success
    ↓
Odoo: Continue with deletion
```

#### Odoo Implementation
```python
def unlink(self):
    """Override to cleanup pgvector data"""
    for chatbot in self:
        fastapi_url = self.env['ir.config_parameter'].get_param('fastapi.url')
        internal_key = self.env['ir.config_parameter'].get_param('fastapi.internal_key')
        
        try:
            response = requests.delete(
                f"{fastapi_url}/api/internal/chatbot/{chatbot.id}/cleanup",
                headers={'X-Odoo-API-Key': internal_key},
                timeout=60
            )
            
            if response.status_code != 200:
                _logger.error(f"Failed to cleanup chatbot: {response.text}")
        except Exception as e:
            _logger.error(f"Error cleaning up chatbot: {str(e)}")
    
    return super().unlink()
```

#### FastAPI Implementation
```python
@router.delete("/api/internal/chatbot/{chatbot_id}/cleanup")
async def cleanup_chatbot(
    chatbot_id: int,
    api_key: str = Header(..., alias="X-Odoo-API-Key")
):
    # Validate
    if not validate_internal_api_key(api_key):
        raise HTTPException(401, "Invalid internal API key")
    
    # Delete all embeddings
    embeddings_deleted = await vector_store.delete_by_chatbot(chatbot_id)
    
    # Delete all sessions
    sessions_deleted = await session_store.delete_by_chatbot(chatbot_id)
    
    return {
        "status": "success",
        "chatbot_id": chatbot_id,
        "embeddings_deleted": embeddings_deleted,
        "sessions_deleted": sessions_deleted
    }
```

---

## Error Handling

### Retry Logic
```python
def sync_to_fastapi_with_retry(self, max_retries=3):
    """Sync with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            self.sync_to_fastapi()
            return True
        except Exception as e:
            if attempt == max_retries - 1:
                # Last attempt failed
                self.write({'vector_sync_status': 'error'})
                raise
            else:
                # Wait before retry (exponential backoff)
                import time
                wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                time.sleep(wait_time)
                _logger.warning(f"Sync failed, retrying in {wait_time}s: {str(e)}")
    
    return False
```

### Status Tracking
- `pending`: Sync initiated but not completed
- `synced`: Successfully synced to pgvector
- `error`: Sync failed (user can retry manually)

### Manual Retry
Users can manually trigger sync from Odoo UI:
```python
def action_retry_sync(self):
    """Manual retry sync action"""
    self.write({'vector_sync_status': 'pending'})
    self.sync_to_fastapi()
```

---

## Batch Operations

### Bulk Sync
For initial setup or bulk updates:
```python
@api.model
def action_bulk_sync_all(self):
    """Sync all pending documents and links"""
    documents = self.search([('vector_sync_status', 'in', ['pending', 'error'])])
    links = self.env['chatbot.link'].search([('vector_sync_status', 'in', ['pending', 'error'])])
    
    for doc in documents:
        try:
            doc.sync_to_fastapi()
        except Exception as e:
            _logger.error(f"Failed to sync document {doc.id}: {str(e)}")
    
    for link in links:
        try:
            link.sync_to_fastapi()
        except Exception as e:
            _logger.error(f"Failed to sync link {link.id}: {str(e)}")
```

---

## Performance Considerations

### Async Processing
For large documents, consider async processing:
```python
# Odoo: Trigger async task
self.env['queue.job'].enqueue(
    self.sync_to_fastapi,
    description=f"Sync document {self.id}"
)
```

### Chunking Strategy
- **Chunk Size**: 1000 characters
- **Overlap**: 200 characters
- **Max Chunks per Document**: 100 (to prevent excessive embeddings)

### Batch Embedding
FastAPI can process multiple chunks in parallel:
```python
# Generate embeddings in batches
batch_size = 10
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i+batch_size]
    embeddings_batch = await embedding_service.generate_embeddings_batch(batch)
    # Store batch
```

---

## Monitoring and Logging

### Logging Points
1. Sync initiation
2. FastAPI request/response
3. Embedding generation
4. Vector store operations
5. Errors and retries

### Metrics to Track
- Sync success rate
- Average sync time
- Embedding generation time
- Vector store operation time
- Error rates by type

---

## Testing

### Unit Tests
- Test document create/update/delete triggers
- Test link create/update/delete triggers
- Test error handling and retries

### Integration Tests
- Test Odoo → FastAPI communication
- Test FastAPI → pgvector operations
- Test end-to-end sync flow

### Load Tests
- Test concurrent sync operations
- Test large document processing
- Test bulk operations

---

## Troubleshooting

### Common Issues

1. **Sync Status Stuck on 'pending'**
   - Check FastAPI logs
   - Verify network connectivity
   - Check internal API key

2. **Embeddings Not Found After Sync**
   - Verify pgvector connection
   - Check embedding generation
   - Verify chatbot_id matching

3. **Slow Sync Performance**
   - Check document size
   - Optimize chunking
   - Consider async processing

4. **Deletion Not Working**
   - Verify FastAPI endpoint
   - Check source_id matching
   - Review error logs

---

**Last Updated**: 2024-01-15  
**Version**: 1.0.0

