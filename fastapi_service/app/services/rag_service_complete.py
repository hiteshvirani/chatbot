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
            
            # Step 5: Generate response with Ollama
            response_text = await self._generate_with_ollama(
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
                    'model': 'llama2',
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
            system_prompt = "\n".join(system_prompts) if system_prompts else (
                "You are a helpful assistant. Use the provided context to answer questions accurately. "
                "If the context doesn't contain relevant information, say so politely."
            )
            
            # Prepare full prompt
            full_prompt = f"""System: {system_prompt}

Context:
{context}

User: {message}
