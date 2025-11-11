import uuid
import json
import logging
import httpx
from typing import List, Dict, Any, Optional
from app.config import settings
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.database.connection import execute_query

_logger = logging.getLogger(__name__)


class RAGService:
    
    def __init__(self):
        self.ollama_client = httpx.AsyncClient(timeout=120.0)

    async def generate_response(
        self,
        chatbot_id: int,
        message: str,
        chatbot_info: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate response using RAG pipeline"""
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())

            # Step 1: Generate query embedding
            query_embedding = await embedding_service.generate_embedding(message)
            
            # Step 2: Search for relevant documents
            similar_docs = await vector_store.similarity_search(
                chatbot_id=chatbot_id,
                query_embedding=query_embedding,
                limit=5,
                threshold=0.3
            )
            
            # Step 3: Prepare context from retrieved documents
            context = self._prepare_context(similar_docs)
            
            # Step 4: Get system prompts
            system_prompts = [
                prompt['text'] for prompt in chatbot_info.get('prompts', [])
                if prompt['type'] == 'system'
            ]
            
            # Step 5: Generate response (simple version without Ollama for now)
            response_text = await self._generate_simple_response(
                message=message,
                context=context,
                system_prompts=system_prompts
            )
            
            # Step 6: Prepare sources
            sources = await self._prepare_sources(chatbot_id, similar_docs)
            
            # Step 7: Save conversation (optional)
            await self._save_conversation(chatbot_id, session_id, message, response_text)
            
            return {
                'response': response_text,
                'sources': sources,
                'session_id': session_id,
                'metadata': {
                    'model': 'simple',
                    'tokens_used': len(response_text.split()),
                    'response_time_ms': 0,
                    'context_chunks': len(similar_docs)
                }
            }
            
        except Exception as e:
            _logger.error(f"Error generating response: {str(e)}")
            return {
                'response': "I'm sorry, I encountered an error while processing your request.",
                'sources': [],
                'session_id': session_id or str(uuid.uuid4()),
                'metadata': {'error': str(e)}
            }

    def _prepare_context(self, similar_docs: List[Dict[str, Any]]) -> str:
        """Prepare context from similar documents"""
        if not similar_docs:
            return "No relevant information found."
        
        context_parts = []
        for doc in similar_docs:
            content = doc['content']
            metadata = doc['metadata']
            source_info = f"Source: {metadata.get('filename', 'Unknown')}"
            context_parts.append(f"{source_info}\n{content}")
        
        return "\n\n---\n\n".join(context_parts)

    async def _generate_simple_response(
        self,
        message: str,
        context: str,
        system_prompts: List[str]
    ) -> str:
        """Generate simple response (without Ollama for now)"""
        # For now, return a simple response based on context
        if "No relevant information found" in context:
            return "I don't have specific information about that in my knowledge base. Could you please provide more details or ask about something else?"
        
        # Simple response based on context
        return f"Based on the information I have, here's what I can tell you: {context[:500]}..."

    async def _prepare_sources(self, chatbot_id: int, similar_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare sources from similar documents"""
        sources = []
        
        for doc in similar_docs:
            source = {
                'type': doc['source_type'],
                'id': doc['source_id'],
                'relevance_score': doc['similarity']
            }
            
            metadata = doc['metadata']
            if doc['source_type'] == 'document':
                source['name'] = metadata.get('filename', f"Document {doc['source_id']}")
            elif doc['source_type'] == 'link':
                source['name'] = metadata.get('title', f"Link {doc['source_id']}")
                source['url'] = metadata.get('url', '')
            
            sources.append(source)
        
        return sources

    async def _save_conversation(self, chatbot_id: int, session_id: str, message: str, response: str):
        """Save conversation to database"""
        try:
            # Check if session exists
            query = "SELECT conversation_history FROM chatbot_sessions WHERE chatbot_id = $1 AND session_id = $2"
            result = await execute_query(query, chatbot_id, session_id, fetch_one=True)
            
            # Prepare conversation entry
            conversation_entry = {
                'timestamp': str(uuid.uuid4()),  # Simple timestamp
                'user_message': message,
                'bot_response': response
            }
            
            if result:
                # Update existing session
                history = json.loads(result['conversation_history']) if result['conversation_history'] else []
                history.append(conversation_entry)
                
                update_query = """
                    UPDATE chatbot_sessions 
                    SET conversation_history = $1, last_activity = NOW()
                    WHERE chatbot_id = $2 AND session_id = $3
                """
                await execute_query(update_query, json.dumps(history), chatbot_id, session_id)
            else:
                # Create new session
                insert_query = """
                    INSERT INTO chatbot_sessions (chatbot_id, session_id, conversation_history)
                    VALUES ($1, $2, $3)
                """
                await execute_query(insert_query, chatbot_id, session_id, json.dumps([conversation_entry]))
                
        except Exception as e:
            _logger.error(f"Error saving conversation: {str(e)}")

    async def close(self):
        """Close HTTP client"""
        await self.ollama_client.aclose()


# Global instance
rag_service = RAGService()
