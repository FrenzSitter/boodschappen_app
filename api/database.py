"""
Database connection and utilities
================================
"""

from supabase import create_client, Client
import redis.asyncio as redis
from config import settings
import logging

logger = logging.getLogger(__name__)

# Global clients
_supabase_client: Client = None
_redis_client: redis.Redis = None

def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        logger.info("✅ Supabase client initialized")
    
    return _supabase_client

async def get_redis_client() -> redis.Redis:
    """Get Redis client instance"""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            password=settings.redis_password,
            db=settings.redis_db,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        logger.info("✅ Redis client initialized")
    
    return _redis_client

async def close_redis_client():
    """Close Redis client"""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("✅ Redis client closed")