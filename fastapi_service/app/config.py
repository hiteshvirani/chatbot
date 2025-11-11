from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://chatbot_user:password@db:5432/chatbot_db"
    
    # Odoo Integration
    odoo_url: str = "http://odoo:8069"
    odoo_api_key: Optional[str] = None
    
    # Internal API
    internal_api_key: str = "change_me_internal_api_key"
    
    # Ollama
    ollama_base_url: str = "http://ollama:11434"
    
    # Embedding Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    rate_limit_per_hour: int = 1000
    
    # CORS
    allowed_origins: list = ["*"]
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()
