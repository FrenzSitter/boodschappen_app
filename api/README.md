# CheckjeBon API

FastAPI application serving Dutch supermarket price comparison data from the CheckjeBon import system.

## 🚀 Features

- **🏪 Supermarket Data** - Complete information about Dutch supermarkets
- **🛒 Product Search** - Full-text search across all products
- **💰 Price Comparison** - Compare prices across multiple supermarkets
- **📊 Price History** - Track price changes over time
- **🏷️ Category Browse** - Browse products by category
- **⚡ High Performance** - Redis caching and optimized queries
- **🔒 Rate Limited** - Prevent abuse with configurable rate limiting
- **📖 Auto Documentation** - OpenAPI/Swagger documentation
- **🐳 Docker Ready** - Complete containerization support

## 📋 API Endpoints

### 🏪 Supermarkets
- `GET /supermarkets` - Get all supermarkets
- `GET /supermarkets/{id}` - Get specific supermarket

### 🛒 Products  
- `GET /products` - Get products (paginated)
- `GET /products/{id}` - Get specific product
- `GET /products/search` - Search products by name
- `GET /products/compare` - Compare prices across supermarkets
- `GET /products/{id}/history` - Get price history

### 🏷️ Categories
- `GET /categories` - Get all categories
- `GET /categories/{id}/products` - Get products in category

### 🔧 System
- `GET /health` - Health check endpoint
- `GET /` - API information

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Redis server
- Supabase account with imported data

### Environment Setup
```bash
# Required environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-supabase-anon-key"

# Optional
export REDIS_URL="redis://localhost:6379"
export DEBUG="false"
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis (if not running)
redis-server

# Run the API
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment
```bash
# Build and deploy
./deploy.sh deploy

# Or step by step
./deploy.sh build
./deploy.sh up
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | **Required** |
| `SUPABASE_KEY` | Supabase API key | **Required** |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `RATE_LIMIT_DEFAULT` | Default rate limit | `100/minute` |
| `CACHE_DEFAULT_TTL` | Default cache TTL | `300` |

### Rate Limiting
- **General endpoints**: 100 requests/minute
- **Search endpoints**: 200 requests/minute  
- **Price comparison**: 100 requests/minute
- **Health check**: Unlimited

### Caching Strategy
- **Supermarkets**: 1 hour TTL
- **Categories**: 2 hours TTL
- **Products**: 30 minutes TTL
- **Search results**: 10 minutes TTL
- **Price comparisons**: 5 minutes TTL

## 📖 API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Example Requests

#### Search Products
```bash
curl "http://localhost:8000/products/search?q=melk&page=1&limit=10"
```

#### Compare Prices
```bash
curl "http://localhost:8000/products/compare?product_name=melk%201L"
```

#### Get Price History
```bash
curl "http://localhost:8000/products/123e4567-e89b-12d3-a456-426614174000/history?days=30"
```

#### Get Products by Category
```bash
curl "http://localhost:8000/categories/123e4567-e89b-12d3-a456-426614174000/products"
```

### Response Format
All endpoints return responses in this format:
```json
{
  "success": true,
  "message": "Request completed successfully",
  "data": { ... },
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "has_more": true
  },
  "timestamp": "2025-01-09T10:00:00Z"
}
```

## 🐳 Docker Deployment

### Docker Compose
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Deployment Commands
```bash
# Full deployment
./deploy.sh deploy

# Build only
./deploy.sh build

# Start containers
./deploy.sh up

# Stop containers
./deploy.sh down

# View logs
./deploy.sh logs

# Health check
./deploy.sh health

# Cleanup
./deploy.sh cleanup
```

## 🔍 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Metrics
- Response times
- Cache hit rates
- Rate limit violations
- Database query performance

### Logging
- Structured logging with timestamps
- Request/response logging
- Error tracking
- Performance metrics

## 🛡️ Security

### Rate Limiting
- IP-based rate limiting
- Configurable per endpoint
- Burst protection

### Input Validation
- Pydantic models for validation
- SQL injection protection
- XSS prevention

### Headers
- Security headers via Nginx
- CORS configuration
- Content-Type validation

## 📊 Performance

### Caching
- Redis-based caching
- Smart cache invalidation
- Configurable TTL per endpoint

### Database
- Optimized Supabase queries
- Connection pooling
- Query result pagination

### Response Optimization
- Gzip compression
- JSON response optimization
- Minimal data transfer

## 🔧 Development

### Project Structure
```
api/
├── main.py              # FastAPI application
├── models.py            # Pydantic models
├── config.py            # Configuration
├── database.py          # Database connections
├── cache.py             # Caching utilities
├── utils.py             # Utility functions
├── requirements.txt     # Dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose
├── nginx.conf          # Nginx configuration
└── deploy.sh           # Deployment script
```

### Adding New Endpoints
1. Define Pydantic models in `models.py`
2. Add endpoint function in `main.py`
3. Add caching logic if needed
4. Update documentation
5. Add tests

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test
pytest tests/test_endpoints.py::test_search_products
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check environment variables
   echo $SUPABASE_URL
   echo $SUPABASE_KEY
   
   # Test connection
   curl -H "Authorization: Bearer $SUPABASE_KEY" $SUPABASE_URL/rest/v1/supermarkets
   ```

2. **Redis Connection Failed**
   ```bash
   # Check Redis status
   redis-cli ping
   
   # Check Redis logs
   docker-compose logs redis
   ```

3. **Rate Limit Exceeded**
   ```bash
   # Check rate limit headers
   curl -I http://localhost:8000/products
   ```

4. **Cache Issues**
   ```bash
   # Clear cache
   redis-cli FLUSHALL
   
   # Check cache stats
   curl http://localhost:8000/health
   ```

### Debug Mode
```bash
# Enable debug mode
export DEBUG=true
uvicorn main:app --reload --log-level debug
```

### Logs
```bash
# View API logs
docker-compose logs api

# View all logs
docker-compose logs

# Follow logs
docker-compose logs -f
```

## 📈 Production Deployment

### Environment Setup
```bash
# Production environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-production-key"
export REDIS_URL="redis://production-redis:6379"
export DEBUG="false"
export LOG_LEVEL="INFO"
```

### SSL Configuration
1. Obtain SSL certificates
2. Place in `ssl/` directory
3. Update `nginx.conf` paths
4. Deploy with HTTPS

### Scaling
```bash
# Scale API containers
docker-compose up -d --scale api=3

# Use load balancer
# Configure Nginx upstream
```

### Monitoring
- Set up monitoring (Prometheus/Grafana)
- Configure alerts
- Monitor cache hit rates
- Track API performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the logs: `docker-compose logs`
2. Review the health endpoint: `/health`
3. Check the documentation: `/docs`
4. Verify environment variables
5. Test database connectivity

## 📊 API Statistics

Current API capabilities:
- **95,289+** products from CheckjeBon data
- **11** Dutch supermarkets
- **12** product categories
- **Sub-second** response times
- **99.9%** uptime target

## 🎯 Future Enhancements

Planned features:
- **Authentication** - API key management
- **Webhooks** - Real-time price alerts
- **GraphQL** - Flexible query API
- **Analytics** - Usage analytics
- **Mobile SDK** - Mobile app integration
- **Bulk Operations** - Batch API endpoints

This FastAPI application provides a production-ready API for accessing Dutch supermarket price comparison data with high performance, comprehensive documentation, and easy deployment.