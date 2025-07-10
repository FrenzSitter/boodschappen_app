# Price History API

Comprehensive FastAPI application for serving price history data with efficient endpoints for current prices, historical trends, comparisons, and analytics.

## 🚀 Features

- **Current Price Endpoints**: Real-time pricing with cheapest store detection
- **Price History**: Historical data with trends and statistical analysis
- **Price Comparison**: Cross-supermarket comparisons and savings analysis
- **Analytics**: Market trends, deals, and volatility analysis
- **High Performance**: Response caching and optimized queries
- **Comprehensive Documentation**: OpenAPI/Swagger with detailed examples
- **Data Validation**: Pydantic models for request/response validation

## 📋 Requirements

- Python 3.8+
- FastAPI and dependencies
- Supabase database with price history schema
- Redis for caching (optional)

## 🔧 Installation

```bash
# Install dependencies
pip install fastapi uvicorn supabase redis aiohttp pydantic numpy

# Set environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-supabase-key"
export REDIS_URL="redis://localhost:6379"  # Optional
```

## 🎯 Quick Start

```bash
# Start the API server
uvicorn price_history_api:app --reload --host 0.0.0.0 --port 8000

# Access the API documentation
open http://localhost:8000/docs
```

## 📊 API Endpoints

### 1. Current Price Endpoints

#### Get Current Prices
```http
GET /products/{product_id}/current-price
```

**Description**: Get current prices for a product across all supermarkets

**Parameters**:
- `product_id` (path): Product UUID
- `supermarket_ids` (query): Filter by supermarket IDs

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "product": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Melk Halfvol 1L",
        "brand": "Campina",
        "size_text": "1L"
      },
      "supermarket": {
        "id": "456e7890-e89b-12d3-a456-426614174000",
        "name": "Albert Heijn",
        "slug": "albert-heijn"
      },
      "price": 1.49,
      "price_per_unit": 1.49,
      "is_available": true,
      "is_on_sale": false,
      "last_updated": "2025-01-09T10:00:00Z",
      "price_change_24h": -0.10,
      "price_change_percentage_24h": -6.25
    }
  ],
  "metadata": {
    "supermarket_count": 8,
    "available_count": 7,
    "on_sale_count": 2
  }
}
```

#### Find Cheapest Store
```http
GET /products/{product_id}/cheapest-store
```

**Description**: Find the cheapest store for a specific product

**Response**:
```json
{
  "success": true,
  "data": {
    "cheapest_price": { /* CurrentPrice object */ },
    "savings": {
      "amount": 0.45,
      "percentage": 23.1,
      "compared_to": { /* SupermarketInfo object */ }
    },
    "historical_context": {
      "avg_price_30d": 1.65,
      "current_vs_avg": -9.7,
      "price_trend": "down"
    }
  }
}
```

#### Get Supermarket Products
```http
GET /supermarkets/{store_id}/products
```

**Description**: Get all products from a specific supermarket

**Parameters**:
- `store_id` (path): Supermarket UUID
- `page` (query): Page number (default: 1)
- `limit` (query): Items per page (default: 20, max: 100)
- `category` (query): Filter by category
- `on_sale` (query): Filter by sale status
- `min_price`, `max_price` (query): Price range filter

### 2. Price History Endpoints

#### Get Price History
```http
GET /products/{product_id}/price-history
```

**Description**: Get historical price data with trends and statistics

**Parameters**:
- `product_id` (path): Product UUID
- `days` (query): Number of days (default: 30, max: 365)
- `supermarket_ids` (query): Filter by supermarket IDs
- `include_sales` (query): Include sale information

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "product": { /* ProductInfo object */ },
      "supermarket": { /* SupermarketInfo object */ },
      "price_points": [
        {
          "date": "2025-01-09",
          "price": 1.49,
          "is_on_sale": false
        }
      ],
      "statistics": {
        "min_price": 1.35,
        "max_price": 1.65,
        "avg_price": 1.52,
        "volatility": 0.08,
        "data_points": 30
      },
      "trends": {
        "overall_change_percentage": -8.5,
        "overall_direction": "down",
        "volatility_score": 5.2,
        "price_status": "falling"
      }
    }
  ]
}
```

#### Get Price Trends
```http
GET /products/{product_id}/price-trends
```

**Description**: Get price trends for different time periods

**Parameters**:
- `periods` (query): Time periods to analyze (e.g., ["7d", "30d", "90d"])

