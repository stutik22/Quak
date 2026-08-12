"""
Configuration settings for the QWAK Recipe Recommender API.
"""
import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    app_name: str = "QWAK Recipe Recommender"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Model Configuration
    model_path: str = "models/"
    tfidf_weight: float = 0.4
    embedding_weight: float = 0.6
    max_recommendations: int = 50
    
    # Performance Configuration
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour
    enable_redis_cache: bool = True
    redis_url: Optional[str] = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Model Loading Configuration
    preload_models: bool = True
    model_cache_size: int = 100  # MB
    
    # API Limits
    max_ingredients: int = 20
    request_timeout: int = 30
    max_concurrent_requests: int = 100
    
    class Config:
        env_file = ".env"
        env_prefix = "QWAK_"


# Global settings instance
settings = Settings()