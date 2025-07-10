"""
Caching utilities for CheckjeBon API
====================================
"""

import json
import hashlib
from typing import Any, Optional
from datetime import datetime, timedelta
import logging

from database import get_redis_client
from config import settings

logger = logging.getLogger(__name__)

def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    # Convert all arguments to strings
    key_parts = []
    
    for arg in args:
        if arg is not None:
            key_parts.append(str(arg))
    
    for key, value in sorted(kwargs.items()):
        if value is not None:
            key_parts.append(f"{key}:{value}")
    
    # Create hash of key parts
    key_string = ":".join(key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"checkjebon:api:{key_hash}"

async def get_cached_response(key: str) -> Optional[Any]:
    """Get cached response if available"""
    try:
        redis_client = await get_redis_client()
        cached_data = await redis_client.get(key)
        
        if cached_data:
            logger.debug(f"Cache hit for key: {key}")
            return json.loads(cached_data)
        
        logger.debug(f"Cache miss for key: {key}")
        return None
        
    except Exception as e:
        logger.warning(f"Cache get error for key {key}: {e}")
        return None

async def set_cached_response(key: str, data: Any, expire: int = None) -> bool:
    """Set cached response with expiration"""
    try:
        redis_client = await get_redis_client()
        
        # Use default TTL if not specified
        if expire is None:
            expire = settings.cache_default_ttl
        
        # Serialize data
        serialized_data = json.dumps(data, default=str)
        
        # Set with expiration
        await redis_client.setex(key, expire, serialized_data)
        
        logger.debug(f"Cache set for key: {key} (expire: {expire}s)")
        return True
        
    except Exception as e:
        logger.warning(f"Cache set error for key {key}: {e}")
        return False

async def delete_cached_response(key: str) -> bool:
    """Delete cached response"""
    try:
        redis_client = await get_redis_client()
        result = await redis_client.delete(key)
        
        if result:
            logger.debug(f"Cache deleted for key: {key}")
            return True
        
        return False
        
    except Exception as e:
        logger.warning(f"Cache delete error for key {key}: {e}")
        return False

async def clear_cache_pattern(pattern: str) -> int:
    """Clear cache entries matching pattern"""
    try:
        redis_client = await get_redis_client()
        
        # Find keys matching pattern
        keys = await redis_client.keys(f"checkjebon:api:{pattern}")
        
        if keys:
            deleted = await redis_client.delete(*keys)
            logger.info(f"Cleared {deleted} cache entries for pattern: {pattern}")
            return deleted
        
        return 0
        
    except Exception as e:
        logger.warning(f"Cache clear error for pattern {pattern}: {e}")
        return 0

async def get_cache_stats() -> dict:
    """Get cache statistics"""
    try:
        redis_client = await get_redis_client()
        
        # Get Redis info
        redis_info = await redis_client.info()
        
        # Count our keys
        our_keys = await redis_client.keys("checkjebon:api:*")
        
        stats = {
            "redis_connected": True,
            "redis_memory_used": redis_info.get("used_memory_human", "Unknown"),
            "redis_connected_clients": redis_info.get("connected_clients", 0),
            "our_cached_keys": len(our_keys),
            "cache_hit_rate": "N/A",  # Would need to implement hit/miss counters
            "uptime": redis_info.get("uptime_in_seconds", 0)
        }
        
        return stats
        
    except Exception as e:
        logger.warning(f"Cache stats error: {e}")
        return {
            "redis_connected": False,
            "error": str(e)
        }

# Cache decorators
def cache_response(expire: int = None, key_prefix: str = "default"):
    """Decorator to cache function responses"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache_key(key_prefix, func.__name__, *args, **kwargs)
            
            # Try to get cached response
            cached = await get_cached_response(key)
            if cached is not None:
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache the result
            await set_cached_response(key, result, expire)
            
            return result
        
        return wrapper
    return decorator

# Cache warming functions
async def warm_cache_supermarkets():
    """Warm cache for supermarkets data"""
    try:
        from database import get_supabase_client
        
        logger.info("Warming cache for supermarkets...")
        
        supabase = get_supabase_client()
        response = supabase.table("supermarkets").select("*").eq("is_active", True).execute()
        
        # Cache the response
        key = cache_key("supermarkets")
        await set_cached_response(key, response.data, settings.cache_supermarkets_ttl)
        
        logger.info(f"Cache warmed for {len(response.data)} supermarkets")
        
    except Exception as e:
        logger.warning(f"Cache warming error for supermarkets: {e}")

async def warm_cache_categories():
    """Warm cache for categories data"""
    try:
        from database import get_supabase_client
        
        logger.info("Warming cache for categories...")
        
        supabase = get_supabase_client()
        response = supabase.table("categories").select("*").eq("is_active", True).order("display_order").execute()
        
        # Cache the response
        key = cache_key("categories")
        await set_cached_response(key, response.data, settings.cache_categories_ttl)
        
        logger.info(f"Cache warmed for {len(response.data)} categories")
        
    except Exception as e:
        logger.warning(f"Cache warming error for categories: {e}")

async def warm_cache():
    """Warm all caches"""
    logger.info("Starting cache warming...")
    
    try:
        await warm_cache_supermarkets()
        await warm_cache_categories()
        
        logger.info("Cache warming completed successfully")
        
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")

# Cache middleware
class CacheMiddleware:
    """Middleware for automatic cache management"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Add cache headers
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append([b"cache-control", b"public, max-age=300"])
                    message["headers"] = headers
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)