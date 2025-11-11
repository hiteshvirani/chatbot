import logging
from fastapi import APIRouter, HTTPException, Header, Depends

from app.models.schemas import (
    DocumentEmbedRequest, LinkEmbedRequest, EmbedResponse, DeleteResponse, ErrorResponse
)
from app.services.auth_service import auth_service
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store

_logger = logging.getLogger(__name__)

router = APIRouter()


async def validate_internal_api_key(x_odoo_api_key: str = Header(..., alias="X-Odoo-API-Key")):
    """Validate internal API key for Odoo → FastAPI communication"""
    if not auth_service.validate_internal_api_key(x_odoo_api_key):
        raise HTTPException(status_code=401, detail="Invalid internal API key")
    return True


@router.post("/document/{document_id}/embed", response_model=EmbedResponse)
async def embed_document(
    document_id: int,
    request: DocumentEmbedRequest,
    _: bool = Depends(validate_internal_api_key)
):
    """Process and embed a document into pgvector"""
    try:
        if not request.content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        # Step 1: Chunk the document content
        chunks = embedding_service.chunk_text(request.content)
        
        # Step 2: Generate embeddings for all chunks
        embeddings = await embedding_service.generate_embeddings(chunks)
        
        # Step 3: Delete existing embeddings for this document (if updating)
        deleted_count = await vector_store.delete_by_source(
            chatbot_id=request.chatbot_id,
            source_type='document',
            source_id=document_id
        )
        
        # Step 4: Store new embeddings
        success_count = 0
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            success = await vector_store.insert_embedding(
                chatbot_id=request.chatbot_id,
                source_type='document',
                source_id=document_id,
                content=chunk,
                embedding=embedding,
                chunk_index=idx,
                metadata=request.metadata
            )
            if success:
                success_count += 1
        
        if success_count == 0:
            raise HTTPException(status_code=500, detail="Failed to store embeddings")
        
        _logger.info(f"Successfully embedded document {document_id}: {success_count} chunks")
        
        return EmbedResponse(
            status="success",
            embeddings_count=success_count,
            chunks_created=len(chunks),
            message="Document embedded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Error embedding document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/link/{link_id}/embed", response_model=EmbedResponse)
async def embed_link(
    link_id: int,
    request: LinkEmbedRequest,
    _: bool = Depends(validate_internal_api_key)
):
    """Process and embed a link's content into pgvector"""
    try:
        if not request.content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        # Step 1: Chunk the link content
        chunks = embedding_service.chunk_text(request.content)
        
        # Step 2: Generate embeddings for all chunks
        embeddings = await embedding_service.generate_embeddings(chunks)
        
        # Step 3: Delete existing embeddings for this link (if updating)
        deleted_count = await vector_store.delete_by_source(
            chatbot_id=request.chatbot_id,
            source_type='link',
            source_id=link_id
        )
        
        # Step 4: Store new embeddings
        success_count = 0
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            success = await vector_store.insert_embedding(
                chatbot_id=request.chatbot_id,
                source_type='link',
                source_id=link_id,
                content=chunk,
                embedding=embedding,
                chunk_index=idx,
                metadata=request.metadata
            )
            if success:
                success_count += 1
        
        if success_count == 0:
            raise HTTPException(status_code=500, detail="Failed to store embeddings")
        
        _logger.info(f"Successfully embedded link {link_id}: {success_count} chunks")
        
        return EmbedResponse(
            status="success",
            embeddings_count=success_count,
            chunks_created=len(chunks),
            message="Link embedded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Error embedding link {link_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.delete("/chatbot/{chatbot_id}/source/{source_type}/{source_id}", response_model=DeleteResponse)
async def delete_source_embeddings(
    chatbot_id: int,
    source_type: str,
    source_id: int,
    _: bool = Depends(validate_internal_api_key)
):
    """Delete embeddings for a specific source from pgvector"""
    try:
        if source_type not in ['document', 'link']:
            raise HTTPException(status_code=400, detail="Invalid source_type. Must be 'document' or 'link'")
        
        # Delete embeddings
        deleted_count = await vector_store.delete_by_source(
            chatbot_id=chatbot_id,
            source_type=source_type,
            source_id=source_id
        )
        
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="No embeddings found for the specified source")
        
        _logger.info(f"Deleted {deleted_count} embeddings for {source_type} {source_id}")
        
        return DeleteResponse(
            status="success",
            deleted_count=deleted_count,
            message="Embeddings deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Error deleting embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.delete("/chatbot/{chatbot_id}/cleanup", response_model=DeleteResponse)
async def cleanup_chatbot(
    chatbot_id: int,
    _: bool = Depends(validate_internal_api_key)
):
    """Delete all embeddings and sessions for a chatbot (used when chatbot is deleted)"""
    try:
        # Delete all embeddings for the chatbot
        embeddings_deleted = await vector_store.delete_by_chatbot(chatbot_id)
        
        # Delete all sessions for the chatbot
        sessions_deleted = 0
        try:
            query = "DELETE FROM chatbot_sessions WHERE chatbot_id = $1"
            from app.database.connection import execute_query
            result = await execute_query(query, chatbot_id)
            if isinstance(result, str) and result.startswith("DELETE"):
                sessions_deleted = int(result.split()[1]) if len(result.split()) > 1 else 0
        except Exception as e:
            _logger.warning(f"Error deleting sessions for chatbot {chatbot_id}: {str(e)}")
        
        _logger.info(f"Cleaned up chatbot {chatbot_id}: {embeddings_deleted} embeddings, {sessions_deleted} sessions")
        
        return DeleteResponse(
            status="success",
            deleted_count=embeddings_deleted + sessions_deleted,
            message=f"Chatbot data cleaned up: {embeddings_deleted} embeddings, {sessions_deleted} sessions deleted"
        )
        
    except Exception as e:
        _logger.error(f"Error cleaning up chatbot {chatbot_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/chatbot/{chatbot_id}/sync")
async def sync_chatbot(
    chatbot_id: int,
    _: bool = Depends(validate_internal_api_key)
):
    """Full synchronization of chatbot data (placeholder for future implementation)"""
    try:
        # This endpoint can be used for full sync operations
        # For now, just return success
        return {
            "status": "success",
            "chatbot_id": chatbot_id,
            "message": "Sync endpoint ready (not implemented yet)"
        }
        
    except Exception as e:
        _logger.error(f"Error syncing chatbot {chatbot_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
