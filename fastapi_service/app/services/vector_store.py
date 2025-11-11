import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from app.database.connection import execute_query

_logger = logging.getLogger(__name__)


class VectorStore:
    
    async def insert_embedding(
        self,
        chatbot_id: int,
        source_type: str,
        source_id: int,
        content: str,
        embedding: List[float],
        chunk_index: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Insert an embedding into the vector store"""
        try:
            query = """
                INSERT INTO chatbot_embeddings 
                (chatbot_id, source_type, source_id, content, content_chunk_index, embedding, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """
            
            await execute_query(
                query,
                chatbot_id,
                source_type,
                source_id,
                content,
                chunk_index,
                embedding,
                json.dumps(metadata or {})
            )
            
            return True
            
        except Exception as e:
            _logger.error(f"Error inserting embedding: {str(e)}")
            return False

    async def delete_by_source(
        self,
        chatbot_id: int,
        source_type: str,
        source_id: int
    ) -> int:
        """Delete all embeddings for a specific source"""
        try:
            query = """
                DELETE FROM chatbot_embeddings 
                WHERE chatbot_id = $1 AND source_type = $2 AND source_id = $3
            """
            
            result = await execute_query(query, chatbot_id, source_type, source_id)
            
            # Extract count from result string like "DELETE 5"
            if isinstance(result, str) and result.startswith("DELETE"):
                count = int(result.split()[1]) if len(result.split()) > 1 else 0
                return count
            
            return 0
            
        except Exception as e:
            _logger.error(f"Error deleting embeddings: {str(e)}")
            return 0

    async def delete_by_chatbot(self, chatbot_id: int) -> int:
        """Delete all embeddings for a chatbot"""
        try:
            query = "DELETE FROM chatbot_embeddings WHERE chatbot_id = $1"
            result = await execute_query(query, chatbot_id)
            
            if isinstance(result, str) and result.startswith("DELETE"):
                count = int(result.split()[1]) if len(result.split()) > 1 else 0
                return count
            
            return 0
            
        except Exception as e:
            _logger.error(f"Error deleting chatbot embeddings: {str(e)}")
            return 0

    async def similarity_search(
        self,
        chatbot_id: int,
        query_embedding: List[float],
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar embeddings"""
        try:
            query = """
                SELECT 
                    id,
                    chatbot_id,
                    source_type,
                    source_id,
                    content,
                    content_chunk_index,
                    metadata,
                    1 - (embedding <=> $2) as similarity
                FROM chatbot_embeddings 
                WHERE chatbot_id = $1 
                    AND 1 - (embedding <=> $2) > $3
                ORDER BY embedding <=> $2
                LIMIT $4
            """
            
            results = await execute_query(
                query,
                chatbot_id,
                query_embedding,
                threshold,
                limit,
                fetch_all=True
            )
            
            return [
                {
                    'id': row['id'],
                    'chatbot_id': row['chatbot_id'],
                    'source_type': row['source_type'],
                    'source_id': row['source_id'],
                    'content': row['content'],
                    'chunk_index': row['content_chunk_index'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'similarity': float(row['similarity'])
                }
                for row in results
            ]
            
        except Exception as e:
            _logger.error(f"Error in similarity search: {str(e)}")
            return []

    async def get_embeddings_count(self, chatbot_id: int) -> int:
        """Get count of embeddings for a chatbot"""
        try:
            query = "SELECT COUNT(*) as count FROM chatbot_embeddings WHERE chatbot_id = $1"
            result = await execute_query(query, chatbot_id, fetch_one=True)
            return result['count'] if result else 0
            
        except Exception as e:
            _logger.error(f"Error getting embeddings count: {str(e)}")
            return 0

    async def get_sources_info(self, chatbot_id: int, source_ids: List[Tuple[str, int]]) -> Dict[str, Dict]:
        """Get source information for given source IDs"""
        try:
            # This would typically query Odoo or a local cache
            # For now, return basic info from metadata
            sources_info = {}
            
            for source_type, source_id in source_ids:
                query = """
                    SELECT DISTINCT source_type, source_id, metadata
                    FROM chatbot_embeddings 
                    WHERE chatbot_id = $1 AND source_type = $2 AND source_id = $3
                    LIMIT 1
                """
                
                result = await execute_query(query, chatbot_id, source_type, source_id, fetch_one=True)
                
                if result:
                    metadata = json.loads(result['metadata']) if result['metadata'] else {}
                    key = f"{source_type}_{source_id}"
                    sources_info[key] = {
                        'type': source_type,
                        'id': source_id,
                        'name': metadata.get('filename') or metadata.get('title', f"{source_type}_{source_id}"),
                        'url': metadata.get('url') if source_type == 'link' else None
                    }
            
            return sources_info
            
        except Exception as e:
            _logger.error(f"Error getting sources info: {str(e)}")
            return {}


# Global instance
vector_store = VectorStore()