**Response**:
```json
{
  "success": true,
  "data": {
    "7d": {
      "period": "7d",
      "direction": "down",
      "change_percentage": -5.2,
      "volatility": 3.1,
      "confidence": "high"
    },
    "30d": {
      "period": "30d",
      "direction": "stable",
      "change_percentage": 1.8,
      "volatility": 8.5,
      "confidence": "high"
    }
  }
}
```

#### Get Price Alerts
```http
GET /products/{product_id}/price-alerts
```

**Description**: Get price alerts based on recent changes

**Parameters**:
- `days` (query): Days to check for alerts (default: 7, max: 30)

**Response**:
```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "id": "alert_123",
        "product_id": "123e4567-e89b-12d3-a456-426614174000",
        "supermarket_id": "456e7890-e89b-12d3-a456-426614174000",
        "alert_type": "price_drop",
        "current_price": 1.35,
        "triggered_at": "2025-01-09T10:00:00Z",
        "message": "Price dropped by 15.2% in the last 24 hours"
      }
    ],
    "alert_summary": {
      "total_alerts": 1,
      "price_drops": 1,
      "price_spikes": 0,
      "significant_changes": 3
    }
  }
}
```

### 3. Comparison Endpoints

#### Get Price Comparison
```http
GET /products/{product_id}/price-comparison
```

**Description**: Compare prices across all supermarkets

**Parameters**:
- `include_unavailable` (query): Include unavailable products

**Response**:
```json
{
  "success": true,
  "data": {
    "product": { /* ProductInfo object */ },
    "prices": [ /* Array of CurrentPrice objects */ ],
    "cheapest_store": { /* SupermarketInfo object */ },
    "most_expensive_store": { /* SupermarketInfo object */ },
    "price_range": 0.45,
    "savings_percentage": 23.1,
    "market_position": {
      "percentile_25": 1.42,
      "percentile_50": 1.55,
      "percentile_75": 1.68,
      "price_distribution": {
        "min": 1.35,
        "max": 1.80,
        "mean": 1.56,
        "std": 0.15
      }
    }
  }
}
```

#### Search Products
```http
GET /products/search
```

**Description**: Search products with optional price comparison

**Parameters**:
- `q` (query): Search query (min 2 characters)
- `compare_prices` (query): Include price comparison
- `page`, `limit` (query): Pagination
- `category` (query): Filter by category
- `supermarket_ids` (query): Filter by supermarket IDs

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "product": { /* ProductInfo object */ },
      "current_prices": [ /* Array of CurrentPrice objects */ ],
      "cheapest_price": 1.35,
      "cheapest_store": { /* SupermarketInfo object */ },
      "price_range": 0.45,
      "availability_count": 7
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 156,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

#### Bulk Price Comparison
```http
POST /supermarkets/price-comparison
```

**Description**: Compare prices for multiple products

**Request Body**:
```json
{
  "product_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "234e5678-e89b-12d3-a456-426614174000"
  ],
  "include_unavailable": false
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "comparisons": [
      {
        "product_id": "123e4567-e89b-12d3-a456-426614174000",
        "product_name": "Melk Halfvol 1L",
        "min_price": 1.35,
        "max_price": 1.80,
        "price_range": 0.45,
        "savings_percentage": 25.0,
        "supermarket_count": 8
      }
    ],
    "summary": {
      "total_products": 2,
      "total_savings_available": 0.95,
      "avg_savings_per_product": 0.48,
      "best_overall_savings": 25.0
    }
  }
}
```

### 4. Analytics Endpoints

#### Get Price Trends Analytics
```http
GET /analytics/price-trends
```

**Description**: Get market-wide price trend analytics

**Parameters**:
- `category` (query): Filter by category
- `days` (query): Analysis period (default: 30)
- `supermarket_ids` (query): Filter by supermarket IDs

**Response**:
```json
{
  "success": true,
  "data": {
    "metric_name": "price_trends",
    "value": 12,
    "period": "30d",
    "trend": "stable",
    "context": {
      "market_summary": {
        "overall_direction": "stable",
        "avg_change_percentage": 1.2,
        "products_analyzed": 1250,
        "rising_products": 245,
        "falling_products": 198,
        "volatile_products": 67
      },
      "category_trends": {
        "zuivel-eieren": {
          "product_count": 156,
          "avg_volatility": 8.5,
          "high_volatility_count": 12
        }
      }
    }
  }
}
```

