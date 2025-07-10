#!/usr/bin/env python3
"""
Price History API
================

FastAPI application for serving price history data with comprehensive
endpoints for current prices, price history, comparisons, and analytics.

Features:
- Current price endpoints with cheapest store detection
- Price history with trends and alerts
- Cross-supermarket price comparisons
- Analytics endpoints for insights
- Response caching for performance
- Pagination and filtering
- OpenAPI documentation

Usage:
    uvicorn price_history_api:app --reload --host 0.0.0.0 --port 8000
"""

import os
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json
import hashlib
from functools import lru_cache
import time

# FastAPI imports
from fastapi import FastAPI, HTTPException, Depends, Query, Path, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

# Pydantic imports
from pydantic import BaseModel, Field, validator
from pydantic.types import UUID4

# Third-party imports
import numpy as np
from supabase import create_client, Client
from postgrest import APIError
import redis
from cachetools import TTLCache

# Local imports
from price_analysis import PriceAnalyzer, create_analyzer

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class TrendDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"

class PriceStatus(str, Enum):
    HEALTHY = "healthy"
    RISING = "rising"
    FALLING = "falling"
    VOLATILE = "volatile"

class SupermarketInfo(BaseModel):
    id: UUID4
    name: str
    slug: str
    logo_url: Optional[str] = None
    color_primary: Optional[str] = None

class ProductInfo(BaseModel):
    id: UUID4
    name: str
    brand: Optional[str] = None
    size_text: Optional[str] = None
    category_name: Optional[str] = None
    image_url: Optional[str] = None

class PricePoint(BaseModel):
    date: date
    price: float
    supermarket_id: UUID4
    supermarket_name: str
    is_on_sale: bool = False
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None

class CurrentPrice(BaseModel):
    product: ProductInfo
    supermarket: SupermarketInfo
    price: float
    price_per_unit: Optional[float] = None
    is_available: bool = True
    is_on_sale: bool = False
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    last_updated: datetime
    price_change_24h: Optional[float] = None
    price_change_percentage_24h: Optional[float] = None

class PriceHistory(BaseModel):
    product: ProductInfo
    supermarket: SupermarketInfo
    price_points: List[PricePoint]
    statistics: Dict[str, Any]
    trends: Dict[str, Any]

class PriceTrend(BaseModel):
    period: str
    direction: TrendDirection
    change_amount: float
    change_percentage: float
    volatility: float
    confidence: str  # high, medium, low

class PriceAlert(BaseModel):
    id: str
    product_id: UUID4
    supermarket_id: UUID4
    alert_type: str
    threshold: float
    current_price: float
    triggered_at: datetime
    message: str

class PriceComparison(BaseModel):
    product: ProductInfo
    prices: List[CurrentPrice]
    cheapest_store: SupermarketInfo
    most_expensive_store: SupermarketInfo
    price_range: float
    savings_percentage: float
    market_position: Dict[str, Any]

class SearchResult(BaseModel):
    product: ProductInfo
    current_prices: List[CurrentPrice]
    cheapest_price: float
    cheapest_store: SupermarketInfo
    price_range: float
    availability_count: int

class Analytics(BaseModel):
    metric_name: str
    value: Union[int, float, str]
    period: str
    timestamp: datetime
    trend: TrendDirection
    context: Dict[str, Any]

class PaginationInfo(BaseModel):
    page: int
    limit: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Any
    pagination: Optional[PaginationInfo] = None
    metadata: Dict[str, Any] = {}
    timestamp: datetime

# Request models
class PriceHistoryRequest(BaseModel):
    days: int = Field(default=30, ge=1, le=365)
    supermarket_ids: Optional[List[UUID4]] = None
    include_sales: bool = True

class PriceComparisonRequest(BaseModel):
    product_ids: List[UUID4] = Field(..., min_items=1, max_items=50)
    supermarket_ids: Optional[List[UUID4]] = None
    include_unavailable: bool = False

class AnalyticsRequest(BaseModel):
    category: Optional[str] = None
    supermarket_ids: Optional[List[UUID4]] = None
    days: int = Field(default=30, ge=1, le=365)
    metric: Optional[str] = None

# =============================================================================
# CONFIGURATION AND SETUP
# =============================================================================

class APIConfig:
    """API configuration"""
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.cache_ttl = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.rate_limit = int(os.getenv("RATE_LIMIT", "100"))  # per minute
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

config = APIConfig()

