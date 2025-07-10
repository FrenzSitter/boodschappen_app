# Price Analysis Module

Comprehensive Python module for analyzing price history data from CheckjeBon imports with advanced analytics, comparisons, and reporting capabilities.

## 🚀 Features

- **Price Trend Analysis**: Calculate price changes, volatility, and seasonal patterns
- **Cross-Supermarket Comparisons**: Compare prices across different stores
- **Automated Alerts**: Price drop/spike detection with configurable thresholds
- **Comprehensive Reporting**: Generate detailed reports and export data
- **API Integration**: Format data for frontend consumption with caching
- **Performance Optimized**: Built-in caching and efficient database queries

## 📋 Requirements

- Python 3.8+
- Supabase database with price history schema
- NumPy and Pandas for statistical analysis

## 🔧 Installation

```bash
pip install -r requirements.txt
```

Required dependencies:
- `supabase>=1.0.0`
- `numpy>=1.24.0`
- `pandas>=2.0.0`
- `postgrest>=0.10.0`

## 🎯 Quick Start

```python
from price_analysis import create_analyzer

# Create analyzer instance
analyzer = create_analyzer(
    supabase_url="https://your-project.supabase.co",
    supabase_key="your-supabase-key"
)

# Get price trends
trends = analyzer.get_price_trends(days=30)

# Check for alerts
alerts = analyzer.check_price_alerts()

# Compare current prices
comparisons = analyzer.compare_current_prices()
```

## 📊 Core Functions

### 1. Price Trend Analysis

#### `get_price_trends(product_id=None, supermarket_id=None, days=30)`
Calculate price trends over time with volatility analysis.

```python
# Get trends for all products
trends = analyzer.get_price_trends(days=30)

# Get trends for specific product
trends = analyzer.get_price_trends(product_id="123", days=60)

# Get trends for specific supermarket
trends = analyzer.get_price_trends(supermarket_id="456", days=30)
```

**Returns**: List of `PriceTrend` objects with:
- Price changes (amount and percentage)
- Volatility calculations
- Min/max/average prices
- Data point counts

#### `get_price_volatility(product_id=None, days=30)`
Analyze price volatility with classifications.

```python
volatility_data = analyzer.get_price_volatility(days=30)

# Results include volatility classification: low, medium, high
for item in volatility_data:
    print(f"{item['product_name']}: {item['volatility_class']} ({item['volatility']:.2f}%)")
```

#### `detect_seasonal_patterns(product_id, years=2)`
Detect seasonal price patterns over multiple years.

```python
seasonal_data = analyzer.detect_seasonal_patterns(product_id="123", years=2)

print(f"Peak season: Month {seasonal_data['peak_season']['month']}")
print(f"Low season: Month {seasonal_data['low_season']['month']}")
```

#### `detect_significant_changes(days=7, threshold=15.0)`
Find significant price changes in recent period.

```python
changes = analyzer.detect_significant_changes(days=7, threshold=20.0)

for change in changes:
    print(f"{change['product_name']}: {change['change_percentage']:.2f}%")
```

### 2. Comparison Functions

#### `compare_current_prices(product_id=None, category_id=None)`
Compare current prices across supermarkets.

```python
# Compare all products
comparisons = analyzer.compare_current_prices()

# Compare specific category
comparisons = analyzer.compare_current_prices(category_id="dairy")

for comp in comparisons:
    print(f"{comp.product_name}: €{comp.price_range:.2f} range")
    print(f"Cheapest: {comp.cheapest_store}")
```

#### `compare_historical_prices(product_id, days=30)`
Compare historical prices for a product across stores.

```python
historical = analyzer.compare_historical_prices(product_id="123", days=90)

print(f"Best store: {historical['best_store']['supermarket_name']}")
print(f"Price spread: €{historical['price_spread']:.2f}")
```

#### `get_price_ranges(category_id=None, days=30)`
Get price ranges (min/max/avg) for products.

```python
ranges = analyzer.get_price_ranges(category_id="dairy", days=30)

for item in ranges:
    print(f"{item['product_name']}: €{item['min_price']:.2f} - €{item['max_price']:.2f}")
```

#### `find_cheapest_stores(product_id=None, days=30)`
Find cheapest stores for products over time.

```python
cheapest = analyzer.find_cheapest_stores(days=30)

for store in cheapest:
    print(f"{store['product_name']}: {store['cheapest_store_name']}")
    print(f"Savings: €{store['savings_amount']:.2f} ({store['savings_percentage']:.1f}%)")
```

### 3. Alert Functions

#### `check_price_alerts(drop_threshold=15.0, spike_threshold=25.0)`
Check for price alerts based on recent changes.

```python
alerts = analyzer.check_price_alerts(drop_threshold=20.0, spike_threshold=30.0)

for alert in alerts:
    print(f"{alert.product_name}: {alert.alert_type}")
    print(f"Change: {alert.change_percentage:.2f}%")
    print(f"Severity: {alert.severity}")
```

**Alert Types**:
- `price_drop`: Significant price decrease
- `price_spike`: Significant price increase

