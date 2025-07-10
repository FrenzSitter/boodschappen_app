#!/usr/bin/env python3
"""
CheckjeBon API - FastAPI Application
===================================

FastAPI application serving imported supermarket data from Supabase.

Features:
- Product search and comparison
- Price history tracking
- Category browsing
- Supermarket information
- Caching for performance
- Rate limiting
- API documentation

Author: Generated for boodschappen_app
Date: 2025-01-09
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
import asyncio
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# FastAPI and related imports
from fastapi import FastAPI, HTTPException, Depends, Query, Path as PathParam
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

# Database and caching
from supabase import create_client, Client
import redis.asyncio as redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Pydantic models
from pydantic import BaseModel, Field, validator
from pydantic.types import UUID4

# API models
from models import (
    Supermarket, Product, ProductPrice, PriceHistory, Category,
    ProductSearchResponse, PriceComparisonResponse, PriceHistoryResponse,
    ErrorResponse, APIResponse
)

# Configuration
from config import settings
from database import get_supabase_client, get_redis_client
from cache import cache_key, get_cached_response, set_cached_response
from utils import paginate_response, format_error_response

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# FastAPI app
app = FastAPI(
    title="CheckjeBon API",
    description="API for Dutch supermarket price comparison data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Rate limiting error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize connections and setup"""
    logger.info("🚀 Starting CheckjeBon API...")
    
    # Test database connection
    try:
        supabase = get_supabase_client()
        response = supabase.table("supermarkets").select("count").execute()
        logger.info(f"✅ Database connected - {response.count} supermarkets")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise
    
    # Test Redis connection
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"⚠️  Redis connection failed: {e}")
    
    logger.info("🎉 API startup complete")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections"""
    logger.info("🔄 Shutting down CheckjeBon API...")
    
    try:
        redis_client = await get_redis_client()
        await redis_client.close()
        logger.info("✅ Redis connection closed")
    except Exception as e:
        logger.warning(f"⚠️  Redis cleanup failed: {e}")
    
    logger.info("👋 API shutdown complete")

# Root endpoint
@app.get("/", response_model=APIResponse)
async def root():
    """API root endpoint with basic information"""
    return APIResponse(
        success=True,
        message="CheckjeBon API - Dutch Supermarket Price Comparison",
        data={
            "version": "1.0.0",
            "description": "API for accessing Dutch supermarket price data",
            "documentation": "/docs",
            "endpoints": {
                "supermarkets": "/supermarkets",
                "products": "/products",
                "search": "/products/search",
                "compare": "/products/compare",
                "categories": "/categories",
                "history": "/products/{product_id}/history"
            }
        }
    )

# Health check endpoint
@app.get("/health", response_model=APIResponse)
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "unknown",
        "cache": "unknown"
    }
    
    # Check database
    try:
        supabase = get_supabase_client()
        supabase.table("supermarkets").select("count").execute()
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
    
    # Check cache
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        health_status["cache"] = "connected"
    except Exception as e:
        health_status["cache"] = f"error: {str(e)}"
    
    return APIResponse(
        success=True,
        message="Health check completed",
        data=health_status
    )

# Supermarkets endpoints
@app.get("/supermarkets", response_model=APIResponse[List[Supermarket]])
@limiter.limit("30/minute")
async def get_supermarkets(request):
    """Get all supermarkets"""
    cache_key_name = cache_key("supermarkets")
    
    # Try cache first
    cached_response = await get_cached_response(cache_key_name)
    if cached_response:
        return cached_response
    
    try:
        supabase = get_supabase_client()
        response = supabase.table("supermarkets").select("*").eq("is_active", True).execute()
        
        supermarkets = [Supermarket(**item) for item in response.data]
        
        result = APIResponse(
            success=True,
            message=f"Retrieved {len(supermarkets)} supermarkets",
            data=supermarkets
        )
        
        # Cache for 1 hour
        await set_cached_response(cache_key_name, result, expire=3600)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting supermarkets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/supermarkets/{supermarket_id}", response_model=APIResponse[Supermarket])
@limiter.limit("60/minute")
async def get_supermarket(request, supermarket_id: UUID4):
    """Get specific supermarket by ID"""
    cache_key_name = cache_key("supermarket", supermarket_id)
    
    # Try cache first
    cached_response = await get_cached_response(cache_key_name)
    if cached_response:
        return cached_response
    
    try:
        supabase = get_supabase_client()
        response = supabase.table("supermarkets").select("*").eq("id", str(supermarket_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Supermarket not found")
        
        supermarket = Supermarket(**response.data[0])
        
        result = APIResponse(
            success=True,
            message="Supermarket retrieved successfully",
            data=supermarket
        )
        
        # Cache for 1 hour
        await set_cached_response(cache_key_name, result, expire=3600)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting supermarket {supermarket_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Products endpoints
@app.get("/products", response_model=APIResponse[List[Product]])
@limiter.limit("100/minute")
async def get_products(
    request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    supermarket_id: Optional[UUID4] = Query(None, description="Filter by supermarket"),
    category_id: Optional[UUID4] = Query(None, description="Filter by category")
):
    """Get products with pagination and filtering"""
    cache_key_name = cache_key("products", page, limit, supermarket_id, category_id)
    
    # Try cache first
    cached_response = await get_cached_response(cache_key_name)
    if cached_response:
        return cached_response
    
    try:
        supabase = get_supabase_client()
        
        # Build query
        query = supabase.table("products").select(
            "*, supermarkets!source_supermarket_id(*), categories(*)"
        ).eq("is_active", True)
        
        if supermarket_id:
            query = query.eq("source_supermarket_id", str(supermarket_id))
        
        if category_id:
            query = query.eq("category_id", str(category_id))
        
        # Add pagination
        offset = (page - 1) * limit
        query = query.range(offset, offset + limit - 1)
        
        response = query.execute()
        
        products = [Product(**item) for item in response.data]
        
        result = APIResponse(
            success=True,
            message=f"Retrieved {len(products)} products",
            data=products,
            pagination={
                "page": page,
                "limit": limit,
                "total": len(products),
                "has_more": len(products) == limit
            }
        )
        
        # Cache for 15 minutes
        await set_cached_response(cache_key_name, result, expire=900)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/search", response_model=APIResponse[ProductSearchResponse])
@limiter.limit("200/minute")
async def search_products(
    request,
    q: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=50, description="Items per page"),
    supermarket_id: Optional[UUID4] = Query(None, description="Filter by supermarket"),
    category_id: Optional[UUID4] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price")
):
    """Search products by name with filters"""
    cache_key_name = cache_key("search", q, page, limit, supermarket_id, category_id, min_price, max_price)
    
    # Try cache first
    cached_response = await get_cached_response(cache_key_name)
    if cached_response:
        return cached_response
    
    try:
        supabase = get_supabase_client()
        
        # Build search query using full-text search
        query = supabase.table("products").select(
            "*, supermarkets!source_supermarket_id(*), categories(*), product_prices!inner(*)"
        ).text_search("search_vector", q).eq("is_active", True)
        
        if supermarket_id:
            query = query.eq("source_supermarket_id", str(supermarket_id))
        
        if category_id:
            query = query.eq("category_id", str(category_id))
        
        if min_price is not None:
            query = query.gte("product_prices.price", min_price)
        
        if max_price is not None:
            query = query.lte("product_prices.price", max_price)
        
        # Add pagination
        offset = (page - 1) * limit
        query = query.range(offset, offset + limit - 1)
        
        response = query.execute()
        
        products = []
        for item in response.data:
            # Extract price information
            price_info = item.pop("product_prices", [])
            if price_info:
                item["current_price"] = price_info[0]
            
            products.append(Product(**item))
        
        search_response = ProductSearchResponse(
            query=q,
            results=products,
            total_results=len(products),
            page=page,
            limit=limit,
            filters={
                "supermarket_id": supermarket_id,
                "category_id": category_id,
                "min_price": min_price,
                "max_price": max_price
            }
        )
        
        result = APIResponse(
            success=True,
            message=f"Found {len(products)} products matching '{q}'",
            data=search_response
        )
        
        # Cache for 10 minutes
        await set_cached_response(cache_key_name, result, expire=600)
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/compare", response_model=APIResponse[PriceComparisonResponse])
@limiter.limit("100/minute")
async def compare_prices(
    request,
    product_name: str = Query(..., min_length=2, description="Product name to compare"),
    supermarket_ids: Optional[str] = Query(None, description="Comma-separated supermarket IDs")
):
    """Compare prices for a product across supermarkets"""
    cache_key_name = cache_key("compare", product_name, supermarket_ids)
    
    # Try cache first
    cached_response = await get_cached_response(cache_key_name)
    if cached_response:
        return cached_response
    
    try:
        supabase = get_supabase_client()
        
        # Search for similar products
        query = supabase.table("products").select(
            "*, supermarkets!source_supermarket_id(*), product_prices!inner(*)"
        ).text_search("search_vector", product_name).eq("is_active", True)
        
        if supermarket_ids:
            supermarket_id_list = [id.strip() for id in supermarket_ids.split(",")]
            query = query.in_("source_supermarket_id", supermarket_id_list)
        
        response = query.execute()
        
        # Group by supermarket
        price_comparison = {}
        for item in response.data:
            supermarket = item["supermarkets"]
            price_info = item["product_prices"][0] if item["product_prices"] else None
            
            if supermarket and price_info:
                supermarket_key = supermarket["slug"]
                if supermarket_key not in price_comparison:
                    price_comparison[supermarket_key] = {
                        "supermarket": Supermarket(**supermarket),
                        "products": []
                    }
                
                product_data = {k: v for k, v in item.items() if k not in ["supermarkets", "product_prices"]}
                product_data["current_price"] = ProductPrice(**price_info)
                
                price_comparison[supermarket_key]["products"].append(Product(**product_data))
        
        # Find best prices
        all_prices = []
        for supermarket_data in price_comparison.values():
            for product in supermarket_data["products"]:
                if product.current_price:
                    all_prices.append({
                        "supermarket": supermarket_data["supermarket"],
                        "product": product,
                        "price": product.current_price.price
                    })
        
        # Sort by price
        all_prices.sort(key=lambda x: x["price"])
        
        comparison_response = PriceComparisonResponse(
            query=product_name,
            supermarkets=list(price_comparison.values()),
            best_price=all_prices[0] if all_prices else None,
            price_range={
                "min": all_prices[0]["price"] if all_prices else None,
                "max": all_prices[-1]["price"] if all_prices else None,
                "average": sum(p["price"] for p in all_prices) / len(all_prices) if all_prices else None
            },
            total_results=len(all_prices)
        )
        
        result = APIResponse(
            success=True,
            message=f"Compared prices for '{product_name}' across {len(price_comparison)} supermarkets",
            data=comparison_response
        )
        
        # Cache for 5 minutes
        await set_cached_response(cache_key_name, result, expire=300)
        
        return result
        
    except Exception as e:
        logger.error(f"Error comparing prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/{product_id}", response_model=APIResponse[Product])
@limiter.limit("200/minute")
async def get_product(request, product_id: UUID4):
    """Get specific product by ID"""
    cache_key_name = cache_key("product", product_id)
    
    # Try cache first
    cached_response = await get_cached_response(cache_key_name)
    if cached_response:
        return cached_response
    
    try:
        supabase = get_supabase_client()
        response = supabase.table("products").select(
            "*, supermarkets!source_supermarket_id(*), categories(*), product_prices!inner(*)"
        ).eq("id", str(product_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Product not found")
        
        item = response.data[0]
        
        # Extract price information
        price_info = item.pop("product_prices", [])
        if price_info:
            item["current_price"] = price_info[0]
        
        product = Product(**item)
        
        result = APIResponse(
            success=True,
            message="Product retrieved successfully",
            data=product
        )
        
        # Cache for 30 minutes
        await set_cached_response(cache_key_name, result, expire=1800)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/{product_id}/history", response_model=APIResponse[PriceHistoryResponse])
@limiter.limit("100/minute")
async def get_price_history(
    request,
    product_id: UUID4,
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    supermarket_id: Optional[UUID4] = Query(None, description="Filter by supermarket")
):
    """Get price history for a product"""
    cache_key_name = cache_key("history", product_id, days, supermarket_id)
    
    # Try cache first
    cached_response = await get_cached_response(cache_key_name)
    if cached_response:
        return cached_response
    
    try:
        supabase = get_supabase_client()
        
        # Get product info
        product_response = supabase.table("products").select(
            "*, supermarkets!source_supermarket_id(*), categories(*)"
        ).eq("id", str(product_id)).execute()
        
        if not product_response.data:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product = Product(**product_response.data[0])
        
        # Get price history
        since_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        history_query = supabase.table("price_history").select(
            "*, supermarkets!supermarket_id(*)"
        ).eq("product_id", str(product_id)).gte("recorded_at", since_date)
        
        if supermarket_id:
            history_query = history_query.eq("supermarket_id", str(supermarket_id))
        
        history_response = history_query.order("recorded_at", desc=True).execute()
        
        price_history = [PriceHistory(**item) for item in history_response.data]
        
        # Calculate statistics
        if price_history:
            prices = [h.price for h in price_history]
            statistics = {
                "min_price": min(prices),
                "max_price": max(prices),
                "avg_price": sum(prices) / len(prices),
                "current_price": price_history[0].price if price_history else None,
                "price_change": price_history[0].price_change if price_history else None,
                "price_change_percentage": price_history[0].price_change_percentage if price_history else None
            }
        else:
            statistics = {}
        
        history_response = PriceHistoryResponse(
            product=product,
            history=price_history,
            period_days=days,
            statistics=statistics,
            total_records=len(price_history)
        )
        
        result = APIResponse(
            success=True,
            message=f"Retrieved {len(price_history)} price history records",
            data=history_response
        )
        
        # Cache for 1 hour
        await set_cached_response(cache_key_name, result, expire=3600)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting price history for {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Categories endpoints
@app.get("/categories", response_model=APIResponse[List[Category]])
@limiter.limit("30/minute")
async def get_categories(request):
    """Get all categories"""
    cache_key_name = cache_key("categories")
    
    # Try cache first
    cached_response = await get_cached_response(cache_key_name)
    if cached_response:
        return cached_response
    
    try:
        supabase = get_supabase_client()
        response = supabase.table("categories").select("*").eq("is_active", True).order("display_order").execute()
        
        categories = [Category(**item) for item in response.data]
        
        result = APIResponse(
            success=True,
            message=f"Retrieved {len(categories)} categories",
            data=categories
        )
        
        # Cache for 2 hours
        await set_cached_response(cache_key_name, result, expire=7200)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories/{category_id}/products", response_model=APIResponse[List[Product]])
@limiter.limit("100/minute")
async def get_category_products(
    request,
    category_id: UUID4,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """Get products in a specific category"""
    cache_key_name = cache_key("category_products", category_id, page, limit)
    
    # Try cache first
    cached_response = await get_cached_response(cache_key_name)
    if cached_response:
        return cached_response
    
    try:
        supabase = get_supabase_client()
        
        # Add pagination
        offset = (page - 1) * limit
        
        response = supabase.table("products").select(
            "*, supermarkets!source_supermarket_id(*), categories(*)"
        ).eq("category_id", str(category_id)).eq("is_active", True).range(offset, offset + limit - 1).execute()
        
        products = [Product(**item) for item in response.data]
        
        result = APIResponse(
            success=True,
            message=f"Retrieved {len(products)} products in category",
            data=products,
            pagination={
                "page": page,
                "limit": limit,
                "total": len(products),
                "has_more": len(products) == limit
            }
        )
        
        # Cache for 30 minutes
        await set_cached_response(cache_key_name, result, expire=1800)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting products for category {category_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(exc.detail, exc.status_code)
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=format_error_response("Internal server error", 500)
    )

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="CheckjeBon API",
        version="1.0.0",
        description="API for Dutch supermarket price comparison data",
        routes=app.routes,
    )
    
    # Add custom info
    openapi_schema["info"]["x-logo"] = {
        "url": "https://checkjebon.nl/logo.png",
        "altText": "CheckjeBon Logo"
    }
    
    # Add tags
    openapi_schema["tags"] = [
        {
            "name": "supermarkets",
            "description": "Operations with supermarkets"
        },
        {
            "name": "products",
            "description": "Operations with products"
        },
        {
            "name": "categories",
            "description": "Operations with categories"
        },
        {
            "name": "system",
            "description": "System and health operations"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )