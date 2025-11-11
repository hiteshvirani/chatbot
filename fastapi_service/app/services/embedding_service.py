import asyncio
import logging
from typing import List
from sentence_transformers import SentenceTransformer
from app.config import settings

_logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.model = None
        self._lock = asyncio.Lock()

    async def _load_model(self):
        """Load the embedding model (thread-safe)"""
        async with self._lock:
            if self.model is None:
                try:
                    # Load model in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    self.model = await loop.run_in_executor(
                        None, 
                        SentenceTransformer, 
                        settings.embedding_model
                    )
                    _logger.info(f"Loaded embedding model: {settings.embedding_model}")
                except Exception as e:
                    _logger.error(f"Failed to load embedding model: {str(e)}")
                    raise

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        if not texts:
            return []

        # Ensure model is loaded
        if self.model is None:
            await self._load_model()

        try:
            # Generate embeddings in thread pool
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                self.model.encode,
                texts
            )
            
            # Convert to list of lists
            return [embedding.tolist() for embedding in embeddings]
            
        except Exception as e:
            _logger.error(f"Error generating embeddings: {str(e)}")
            raise

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else []

    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """Split text into chunks"""
        chunk_size = chunk_size or settings.chunk_size
        overlap = overlap or settings.chunk_overlap
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start + chunk_size // 2, end - 100), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks


# Global instance
embedding_service = EmbeddingService()