**Severity Levels**:
- `low`: Basic threshold exceeded
- `medium`: 1.5x threshold exceeded
- `high`: 2x threshold exceeded

#### `detect_new_products(days=7)`
Detect new products added recently.

```python
new_products = analyzer.detect_new_products(days=7)

for product in new_products:
    print(f"New: {product['product_name']} ({product['brand']})")
```

#### `find_store_specific_deals(supermarket_id, discount_threshold=20.0)`
Find deals specific to a store.

```python
deals = analyzer.find_store_specific_deals(supermarket_id="123", discount_threshold=25.0)

for deal in deals:
    print(f"{deal['product_name']}: {deal['discount_percentage']:.1f}% off")
    print(f"Price: €{deal['current_price']:.2f} (was €{deal['original_price']:.2f})")
```

### 4. Reporting Functions

#### `generate_price_history_report(product_id, days=90)`
Generate comprehensive price history report.

```python
report = analyzer.generate_price_history_report(product_id="123", days=90)

print(f"Product: {report['product_info']['name']}")
print(f"Stores tracking: {report['summary']['total_stores_tracking']}")
print(f"Most volatile store: {report['summary']['most_volatile_store']}")
```

#### `export_data_for_visualization(product_id=None, days=30, format="json")`
Export data for visualization tools.

```python
# Export as JSON
viz_data = analyzer.export_data_for_visualization(days=30, format="json")

# Export as CSV
csv_data = analyzer.export_data_for_visualization(days=30, format="csv")
```

#### `get_summary_statistics(days=30)`
Get comprehensive summary statistics.

```python
summary = analyzer.get_summary_statistics(days=30)

print(f"Total products: {summary['basic_stats']['total_products']}")
print(f"Price changes: {summary['basic_stats']['price_changes']}")
print(f"Average change: {summary['price_change_stats']['avg_change_percentage']:.2f}%")
```

### 5. API Helper Functions

#### `format_for_api(data, include_metadata=True)`
Format data for API consumption.

```python
trends = analyzer.get_price_trends(days=30)
api_response = analyzer.format_for_api(trends)

# Returns structured response with success/error status
{
    "success": True,
    "data": [...],
    "metadata": {
        "generated_at": "2025-01-09T10:00:00",
        "cache_ttl": 300
    }
}
```

#### `paginate_results(data, page=1, limit=50)`
Paginate results for API responses.

```python
trends = analyzer.get_price_trends(days=30)
paginated = analyzer.paginate_results(trends, page=1, limit=10)

# Returns paginated response with metadata
{
    "data": [...],
    "pagination": {
        "page": 1,
        "limit": 10,
        "total": 100,
        "pages": 10,
        "has_next": True,
        "has_prev": False
    }
}
```

## ⚙️ Configuration

Configure analysis behavior with `AnalysisConfig`:

```python
from price_analysis import AnalysisConfig, create_analyzer

config = AnalysisConfig(
    cache_ttl=600,  # 10 minutes cache
    max_results=500,
    default_days=30,
    
    # Volatility thresholds
    low_volatility_threshold=5.0,
    high_volatility_threshold=20.0,
    
    # Alert thresholds
    price_drop_threshold=15.0,
    price_spike_threshold=25.0,
    
    # Seasonal analysis
    seasonal_window_days=365,
    seasonal_min_data_points=50
)

analyzer = create_analyzer(supabase_url, supabase_key, config)
```

## 🚀 Performance & Caching

### Built-in Caching
All functions include intelligent caching:

```python
# Cache management
analyzer.get_cache_stats()  # View cache statistics
analyzer.clear_cache()      # Clear all cached data

# Cache is automatically managed based on TTL
```

### Cache Decorator
Functions are automatically cached using the `@cache_result()` decorator:

```python
@cache_result(ttl=300)  # 5 minute cache
def expensive_analysis():
    # Results cached for 5 minutes
    pass
```

## 📈 Data Structures

### PriceTrend
```python
@dataclass
class PriceTrend:
    product_id: str
    product_name: str
    supermarket_id: str
    supermarket_name: str
    start_date: date
    end_date: date
    start_price: float
    end_price: float
    price_change: float
    price_change_percentage: float
    avg_price: float
    min_price: float
    max_price: float
    volatility: float
    data_points: int
```

### PriceComparison
```python
@dataclass
class PriceComparison:
    product_id: str
    product_name: str
    comparison_date: date
    prices: List[Dict[str, Any]]
    cheapest_store: str
    most_expensive_store: str
    price_range: float
    avg_price: float
    std_deviation: float
```

### PriceAlert
```python
@dataclass
class PriceAlert:
    alert_id: str
    product_id: str
    product_name: str
    supermarket_id: str
    supermarket_name: str
    alert_type: str
    current_price: float
    previous_price: float
    change_percentage: float
    alert_date: datetime
    severity: str
```

## 🔧 Usage Examples

### Basic Analysis Workflow