# Initialize FastAPI app
app = FastAPI(
    title="Price History API",
    description="Comprehensive API for supermarket price history data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global cache
cache = TTLCache(maxsize=1000, ttl=config.cache_ttl)

# =============================================================================
# DEPENDENCIES
# =============================================================================

@lru_cache()
def get_supabase_client() -> Client:
    """Get cached Supabase client"""
    return create_client(config.supabase_url, config.supabase_key)

@lru_cache()
def get_price_analyzer() -> PriceAnalyzer:
    """Get cached price analyzer"""
    return create_analyzer(config.supabase_url, config.supabase_key)

def get_redis_client():
    """Get Redis client for caching"""
    try:
        return redis.from_url(config.redis_url)
    except:
        return None

# Cache key generator
def generate_cache_key(endpoint: str, **kwargs) -> str:
    """Generate cache key for endpoint with parameters"""
    key_parts = [endpoint]
    for key, value in sorted(kwargs.items()):
        if value is not None:
            key_parts.append(f"{key}:{value}")
    
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

# Cache decorator
def cache_response(ttl: int = 300):
    """Cache decorator for endpoints"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(func.__name__, **kwargs)
            
            # Try to get from cache
            redis_client = get_redis_client()
            if redis_client:
                try:
                    cached_data = redis_client.get(cache_key)
                    if cached_data:
                        return json.loads(cached_data)
                except:
                    pass
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            if redis_client:
                try:
                    redis_client.setex(cache_key, ttl, json.dumps(result, default=str))
                except:
                    pass
            
            return result
        return wrapper
    return decorator

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_api_response(
    success: bool = True,
    message: str = "Success",
    data: Any = None,
    pagination: Optional[PaginationInfo] = None,
    metadata: Dict[str, Any] = None
) -> APIResponse:
    """Create standardized API response"""
    return APIResponse(
        success=success,
        message=message,
        data=data,
        pagination=pagination,
        metadata=metadata or {},
        timestamp=datetime.now()
    )

def create_pagination_info(page: int, limit: int, total: int) -> PaginationInfo:
    """Create pagination information"""
    pages = (total + limit - 1) // limit
    return PaginationInfo(
        page=page,
        limit=limit,
        total=total,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )

def calculate_price_change(current: float, previous: Optional[float]) -> tuple:
    """Calculate price change amount and percentage"""
    if previous is None or previous == 0:
        return 0.0, 0.0
    
    change_amount = current - previous
    change_percentage = (change_amount / previous) * 100
    
    return change_amount, change_percentage

def determine_trend_direction(change_percentage: float) -> TrendDirection:
    """Determine trend direction based on percentage change"""
    if abs(change_percentage) < 2.0:
        return TrendDirection.STABLE
    elif change_percentage > 0:
        return TrendDirection.UP
    else:
        return TrendDirection.DOWN

def format_product_info(product_row: Dict) -> ProductInfo:
    """Format product information from database row"""
    return ProductInfo(
        id=product_row['id'],
        name=product_row['name'],
        brand=product_row.get('brand'),
        size_text=product_row.get('size_text'),
        category_name=product_row.get('category_name'),
        image_url=product_row.get('image_url')
    )

def format_supermarket_info(supermarket_row: Dict) -> SupermarketInfo:
    """Format supermarket information from database row"""
    return SupermarketInfo(
        id=supermarket_row['id'],
        name=supermarket_row['name'],
        slug=supermarket_row['slug'],
        logo_url=supermarket_row.get('logo_url'),
        color_primary=supermarket_row.get('color_primary')
    )

# =============================================================================
# CURRENT PRICE ENDPOINTS
# =============================================================================

@app.get("/products/{product_id}/current-price", response_model=APIResponse)
@cache_response(ttl=300)
async def get_current_price(
    product_id: UUID4 = Path(..., description="Product ID"),
    supermarket_ids: Optional[List[UUID4]] = Query(None, description="Filter by supermarket IDs")
):
    """
    Get current prices for a product across all supermarkets or filtered by supermarket IDs.
    
    Returns current pricing information including:
    - Current price and availability
    - Sale information and discounts
    - Price changes in last 24 hours
    - Price per unit calculations
    """
    try:
        supabase = get_supabase_client()
        
        # Build query
        query = supabase.table("current_prices").select(
            "*, products!inner(*), supermarkets!inner(*)"
        ).eq("product_id", str(product_id))
        
        if supermarket_ids:
            query = query.in_("supermarket_id", [str(sid) for sid in supermarket_ids])
        
        response = query.execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Product not found or no current prices available")
        
        # Get 24h price changes
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        price_changes = supabase.table("price_history").select(
            "supermarket_id, price"
        ).eq("product_id", str(product_id)).eq("price_date", yesterday).execute()
        
        price_changes_dict = {row['supermarket_id']: row['price'] for row in price_changes.data}
        
        # Format response
        current_prices = []
        for row in response.data:
            # Calculate 24h price change
            previous_price = price_changes_dict.get(row['supermarket_id'])
            change_amount, change_percentage = calculate_price_change(row['price'], previous_price)
            
            current_price = CurrentPrice(
                product=format_product_info(row['products']),
                supermarket=format_supermarket_info(row['supermarkets']),
                price=row['price'],
                price_per_unit=row.get('price_per_unit'),
                is_available=row['is_available'],
                is_on_sale=row['is_on_sale'],
                original_price=row.get('original_price'),
                discount_percentage=row.get('discount_percentage'),
                last_updated=datetime.fromisoformat(row['last_updated'].replace('Z', '+00:00')),
                price_change_24h=change_amount,
                price_change_percentage_24h=change_percentage
            )
            current_prices.append(current_price)
        
        # Sort by price
        current_prices.sort(key=lambda x: x.price)
        
        return create_api_response(
            data=current_prices,
            metadata={
                "product_id": str(product_id),
                "supermarket_count": len(current_prices),
                "available_count": len([p for p in current_prices if p.is_available]),
                "on_sale_count": len([p for p in current_prices if p.is_on_sale])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/products/{product_id}/cheapest-store", response_model=APIResponse)
@cache_response(ttl=300)
async def get_cheapest_store(
    product_id: UUID4 = Path(..., description="Product ID"),
    include_unavailable: bool = Query(False, description="Include unavailable products")
):
    """
    Find the cheapest store for a specific product.
    
    Returns:
    - Cheapest available price
    - Store information
    - Savings compared to most expensive
    - Historical price context
    """
    try:
        supabase = get_supabase_client()
        
        # Get current prices
        query = supabase.table("current_prices").select(
            "*, products!inner(*), supermarkets!inner(*)"
        ).eq("product_id", str(product_id))
        
        if not include_unavailable:
            query = query.eq("is_available", True)
        
        response = query.execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Product not found or no prices available")
        
        # Find cheapest
        cheapest_row = min(response.data, key=lambda x: x['price'])
        most_expensive_row = max(response.data, key=lambda x: x['price'])
        
        # Calculate savings
        savings_amount = most_expensive_row['price'] - cheapest_row['price']
        savings_percentage = (savings_amount / most_expensive_row['price']) * 100
        
        # Get historical context (average price last 30 days)
        thirty_days_ago = (date.today() - timedelta(days=30)).isoformat()
        historical_prices = supabase.table("price_history").select(
            "price"
        ).eq("product_id", str(product_id)).eq("supermarket_id", cheapest_row['supermarket_id']).gte("price_date", thirty_days_ago).execute()
        
        avg_historical_price = np.mean([row['price'] for row in historical_prices.data]) if historical_prices.data else cheapest_row['price']
        
        result = {
            "cheapest_price": CurrentPrice(
                product=format_product_info(cheapest_row['products']),
                supermarket=format_supermarket_info(cheapest_row['supermarkets']),
                price=cheapest_row['price'],
                price_per_unit=cheapest_row.get('price_per_unit'),
                is_available=cheapest_row['is_available'],
                is_on_sale=cheapest_row['is_on_sale'],
                original_price=cheapest_row.get('original_price'),
                discount_percentage=cheapest_row.get('discount_percentage'),
                last_updated=datetime.fromisoformat(cheapest_row['last_updated'].replace('Z', '+00:00'))
            ),
            "savings": {
                "amount": savings_amount,
                "percentage": savings_percentage,
                "compared_to": format_supermarket_info(most_expensive_row['supermarkets'])
            },
            "historical_context": {
                "avg_price_30d": avg_historical_price,
                "current_vs_avg": ((cheapest_row['price'] - avg_historical_price) / avg_historical_price) * 100,
                "price_trend": determine_trend_direction(((cheapest_row['price'] - avg_historical_price) / avg_historical_price) * 100)
            }
        }
        
        return create_api_response(
            data=result,
            metadata={
                "product_id": str(product_id),
                "stores_compared": len(response.data),
                "analysis_date": date.today().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/supermarkets/{store_id}/products", response_model=APIResponse)
@cache_response(ttl=300)
async def get_supermarket_products(
    store_id: UUID4 = Path(..., description="Supermarket ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    on_sale: Optional[bool] = Query(None, description="Filter by sale status"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter")
):
    """
    Get all products available at a specific supermarket with filtering options.
    
    Supports filtering by:
    - Category
    - Sale status
    - Price range
    - Availability
    """
    try:
        supabase = get_supabase_client()
        
        # Build query
        query = supabase.table("current_prices").select(
            "*, products!inner(*), supermarkets!inner(*)"
        ).eq("supermarket_id", str(store_id)).eq("is_available", True)
        
        # Apply filters
        if category:
            query = query.eq("products.category_id", category)
        
        if on_sale is not None:
            query = query.eq("is_on_sale", on_sale)
        
        if min_price is not None:
            query = query.gte("price", min_price)
        
        if max_price is not None:
            query = query.lte("price", max_price)
        
        # Get total count
        count_response = query.execute()
        total = len(count_response.data)
        
        # Apply pagination
        offset = (page - 1) * limit
        response = query.range(offset, offset + limit - 1).execute()
        
        # Format response
        products = []
        for row in response.data:
            current_price = CurrentPrice(
                product=format_product_info(row['products']),
                supermarket=format_supermarket_info(row['supermarkets']),
                price=row['price'],
                price_per_unit=row.get('price_per_unit'),
                is_available=row['is_available'],
                is_on_sale=row['is_on_sale'],
                original_price=row.get('original_price'),
                discount_percentage=row.get('discount_percentage'),
                last_updated=datetime.fromisoformat(row['last_updated'].replace('Z', '+00:00'))
            )
            products.append(current_price)
        
        # Sort by price
        products.sort(key=lambda x: x.price)
        
        pagination = create_pagination_info(page, limit, total)
        
        return create_api_response(
            data=products,
            pagination=pagination,
            metadata={
                "supermarket_id": str(store_id),
                "filters_applied": {
                    "category": category,
                    "on_sale": on_sale,
                    "price_range": [min_price, max_price]
                },
                "total_products": total,
                "on_sale_count": len([p for p in products if p.is_on_sale])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# =============================================================================
# PRICE HISTORY ENDPOINTS
# =============================================================================

@app.get("/products/{product_id}/price-history", response_model=APIResponse)
@cache_response(ttl=600)
async def get_price_history(
    product_id: UUID4 = Path(..., description="Product ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve"),
    supermarket_ids: Optional[List[UUID4]] = Query(None, description="Filter by supermarket IDs"),
    include_sales: bool = Query(True, description="Include sale information")
):
    """
    Get price history for a product with detailed statistics and trends.
    
    Returns:
    - Daily price points with change indicators
    - Statistical analysis (min, max, average, volatility)
    - Trend analysis and direction
    - Sale periods and discount information
    """
    try:
        supabase = get_supabase_client()
        
        # Date range
        start_date = (date.today() - timedelta(days=days)).isoformat()
        
        # Build query
        query = supabase.table("price_history").select(
            "*, products!inner(*), supermarkets!inner(*)"
        ).eq("product_id", str(product_id)).gte("price_date", start_date).order("price_date", desc=False)
        
        if supermarket_ids:
            query = query.in_("supermarket_id", [str(sid) for sid in supermarket_ids])
        
        response = query.execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="No price history found for this product")
        
        # Group by supermarket
        supermarket_histories = {}
        for row in response.data:
            supermarket_id = row['supermarket_id']
            if supermarket_id not in supermarket_histories:
                supermarket_histories[supermarket_id] = {
                    'product': format_product_info(row['products']),
                    'supermarket': format_supermarket_info(row['supermarkets']),
                    'price_points': [],
                    'statistics': {},
                    'trends': {}
                }
            
            price_point = PricePoint(
                date=date.fromisoformat(row['price_date']),
                price=row['price'],
                supermarket_id=row['supermarket_id'],
                supermarket_name=row['supermarkets']['name'],
                is_on_sale=row.get('is_on_sale', False),
                original_price=row.get('original_price'),
                discount_percentage=row.get('discount_percentage')
            )
            
            supermarket_histories[supermarket_id]['price_points'].append(price_point)
        
        # Calculate statistics and trends for each supermarket
        for supermarket_id, history in supermarket_histories.items():
            prices = [p.price for p in history['price_points']]
            
            if len(prices) > 1:
                # Statistics
                history['statistics'] = {
                    'min_price': min(prices),
                    'max_price': max(prices),
                    'avg_price': np.mean(prices),
                    'median_price': np.median(prices),
                    'volatility': np.std(prices),
                    'price_range': max(prices) - min(prices),
                    'data_points': len(prices)
                }
                
                # Trends
                latest_price = prices[-1]
                earliest_price = prices[0]
                overall_change = ((latest_price - earliest_price) / earliest_price) * 100
                
                # Weekly trend (if enough data)
                weekly_trend = 0
                if len(prices) >= 7:
                    recent_week = prices[-7:]
                    previous_week = prices[-14:-7] if len(prices) >= 14 else prices[:-7]
                    if previous_week:
                        weekly_trend = ((np.mean(recent_week) - np.mean(previous_week)) / np.mean(previous_week)) * 100
                
                history['trends'] = {
                    'overall_change_percentage': overall_change,
                    'overall_direction': determine_trend_direction(overall_change),
                    'weekly_change_percentage': weekly_trend,
                    'weekly_direction': determine_trend_direction(weekly_trend),
                    'volatility_score': (np.std(prices) / np.mean(prices)) * 100 if np.mean(prices) > 0 else 0,
                    'price_status': self._determine_price_status(prices)
                }
        
        # Convert to list format
        histories = list(supermarket_histories.values())
        
        return create_api_response(
            data=histories,
            metadata={
                "product_id": str(product_id),
                "period_days": days,
                "supermarket_count": len(histories),
                "date_range": {
                    "start": start_date,
                    "end": date.today().isoformat()
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def _determine_price_status(prices: List[float]) -> PriceStatus:
    """Determine price status based on recent trends"""
    if len(prices) < 7:
        return PriceStatus.HEALTHY
    
    recent_prices = prices[-7:]
    volatility = np.std(recent_prices) / np.mean(recent_prices) * 100
    
    if volatility > 20:
        return PriceStatus.VOLATILE
    
    trend = ((recent_prices[-1] - recent_prices[0]) / recent_prices[0]) * 100
    
    if trend > 5:
        return PriceStatus.RISING
    elif trend < -5:
        return PriceStatus.FALLING
    else:
        return PriceStatus.HEALTHY

@app.get("/products/{product_id}/price-trends", response_model=APIResponse)
@cache_response(ttl=600)
async def get_price_trends(
    product_id: UUID4 = Path(..., description="Product ID"),
    periods: List[str] = Query(["7d", "30d", "90d"], description="Time periods to analyze")
):
    """
    Get price trends for different time periods.
    
    Analyzes trends over multiple periods:
    - Short-term (7 days)
    - Medium-term (30 days)
    - Long-term (90 days)
    
    Returns trend direction, volatility, and confidence levels.
    """
    try:
        analyzer = get_price_analyzer()
        
        trends = {}
        for period in periods:
            # Parse period
            if period.endswith('d'):
                days = int(period[:-1])
            elif period.endswith('w'):
                days = int(period[:-1]) * 7
            elif period.endswith('m'):
                days = int(period[:-1]) * 30
            else:
                continue
            
            # Get trends for this period
            period_trends = analyzer.get_price_trends(product_id=str(product_id), days=days)
            
            if period_trends:
                # Calculate aggregate trend
                avg_change = np.mean([t.price_change_percentage for t in period_trends])
                avg_volatility = np.mean([t.volatility for t in period_trends])
                
                # Determine confidence based on data points
                total_data_points = sum(t.data_points for t in period_trends)
                confidence = "high" if total_data_points >= days * 0.8 else "medium" if total_data_points >= days * 0.5 else "low"
                
                trends[period] = PriceTrend(
                    period=period,
                    direction=determine_trend_direction(avg_change),
                    change_amount=np.mean([t.price_change for t in period_trends]),
                    change_percentage=avg_change,
                    volatility=avg_volatility,
                    confidence=confidence
                )
        
        return create_api_response(
            data=trends,
            metadata={
                "product_id": str(product_id),
                "periods_analyzed": len(trends),
                "analysis_date": date.today().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/products/{product_id}/price-alerts", response_model=APIResponse)
@cache_response(ttl=180)
async def get_price_alerts(
    product_id: UUID4 = Path(..., description="Product ID"),
    days: int = Query(7, ge=1, le=30, description="Days to check for alerts")
):
    """
    Get price alerts for a product based on recent price changes.
    
    Returns alerts for:
    - Significant price increases/decreases
    - Volatility warnings
    - Sale opportunities
    - Stock availability changes
    """
    try:
        analyzer = get_price_analyzer()
        
        # Get recent alerts
        alerts = analyzer.check_price_alerts()
        
        # Filter for this product
        product_alerts = [alert for alert in alerts if alert.product_id == str(product_id)]
        
        # Format alerts
        formatted_alerts = []
        for alert in product_alerts:
            price_alert = PriceAlert(
                id=alert.alert_id,
                product_id=UUID4(alert.product_id),
                supermarket_id=UUID4(alert.supermarket_id),
                alert_type=alert.alert_type,
                threshold=alert.threshold_value if hasattr(alert, 'threshold_value') else 0,
                current_price=alert.current_price,
                triggered_at=alert.detected_at,
                message=alert.description
            )
            formatted_alerts.append(price_alert)
        
        # Get additional context
        recent_changes = analyzer.detect_significant_changes(days=days, threshold=10.0)
        product_changes = [change for change in recent_changes if change['product_id'] == str(product_id)]
        
        return create_api_response(
            data={
                "alerts": formatted_alerts,
                "recent_changes": product_changes,
                "alert_summary": {
                    "total_alerts": len(formatted_alerts),
                    "price_drops": len([a for a in formatted_alerts if a.alert_type == "price_drop"]),
                    "price_spikes": len([a for a in formatted_alerts if a.alert_type == "price_spike"]),
                    "significant_changes": len(product_changes)
                }
            },
            metadata={
                "product_id": str(product_id),
                "analysis_period": f"{days} days",
                "alert_types": list(set(a.alert_type for a in formatted_alerts))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# =============================================================================
# COMPARISON ENDPOINTS
# =============================================================================

@app.get("/products/{product_id}/price-comparison", response_model=APIResponse)
@cache_response(ttl=300)
async def get_price_comparison(
    product_id: UUID4 = Path(..., description="Product ID"),
    include_unavailable: bool = Query(False, description="Include unavailable products")
):
    """
    Compare prices for a product across all supermarkets.
    
    Returns:
    - Current prices from all supermarkets
    - Cheapest and most expensive stores
    - Price range and savings opportunities
    - Market position analysis
    """
    try:
        analyzer = get_price_analyzer()
        
        # Get current price comparison
        comparisons = analyzer.compare_current_prices(product_id=str(product_id))
        
        if not comparisons:
            raise HTTPException(status_code=404, detail="No price comparison data available")
        
        comparison = comparisons[0]  # Should only be one for specific product
        
        # Get detailed current prices
        supabase = get_supabase_client()
        query = supabase.table("current_prices").select(
            "*, products!inner(*), supermarkets!inner(*)"
        ).eq("product_id", str(product_id))
        
        if not include_unavailable:
            query = query.eq("is_available", True)
        
        response = query.execute()
        
        # Format prices
        current_prices = []
        for row in response.data:
            current_price = CurrentPrice(
                product=format_product_info(row['products']),
                supermarket=format_supermarket_info(row['supermarkets']),
                price=row['price'],
                price_per_unit=row.get('price_per_unit'),
                is_available=row['is_available'],
                is_on_sale=row['is_on_sale'],
                original_price=row.get('original_price'),
                discount_percentage=row.get('discount_percentage'),
                last_updated=datetime.fromisoformat(row['last_updated'].replace('Z', '+00:00'))
            )
            current_prices.append(current_price)
        
        # Sort by price
        current_prices.sort(key=lambda x: x.price)
        
        # Find cheapest and most expensive
        cheapest = current_prices[0]
        most_expensive = current_prices[-1]
        
        # Calculate market position
        prices_only = [p.price for p in current_prices]
        market_position = {
            "percentile_25": np.percentile(prices_only, 25),
            "percentile_50": np.percentile(prices_only, 50),
            "percentile_75": np.percentile(prices_only, 75),
            "price_distribution": {
                "min": min(prices_only),
                "max": max(prices_only),
                "mean": np.mean(prices_only),
                "std": np.std(prices_only)
            }
        }
        
        price_comparison = PriceComparison(
            product=cheapest.product,
            prices=current_prices,
            cheapest_store=cheapest.supermarket,
            most_expensive_store=most_expensive.supermarket,
            price_range=most_expensive.price - cheapest.price,
            savings_percentage=((most_expensive.price - cheapest.price) / most_expensive.price) * 100,
            market_position=market_position
        )
        
        return create_api_response(
            data=price_comparison,
            metadata={
                "product_id": str(product_id),
                "supermarket_count": len(current_prices),
                "available_count": len([p for p in current_prices if p.is_available]),
                "comparison_date": date.today().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/products/search", response_model=APIResponse)
@cache_response(ttl=300)
async def search_products(
    q: str = Query(..., min_length=2, description="Search query"),
    compare_prices: bool = Query(False, description="Include price comparison"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    supermarket_ids: Optional[List[UUID4]] = Query(None, description="Filter by supermarket IDs")
):
    """
    Search for products with optional price comparison.
    
    Returns:
    - Matching products with current prices
    - Price comparison across supermarkets (if enabled)
    - Cheapest store for each product
    - Availability information
    """
    try:
        supabase = get_supabase_client()
        
        # Build search query
        query = supabase.table("products").select(
            "*, current_prices!inner(*, supermarkets!inner(*))"
        ).ilike("name", f"%{q}%")
        
        if category:
            query = query.eq("category_id", category)
        
        # Get total count for pagination
        count_response = query.execute()
        total = len(count_response.data)
        
        # Apply pagination
        offset = (page - 1) * limit
        response = query.range(offset, offset + limit - 1).execute()
        
        # Process results
        search_results = []
        for row in response.data:
            product_info = format_product_info(row)
            
            # Get current prices for this product
            current_prices = []
            for price_row in row['current_prices']:
                if supermarket_ids and price_row['supermarket_id'] not in [str(sid) for sid in supermarket_ids]:
                    continue
                
                current_price = CurrentPrice(
                    product=product_info,
                    supermarket=format_supermarket_info(price_row['supermarkets']),
                    price=price_row['price'],
                    price_per_unit=price_row.get('price_per_unit'),
                    is_available=price_row['is_available'],
                    is_on_sale=price_row['is_on_sale'],
                    original_price=price_row.get('original_price'),
                    discount_percentage=price_row.get('discount_percentage'),
                    last_updated=datetime.fromisoformat(price_row['last_updated'].replace('Z', '+00:00'))
                )
                current_prices.append(current_price)
            
            if current_prices:
                # Sort by price
                current_prices.sort(key=lambda x: x.price)
                
                # Find cheapest
                cheapest = current_prices[0]
                most_expensive = current_prices[-1]
                
                search_result = SearchResult(
                    product=product_info,
                    current_prices=current_prices if compare_prices else [cheapest],
                    cheapest_price=cheapest.price,
                    cheapest_store=cheapest.supermarket,
                    price_range=most_expensive.price - cheapest.price,
                    availability_count=len([p for p in current_prices if p.is_available])
                )
                search_results.append(search_result)
        
        pagination = create_pagination_info(page, limit, total)
        
        return create_api_response(
            data=search_results,
            pagination=pagination,
            metadata={
                "search_query": q,
                "results_count": len(search_results),
                "compare_prices": compare_prices,
                "filters": {
                    "category": category,
                    "supermarket_ids": supermarket_ids
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/supermarkets/price-comparison", response_model=APIResponse)
@cache_response(ttl=300)
async def bulk_price_comparison(
    request: PriceComparisonRequest,
    supermarket_ids: Optional[List[UUID4]] = Query(None, description="Filter by supermarket IDs")
):
    """
    Compare prices for multiple products across supermarkets.
    
    Bulk comparison endpoint for:
    - Multiple products at once
    - Cross-supermarket analysis
    - Savings opportunities
    - Market basket analysis
    """
    try:
        analyzer = get_price_analyzer()
        
        # Get price comparisons for all products
        comparisons = []
        for product_id in request.product_ids:
            product_comparisons = analyzer.compare_current_prices(product_id=str(product_id))
            if product_comparisons:
                comparisons.extend(product_comparisons)
        
        if not comparisons:
            raise HTTPException(status_code=404, detail="No price comparison data available")
        
        # Calculate bulk savings
        total_savings = 0
        comparison_results = []
        
        for comparison in comparisons:
            # Get detailed price info
            supabase = get_supabase_client()
            response = supabase.table("current_prices").select(
                "*, products!inner(*), supermarkets!inner(*)"
            ).eq("product_id", comparison.product_id)
            
            if supermarket_ids:
                response = response.in_("supermarket_id", [str(sid) for sid in supermarket_ids])
            
            if not request.include_unavailable:
                response = response.eq("is_available", True)
            
            price_data = response.execute()
            
            if price_data.data:
                prices = [row['price'] for row in price_data.data]
                min_price = min(prices)
                max_price = max(prices)
                
                savings = max_price - min_price
                total_savings += savings
                
                comparison_results.append({
                    "product_id": comparison.product_id,
                    "product_name": comparison.product_name,
                    "min_price": min_price,
                    "max_price": max_price,
                    "price_range": savings,
                    "savings_percentage": (savings / max_price) * 100 if max_price > 0 else 0,
                    "supermarket_count": len(price_data.data)
                })
        
        # Market basket analysis
        if len(comparison_results) > 1:
            # Find stores with best overall prices
            store_totals = {}
            for result in comparison_results:
                # This would need more complex logic to find actual store combinations
                pass
        
        return create_api_response(
            data={
                "comparisons": comparison_results,
                "summary": {
                    "total_products": len(request.product_ids),
                    "total_savings_available": total_savings,
                    "avg_savings_per_product": total_savings / len(comparison_results) if comparison_results else 0,
                    "best_overall_savings": max([r["savings_percentage"] for r in comparison_results]) if comparison_results else 0
                }
            },
            metadata={
                "product_count": len(request.product_ids),
                "comparison_date": date.today().isoformat(),
                "filters": {
                    "supermarket_ids": supermarket_ids,
                    "include_unavailable": request.include_unavailable
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# =============================================================================
# ANALYTICS ENDPOINTS
# =============================================================================

@app.get("/analytics/price-trends", response_model=APIResponse)
@cache_response(ttl=900)
async def get_analytics_price_trends(
    category: Optional[str] = Query(None, description="Filter by category"),
    days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    supermarket_ids: Optional[List[UUID4]] = Query(None, description="Filter by supermarket IDs")
):
    """
    Get price trend analytics for categories or overall market.
    
    Returns:
    - Category-level price trends
    - Market volatility analysis
    - Seasonal patterns
    - Price direction indicators
    """
    try:
        analyzer = get_price_analyzer()
        
        # Get price volatility data
        volatility_data = analyzer.get_price_volatility(days=days)
        
        # Filter by category if specified
        if category:
            volatility_data = [v for v in volatility_data if v.get('category') == category]
        
        # Group by category
        category_trends = {}
        for item in volatility_data:
            cat = item.get('category', 'uncategorized')
            if cat not in category_trends:
                category_trends[cat] = {
                    'products': [],
                    'avg_volatility': 0,
                    'trend_direction': TrendDirection.STABLE,
                    'price_changes': []
                }
            category_trends[cat]['products'].append(item)
        
        # Calculate category statistics
        for cat, data in category_trends.items():
            volatilities = [p['volatility'] for p in data['products']]
            data['avg_volatility'] = np.mean(volatilities)
            data['product_count'] = len(data['products'])
            data['high_volatility_count'] = len([v for v in volatilities if v > 20])
        
        # Get overall market trends
        overall_trends = analyzer.get_price_trends(days=days)
        
        if overall_trends:
            avg_change = np.mean([t.price_change_percentage for t in overall_trends])
            market_direction = determine_trend_direction(avg_change)
            
            market_summary = {
                'overall_direction': market_direction,
                'avg_change_percentage': avg_change,
                'products_analyzed': len(overall_trends),
                'volatile_products': len([t for t in overall_trends if t.volatility > 20]),
                'rising_products': len([t for t in overall_trends if t.price_change_percentage > 5]),
                'falling_products': len([t for t in overall_trends if t.price_change_percentage < -5])
            }
        else:
            market_summary = {}
        
        analytics = Analytics(
            metric_name="price_trends",
            value=len(category_trends),
            period=f"{days}d",
            timestamp=datetime.now(),
            trend=market_summary.get('overall_direction', TrendDirection.STABLE),
            context={
                'category_trends': category_trends,
                'market_summary': market_summary
            }
        )
        
        return create_api_response(
            data=analytics,
            metadata={
                "analysis_period": f"{days} days",
                "categories_analyzed": len(category_trends),
                "filter_category": category,
                "supermarket_filter": supermarket_ids
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/analytics/top-deals", response_model=APIResponse)
@cache_response(ttl=300)
async def get_top_deals(
    days: int = Query(7, ge=1, le=30, description="Period to analyze for deals"),
    limit: int = Query(20, ge=1, le=100, description="Number of deals to return"),
    min_discount: float = Query(20.0, ge=0, le=100, description="Minimum discount percentage"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Get top deals and discounts available.
    
    Returns:
    - Current sale items with highest discounts
    - Recent price drops
    - Best savings opportunities
    - Deal trends and patterns
    """
    try:
        supabase = get_supabase_client()
        
        # Get current deals
        query = supabase.table("current_prices").select(
            "*, products!inner(*), supermarkets!inner(*)"
        ).eq("is_on_sale", True).gte("discount_percentage", min_discount)
        
        if category:
            query = query.eq("products.category_id", category)
        
        response = query.order("discount_percentage", desc=True).limit(limit).execute()
        
        # Get recent price drops
        analyzer = get_price_analyzer()
        recent_changes = analyzer.detect_significant_changes(days=days, threshold=15.0)
        
        # Filter for price drops
        price_drops = [change for change in recent_changes if change['change_type'] == 'decrease']
        
        # Format deals
        current_deals = []
        for row in response.data:
            deal = {
                'product': format_product_info(row['products']),
                'supermarket': format_supermarket_info(row['supermarkets']),
                'current_price': row['price'],
                'original_price': row['original_price'],
                'discount_percentage': row['discount_percentage'],
                'savings_amount': row['original_price'] - row['price'],
                'deal_type': 'sale'
            }
            current_deals.append(deal)
        
        # Combine with price drops
        all_deals = current_deals + [
            {
                'product': {'name': change['product_name']},
                'supermarket': {'name': change['supermarket_name']},
                'current_price': change['current_price'],
                'change_percentage': change['change_percentage'],
                'deal_type': 'price_drop'
            }
            for change in price_drops[:limit//2]
        ]
        
        # Sort by savings potential
        all_deals.sort(key=lambda x: x.get('discount_percentage', abs(x.get('change_percentage', 0))), reverse=True)
        
        analytics = Analytics(
            metric_name="top_deals",
            value=len(all_deals),
            period=f"{days}d",
            timestamp=datetime.now(),
            trend=TrendDirection.STABLE,
            context={
                'deals': all_deals[:limit],
                'summary': {
                    'total_deals': len(all_deals),
                    'current_sales': len(current_deals),
                    'recent_drops': len(price_drops),
                    'avg_discount': np.mean([d.get('discount_percentage', 0) for d in current_deals]) if current_deals else 0,
                    'best_deal': max(all_deals, key=lambda x: x.get('discount_percentage', 0)) if all_deals else None
                }
            }
        )
        
        return create_api_response(
            data=analytics,
            metadata={
                "analysis_period": f"{days} days",
                "min_discount": min_discount,
                "category_filter": category,
                "deals_found": len(all_deals)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/analytics/price-volatility", response_model=APIResponse)
@cache_response(ttl=600)
async def get_price_volatility_analytics(
    days: int = Query(30, ge=7, le=365, description="Analysis period in days"),
    category: Optional[str] = Query(None, description="Filter by category"),
    threshold: float = Query(20.0, ge=0, description="Volatility threshold percentage")
):
    """
    Get price volatility analytics.
    
    Returns:
    - Products with high price volatility
    - Volatility trends by category
    - Market stability indicators
    - Volatility patterns and causes
    """
    try:
        analyzer = get_price_analyzer()
        
        # Get volatility data
        volatility_data = analyzer.get_price_volatility(days=days)
        
        # Filter by category if specified
        if category:
            volatility_data = [v for v in volatility_data if v.get('category') == category]
        
        # Analyze volatility patterns
        high_volatility = [v for v in volatility_data if v['volatility'] > threshold]
        
        # Group by volatility class
        volatility_distribution = {
            'low': len([v for v in volatility_data if v['volatility_class'] == 'low']),
            'medium': len([v for v in volatility_data if v['volatility_class'] == 'medium']),
            'high': len([v for v in volatility_data if v['volatility_class'] == 'high'])
        }
        
        # Category breakdown
        category_volatility = {}
        for item in volatility_data:
            cat = item.get('category', 'uncategorized')
            if cat not in category_volatility:
                category_volatility[cat] = {
                    'count': 0,
                    'avg_volatility': 0,
                    'high_volatility_count': 0
                }
            
            category_volatility[cat]['count'] += 1
            category_volatility[cat]['avg_volatility'] += item['volatility']
            if item['volatility'] > threshold:
                category_volatility[cat]['high_volatility_count'] += 1
        
        # Calculate averages
        for cat, data in category_volatility.items():
            data['avg_volatility'] = data['avg_volatility'] / data['count']
            data['volatility_rate'] = (data['high_volatility_count'] / data['count']) * 100
        
        # Market stability score
        total_products = len(volatility_data)
        stability_score = 100 - (len(high_volatility) / total_products * 100) if total_products > 0 else 0
        
        analytics = Analytics(
            metric_name="price_volatility",
            value=len(high_volatility),
            period=f"{days}d",
            timestamp=datetime.now(),
            trend=TrendDirection.STABLE,
            context={
                'high_volatility_products': high_volatility[:20],  # Top 20
                'volatility_distribution': volatility_distribution,
                'category_analysis': category_volatility,
                'market_stability': {
                    'stability_score': stability_score,
                    'total_products': total_products,
                    'high_volatility_count': len(high_volatility),
                    'avg_volatility': np.mean([v['volatility'] for v in volatility_data]) if volatility_data else 0
                }
            }
        )
        
        return create_api_response(
            data=analytics,
            metadata={
                "analysis_period": f"{days} days",
                "volatility_threshold": threshold,
                "category_filter": category,
                "products_analyzed": total_products
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# =============================================================================
# HEALTH CHECK AND DOCUMENTATION
# =============================================================================

@app.get("/health", response_model=APIResponse)
async def health_check():
    """API health check endpoint"""
    try:
        # Test database connection
        supabase = get_supabase_client()
        supabase.table("supermarkets").select("id").limit(1).execute()
        
        # Test cache connection
        redis_client = get_redis_client()
        redis_status = True
        try:
            if redis_client:
                redis_client.ping()
        except:
            redis_status = False
        
        return create_api_response(
            data={
                "status": "healthy",
                "database": "connected",
                "cache": "connected" if redis_status else "disconnected",
                "version": "1.0.0"
            },
            metadata={
                "timestamp": datetime.now().isoformat(),
                "uptime": time.time()
            }
        )
    except Exception as e:
        return create_api_response(
            success=False,
            message="Health check failed",
            data={"error": str(e)}
        )

@app.get("/", response_model=APIResponse)
async def root():
    """API root endpoint with information"""
    return create_api_response(
        data={
            "name": "Price History API",
            "version": "1.0.0",
            "description": "Comprehensive API for supermarket price history data",
            "endpoints": {
                "current_prices": "/products/{product_id}/current-price",
                "price_history": "/products/{product_id}/price-history",
                "price_comparison": "/products/{product_id}/price-comparison",
                "search": "/products/search",
                "analytics": "/analytics/price-trends",
                "documentation": "/docs"
            }
        }
    )

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Price History API",
        version="1.0.0",
        description="Comprehensive API for supermarket price history data with trends, comparisons, and analytics",
        routes=app.routes,
    )
    
    # Add custom tags
    openapi_schema["tags"] = [
        {"name": "Current Prices", "description": "Current price information and availability"},
        {"name": "Price History", "description": "Historical price data and trends"},
        {"name": "Price Comparison", "description": "Cross-supermarket price comparisons"},
        {"name": "Analytics", "description": "Price analytics and market insights"},
        {"name": "Search", "description": "Product search with price information"},
        {"name": "Health", "description": "API health and status endpoints"}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# =============================================================================
# STARTUP AND SHUTDOWN EVENTS
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("Price History API starting up...")
    
    # Warm up cache with common queries
    try:
        supabase = get_supabase_client()
        # Pre-warm some common queries
        supabase.table("supermarkets").select("id, name, slug").limit(20).execute()
        print("Cache warmed up successfully")
    except Exception as e:
        print(f"Cache warm-up failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Price History API shutting down...")
    
    # Close Redis connection if exists
    redis_client = get_redis_client()
    if redis_client:
        try:
            redis_client.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)