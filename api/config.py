"""
Configuration for CheckjeBon API
===============================
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_key: str = Field(..., env="SUPABASE_KEY")
    
    # Redis Cache
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    redis_db: int = Field(0, env="REDIS_DB")
    
    # API Configuration
    api_title: str = Field("CheckjeBon API", env="API_TITLE")
    api_version: str = Field("1.0.0", env="API_VERSION")
    api_description: str = Field("API for Dutch supermarket price comparison data", env="API_DESCRIPTION")
    
    # Security
    secret_key: str = Field("your-secret-key-here", env="SECRET_KEY")
    api_key_header: str = Field("X-API-Key", env="API_KEY_HEADER")
    allowed_origins: list = Field(["*"], env="ALLOWED_ORIGINS")
    
    # Rate Limiting
    rate_limit_default: str = Field("100/minute", env="RATE_LIMIT_DEFAULT")
    rate_limit_search: str = Field("200/minute", env="RATE_LIMIT_SEARCH")
    rate_limit_compare: str = Field("100/minute", env="RATE_LIMIT_COMPARE")
    
    # Cache Settings
    cache_default_ttl: int = Field(300, env="CACHE_DEFAULT_TTL")  # 5 minutes
    cache_supermarkets_ttl: int = Field(3600, env="CACHE_SUPERMARKETS_TTL")  # 1 hour
    cache_categories_ttl: int = Field(7200, env="CACHE_CATEGORIES_TTL")  # 2 hours
    cache_products_ttl: int = Field(1800, env="CACHE_PRODUCTS_TTL")  # 30 minutes
    cache_search_ttl: int = Field(600, env="CACHE_SEARCH_TTL")  # 10 minutes
    cache_comparison_ttl: int = Field(300, env="CACHE_COMPARISON_TTL")  # 5 minutes
    
    # Pagination
    default_page_size: int = Field(20, env="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(100, env="MAX_PAGE_SIZE")
    
    # Search
    search_min_length: int = Field(2, env="SEARCH_MIN_LENGTH")
    search_max_results: int = Field(1000, env="SEARCH_MAX_RESULTS")
    
    # Price History
    max_history_days: int = Field(365, env="MAX_HISTORY_DAYS")
    default_history_days: int = Field(30, env="DEFAULT_HISTORY_DAYS")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT")
    
    # Development
    debug: bool = Field(False, env="DEBUG")
    reload: bool = Field(False, env="RELOAD")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()