```python
from price_analysis import create_analyzer

# Initialize
analyzer = create_analyzer(supabase_url, supabase_key)

# 1. Get overview
summary = analyzer.get_summary_statistics(days=30)
print(f"Analyzing {summary['basic_stats']['total_products']} products")

# 2. Find volatile products
volatility = analyzer.get_price_volatility(days=30)
high_volatility = [p for p in volatility if p['volatility_class'] == 'high']

# 3. Check for alerts
alerts = analyzer.check_price_alerts()
price_drops = [a for a in alerts if a.alert_type == 'price_drop']

# 4. Find best deals
cheapest_stores = analyzer.find_cheapest_stores(days=30)
best_savings = cheapest_stores[:10]

# 5. Compare prices
comparisons = analyzer.compare_current_prices()
biggest_differences = sorted(comparisons, key=lambda x: x.price_range, reverse=True)[:5]
```

### API Integration Example

```python
from flask import Flask, jsonify, request
from price_analysis import create_analyzer

app = Flask(__name__)
analyzer = create_analyzer(supabase_url, supabase_key)

@app.route('/api/trends')
def get_trends():
    days = request.args.get('days', 30, type=int)
    product_id = request.args.get('product_id')
    
    trends = analyzer.get_price_trends(product_id=product_id, days=days)
    return jsonify(analyzer.format_for_api(trends))

@app.route('/api/alerts')
def get_alerts():
    alerts = analyzer.check_price_alerts()
    return jsonify(analyzer.format_for_api(alerts))

@app.route('/api/compare')
def compare_prices():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    
    comparisons = analyzer.compare_current_prices()
    paginated = analyzer.paginate_results(comparisons, page, limit)
    
    return jsonify(analyzer.format_for_api(paginated))
```

### Seasonal Analysis Example

```python
# Analyze seasonal patterns for dairy products
dairy_trends = analyzer.get_price_trends(category_id="dairy", days=365)

for trend in dairy_trends:
    seasonal_data = analyzer.detect_seasonal_patterns(trend.product_id, years=2)
    
    if 'error' not in seasonal_data:
        print(f"{trend.product_name}:")
        print(f"  Peak season: Month {seasonal_data['peak_season']['month']}")
        print(f"  Low season: Month {seasonal_data['low_season']['month']}")
        print(f"  Seasonal variation: €{seasonal_data['seasonal_variation']:.2f}")
```

## 🛠️ Advanced Features

### Custom Alert Rules
```python
# Define custom alert logic
def check_custom_alerts(analyzer):
    trends = analyzer.get_price_trends(days=7)
    
    custom_alerts = []
    for trend in trends:
        # Alert if price increased >30% in a week
        if trend.price_change_percentage > 30:
            custom_alerts.append({
                'product': trend.product_name,
                'change': trend.price_change_percentage,
                'type': 'weekly_spike'
            })
    
    return custom_alerts
```

### Bulk Analysis
```python
# Analyze multiple products efficiently
product_ids = ["123", "456", "789"]
results = {}

for product_id in product_ids:
    results[product_id] = {
        'trends': analyzer.get_price_trends(product_id=product_id, days=30),
        'comparison': analyzer.compare_historical_prices(product_id, days=30),
        'seasonal': analyzer.detect_seasonal_patterns(product_id, years=1)
    }
```

### Export for Data Science
```python
# Export data for machine learning
viz_data = analyzer.export_data_for_visualization(days=365, format="json")

# Convert to pandas DataFrame
import pandas as pd
df = pd.DataFrame(viz_data['data'])

# Analyze with pandas
price_correlations = df.pivot_table(
    index='date', 
    columns='supermarket_name', 
    values='price'
).corr()
```

## 🚨 Error Handling

All functions include comprehensive error handling:

```python
try:
    trends = analyzer.get_price_trends(days=30)
except Exception as e:
    print(f"Error analyzing trends: {e}")

# Functions return error dictionaries when appropriate
seasonal_data = analyzer.detect_seasonal_patterns(product_id="invalid")
if 'error' in seasonal_data:
    print(f"Analysis failed: {seasonal_data['error']}")
```

## 📊 Performance Tips

1. **Use caching effectively**:
   ```python
   # Cache is automatically managed, but you can control it
   analyzer.clear_cache()  # Clear when data changes
   ```

2. **Batch similar queries**:
   ```python
   # Get all trends at once, then filter
   all_trends = analyzer.get_price_trends(days=30)
   product_trends = [t for t in all_trends if t.product_id == "123"]
   ```

3. **Use appropriate time windows**:
   ```python
   # Shorter windows for real-time analysis
   recent_alerts = analyzer.check_price_alerts()
   
   # Longer windows for trend analysis
   long_term_trends = analyzer.get_price_trends(days=365)
   ```

## 🔍 Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all function calls will be logged
analyzer = create_analyzer(supabase_url, supabase_key)
```

## 📝 Examples

Run the examples file to see all functions in action:

```bash
python price_analysis_examples.py
```

This comprehensive module provides everything needed for sophisticated price analysis of your CheckjeBon supermarket data with high performance and easy integration.