#### Get Top Deals
```http
GET /analytics/top-deals
```

**Description**: Get top deals and discounts

**Parameters**:
- `days` (query): Period to analyze (default: 7)
- `limit` (query): Number of deals (default: 20)
- `min_discount` (query): Minimum discount percentage (default: 20.0)
- `category` (query): Filter by category

**Response**:
```json
{
  "success": true,
  "data": {
    "metric_name": "top_deals",
    "value": 25,
    "period": "7d",
    "context": {
      "deals": [
        {
          "product": { /* ProductInfo object */ },
          "supermarket": { /* SupermarketInfo object */ },
          "current_price": 1.20,
          "original_price": 1.80,
          "discount_percentage": 33.3,
          "savings_amount": 0.60,
          "deal_type": "sale"
        }
      ],
      "summary": {
        "total_deals": 25,
        "current_sales": 18,
        "recent_drops": 7,
        "avg_discount": 28.5
      }
    }
  }
}
```

#### Get Price Volatility Analytics
```http
GET /analytics/price-volatility
```

**Description**: Get price volatility analysis

**Parameters**:
- `days` (query): Analysis period (default: 30)
- `category` (query): Filter by category
- `threshold` (query): Volatility threshold (default: 20.0)

**Response**:
```json
{
  "success": true,
  "data": {
    "metric_name": "price_volatility",
    "value": 45,
    "period": "30d",
    "context": {
      "volatility_distribution": {
        "low": 856,
        "medium": 298,
        "high": 45
      },
      "market_stability": {
        "stability_score": 92.3,
        "total_products": 1199,
        "high_volatility_count": 45,
        "avg_volatility": 6.8
      },
      "category_analysis": {
        "zuivel-eieren": {
          "count": 156,
          "avg_volatility": 8.2,
          "volatility_rate": 12.8
        }
      }
    }
  }
}
```

### 5. System Endpoints

#### Health Check
```http
GET /health
```

**Description**: Check API health and connectivity

**Response**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "database": "connected",
    "cache": "connected",
    "version": "1.0.0"
  }
}
```

#### API Information
```http
GET /
```

**Description**: Get API information and available endpoints

## 🎛️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SUPABASE_URL` | Supabase project URL | - | Yes |
| `SUPABASE_KEY` | Supabase API key | - | Yes |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` | No |
| `CACHE_TTL` | Cache TTL in seconds | `300` | No |
| `DEBUG` | Enable debug mode | `false` | No |
| `RATE_LIMIT` | Rate limit per minute | `100` | No |

### Performance Configuration

```python
# In price_history_api.py
class APIConfig:
    cache_ttl = 300  # 5 minutes default cache
    rate_limit = 100  # requests per minute
    debug = False
```

## 📈 Performance Features

### Response Caching

The API implements intelligent caching:

- **TTL-based caching**: Configurable cache expiration
- **Redis integration**: Distributed caching for scalability
- **Automatic invalidation**: Cache keys based on parameters
- **Fallback caching**: In-memory cache when Redis unavailable

**Cache TTL by endpoint**:
- Current prices: 5 minutes
- Price history: 10 minutes
- Analytics: 15 minutes
- Search results: 5 minutes

### Query Optimization

- **Supabase connection pooling**: Efficient database connections
- **Selective field loading**: Only load required fields
- **Pagination**: Efficient handling of large datasets
- **Index utilization**: Optimized database queries

### Rate Limiting

- **Per-endpoint limits**: Different limits for different endpoints
- **IP-based tracking**: Rate limiting by client IP
- **Graceful degradation**: Proper error responses when limits exceeded

## 🔧 Data Models

### Core Models

```python
class ProductInfo(BaseModel):
    id: UUID4
    name: str
    brand: Optional[str]
    size_text: Optional[str]
    category_name: Optional[str]
    image_url: Optional[str]

class SupermarketInfo(BaseModel):
    id: UUID4
    name: str
    slug: str
    logo_url: Optional[str]
    color_primary: Optional[str]

class CurrentPrice(BaseModel):
    product: ProductInfo
    supermarket: SupermarketInfo
    price: float
    price_per_unit: Optional[float]
    is_available: bool
    is_on_sale: bool
    last_updated: datetime
    price_change_24h: Optional[float]
    price_change_percentage_24h: Optional[float]
