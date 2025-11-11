from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    api_key: Optional[str] = Field(None, description="API key (alternative to header)")


class Source(BaseModel):
    type: str = Field(..., description="Source type: document or link")
    id: int = Field(..., description="Source ID")
    name: Optional[str] = Field(None, description="Document name or link title")
    url: Optional[str] = Field(None, description="URL for links")
    relevance_score: float = Field(..., description="Relevance score")


class ChatResponse(BaseModel):
    response: str = Field(..., description="Chatbot response")
    sources: List[Source] = Field(default_factory=list, description="Sources used")
    session_id: str = Field(..., description="Session ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")


class DocumentEmbedRequest(BaseModel):
    chatbot_id: int = Field(..., description="Chatbot ID")
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class LinkEmbedRequest(BaseModel):
    chatbot_id: int = Field(..., description="Chatbot ID")
    url: str = Field(..., description="Link URL")
    content: str = Field(..., description="Scraped content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Link metadata")


class EmbedResponse(BaseModel):
    status: str = Field(..., description="Status: success or error")
    embeddings_count: int = Field(..., description="Number of embeddings created")
    chunks_created: int = Field(..., description="Number of chunks created")
    message: str = Field(..., description="Response message")


class DeleteResponse(BaseModel):
    status: str = Field(..., description="Status: success or error")
    deleted_count: int = Field(..., description="Number of embeddings deleted")
    message: str = Field(..., description="Response message")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status")
    chatbot_id: Optional[int] = Field(None, description="Chatbot ID")
    chatbot_status: Optional[str] = Field(None, description="Chatbot status")
    embeddings_count: Optional[int] = Field(None, description="Number of embeddings")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class ErrorResponse(BaseModel):
    status: str = Field(default="error", description="Status")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")
    code: Optional[str] = Field(None, description="Error code")
