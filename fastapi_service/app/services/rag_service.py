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
        # Increased timeout for Ollama - it can take time to generate responses
        self.ollama_client = httpx.AsyncClient(
            timeout=httpx.Timeout(300.0, connect=30.0),  # 5 minutes total, 30s connect
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

    async def generate_response(
        self,
        chatbot_id: int,
        message: str,
        chatbot_info: Dict[str, Any],
        session_id: Optional[str] = None,
        user_prompts: Optional[List[Dict[str, Any]]] = None
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
                threshold=0.1  # Lower threshold to find more matches
            )
            
            # Step 3: Prepare context from retrieved documents
            context = self._prepare_context(similar_docs)
            
            # Step 4: Prepare system prompts
            # Priority: master_system_prompt (from FastAPI config) > user_prompts > chatbot_info prompts
            system_prompts_list = []
            
            # Add master system prompt from FastAPI config first (highest priority, cannot be ignored)
            master_prompt = settings.master_system_prompt
            if master_prompt:
                system_prompts_list.append(f"[MASTER PROMPT - DO NOT IGNORE]\n{master_prompt}")
            
            # Add user-level prompts from request
            if user_prompts:
                for prompt in sorted(user_prompts, key=lambda x: x.get('order', 999)):
                    if prompt.get('type') == 'system' and prompt.get('text'):
                        system_prompts_list.append(prompt['text'])
            
            # Fallback: Get prompts from chatbot_info (for backward compatibility)
            if not system_prompts_list:
                system_prompts_list = [
                    prompt['text'] for prompt in chatbot_info.get('prompts', [])
                    if prompt['type'] == 'system'
                ]
            
            # Step 5: Generate response with Ollama
            response_text = await self._generate_with_ollama(
                message=message,
                context=context,
                system_prompts=system_prompts_list
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
                    'model': settings.ollama_model,
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

    async def _generate_with_ollama(
        self,
        message: str,
        context: str,
        system_prompts: List[str]
    ) -> str:
        """Generate response using Ollama"""
        try:
            # Prepare system prompt
            # Combine all system prompts with clear separation
            if system_prompts:
                # Master prompt is first, then user prompts
                system_prompt = "\n\n---\n\n".join(system_prompts)
            else:
                # Fallback default
                system_prompt = (
                    "You are a helpful assistant. Use the provided context to answer questions accurately. "
                    "If the context doesn't contain relevant information, say so politely."
                )
            
            # Prepare full prompt with context
            if "No relevant information found" in context:
                user_prompt = f"{message}\n\nNote: I don't have specific information about this in my knowledge base."
            else:
                user_prompt = f"""Based on the following context, please answer the question:

Context:
{context}

Question: {message}

Please provide a helpful and accurate answer based on the context provided. If the context doesn't fully answer the question, mention that."""
            
            # Call Ollama API
            response = await self.ollama_client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": user_prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 500
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "I'm sorry, I couldn't generate a response.")
            else:
                _logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                # Fallback response
                if "No relevant information found" in context:
                    return "I don't have specific information about that in my knowledge base. Could you please provide more details or ask about something else?"
                return f"Based on the information I have: {context[:300]}..."
                
        except Exception as e:
            import traceback
            _logger.error(f"Error generating response with Ollama: {str(e)}")
            _logger.error(f"Traceback: {traceback.format_exc()}")
            # Fallback response
            if "No relevant information found" in context:
                return "I don't have specific information about that in my knowledge base. Could you please provide more details or ask about something else?"
            return f"Based on the information I have: {context[:300]}..."

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