```

### Request Models

```python
class PriceHistoryRequest(BaseModel):
    days: int = Field(default=30, ge=1, le=365)
    supermarket_ids: Optional[List[UUID4]]
    include_sales: bool = True

class PriceComparisonRequest(BaseModel):
    product_ids: List[UUID4] = Field(min_items=1, max_items=50)
    supermarket_ids: Optional[List[UUID4]]
    include_unavailable: bool = False
```

### Response Models

```python
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Any
    pagination: Optional[PaginationInfo]
    metadata: Dict[str, Any]
    timestamp: datetime
```

## 📊 Usage Examples

### Basic Usage

```python
import aiohttp
import asyncio

async def get_current_price(product_id: str):
    async with aiohttp.ClientSession() as session:
        url = f"http://localhost:8000/products/{product_id}/current-price"
        async with session.get(url) as response:
            return await response.json()

# Get current prices
result = asyncio.run(get_current_price("123e4567-e89b-12d3-a456-426614174000"))
```

### Search with Price Comparison

```python
async def search_products(query: str):
    async with aiohttp.ClientSession() as session:
        url = "http://localhost:8000/products/search"
        params = {
            "q": query,
            "compare_prices": True,
            "limit": 10
        }
        async with session.get(url, params=params) as response:
            return await response.json()

# Search for milk products
results = asyncio.run(search_products("melk"))
```

### Analytics Dashboard

```python
async def get_market_analytics():
    async with aiohttp.ClientSession() as session:
        # Get price trends
        trends_url = "http://localhost:8000/analytics/price-trends"
        async with session.get(trends_url) as response:
            trends = await response.json()
        
        # Get top deals
        deals_url = "http://localhost:8000/analytics/top-deals"
        async with session.get(deals_url) as response:
            deals = await response.json()
        
        return {"trends": trends, "deals": deals}

# Get market analytics
analytics = asyncio.run(get_market_analytics())
```

## 🧪 Testing

### Run Examples

```bash
# Start the API server
uvicorn price_history_api:app --reload

# Run examples (in another terminal)
python api_examples.py
```

### Manual Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test search endpoint
curl "http://localhost:8000/products/search?q=melk&limit=5"

# Test price comparison
curl http://localhost:8000/products/123e4567-e89b-12d3-a456-426614174000/price-comparison
```

### API Documentation

Visit the interactive documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🚀 Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY price_history_api.py .
COPY price_analysis.py .

EXPOSE 8000

CMD ["uvicorn", "price_history_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Setup

```bash
# Production environment
export SUPABASE_URL="https://your-prod-project.supabase.co"
export SUPABASE_KEY="your-production-service-key"
export REDIS_URL="redis://your-redis-server:6379"
export DEBUG="false"
export CACHE_TTL="600"  # 10 minutes for production
```

### Load Balancing

```nginx
upstream price_api {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name api.yourcompany.com;
    
    location / {
        proxy_pass http://price_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Monitoring

```python
# Add monitoring middleware
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'Request duration')

@app.middleware("http")
async def add_monitoring(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(duration)
    
    return response

@app.get("/metrics")
async def get_metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 🔒 Security

### API Key Authentication (Optional)

```python
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_api_key(token: str = Depends(security)):
    if token.credentials != "your-api-key":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return token

# Apply to endpoints
@app.get("/products/{product_id}/current-price", dependencies=[Depends(verify_api_key)])
async def get_current_price(...):
    ...
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

@app.get("/products/search")
@limiter.limit("10/minute")
async def search_products(request: Request, ...):
    ...
```

## 🚨 Error Handling

### Standard Error Responses

```json
{
  "success": false,
  "message": "Product not found",
  "data": null,
  "metadata": {
    "error_code": "PRODUCT_NOT_FOUND",
    "timestamp": "2025-01-09T10:00:00Z"
  }
}
```

### HTTP Status Codes

- `200`: Success
- `400`: Bad Request (validation errors)
- `404`: Not Found (resource doesn't exist)
- `429`: Too Many Requests (rate limit exceeded)
- `500`: Internal Server Error

## 📋 Changelog

### Version 1.0.0
- Initial release with all core endpoints
- Response caching implementation
- Comprehensive data validation
- OpenAPI documentation
- Performance optimizations

This comprehensive API provides efficient access to price history data with advanced features for comparison, analytics, and real-time monitoring.