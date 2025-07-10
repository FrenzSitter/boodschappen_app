#!/usr/bin/env python3
"""
Price History API Examples
==========================

Comprehensive examples demonstrating how to use the price history API
endpoints with various scenarios and use cases.
"""

import asyncio
import json
from datetime import datetime, timedelta
import aiohttp
from typing import Dict, List, Any

# Configuration
API_BASE_URL = "http://localhost:8000"

class PriceHistoryAPIClient:
    """Client for interacting with the Price History API"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get(self, endpoint: str, params: Dict = None) -> Dict:
        """Make GET request to API"""
        url = f"{self.base_url}{endpoint}"
        async with self.session.get(url, params=params) as response:
            return await response.json()
    
    async def post(self, endpoint: str, data: Dict = None) -> Dict:
        """Make POST request to API"""
        url = f"{self.base_url}{endpoint}"
        async with self.session.post(url, json=data) as response:
            return await response.json()

async def example_current_prices():
    """Example: Get current prices for a product"""
    print("=== Current Prices Example ===")
    
    async with PriceHistoryAPIClient() as client:
        # Get current prices for a product
        # (You'll need to replace with actual product ID from your database)
        product_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = await client.get(f"/products/{product_id}/current-price")
        
        if response.get("success"):
            prices = response["data"]
            print(f"Found {len(prices)} current prices")
            
            for price in prices:
                print(f"- {price['supermarket']['name']}: €{price['price']:.2f}")
                if price['is_on_sale']:
                    print(f"  ON SALE: {price['discount_percentage']:.1f}% off")
                if price['price_change_24h']:
                    change = price['price_change_percentage_24h']
                    direction = "↑" if change > 0 else "↓" if change < 0 else "→"
                    print(f"  24h change: {direction} {change:.1f}%")
        else:
            print(f"Error: {response.get('message')}")

async def example_cheapest_store():
    """Example: Find cheapest store for a product"""
    print("=== Cheapest Store Example ===")
    
    async with PriceHistoryAPIClient() as client:
        product_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = await client.get(f"/products/{product_id}/cheapest-store")
        
        if response.get("success"):
            data = response["data"]
            cheapest = data["cheapest_price"]
            savings = data["savings"]
            
            print(f"Cheapest store: {cheapest['supermarket']['name']}")
            print(f"Price: €{cheapest['price']:.2f}")
            print(f"Savings: €{savings['amount']:.2f} ({savings['percentage']:.1f}%)")
            print(f"Compared to: {savings['compared_to']['name']}")
            
            # Historical context
            context = data["historical_context"]
            print(f"30-day average: €{context['avg_price_30d']:.2f}")
            print(f"Current vs average: {context['current_vs_avg']:.1f}%")
            print(f"Price trend: {context['price_trend']}")
        else:
            print(f"Error: {response.get('message')}")

async def example_supermarket_products():
    """Example: Get products from a supermarket"""
    print("=== Supermarket Products Example ===")
    
    async with PriceHistoryAPIClient() as client:
        supermarket_id = "456e7890-e89b-12d3-a456-426614174000"
        
        params = {
            "page": 1,
            "limit": 10,
            "on_sale": True,
            "min_price": 1.0,
            "max_price": 10.0
        }
        
        response = await client.get(f"/supermarkets/{supermarket_id}/products", params=params)
        
        if response.get("success"):
            products = response["data"]
            pagination = response["pagination"]
            
            print(f"Found {pagination['total']} products (showing {len(products)})")
            
            for product in products:
                print(f"- {product['product']['name']}")
                print(f"  Price: €{product['price']:.2f}")
                if product['is_on_sale']:
                    print(f"  SALE: {product['discount_percentage']:.1f}% off")
                if product['product']['brand']:
                    print(f"  Brand: {product['product']['brand']}")
                print()
        else:
            print(f"Error: {response.get('message')}")

async def example_price_history():
    """Example: Get price history for a product"""
    print("=== Price History Example ===")
    
    async with PriceHistoryAPIClient() as client:
        product_id = "123e4567-e89b-12d3-a456-426614174000"
        
        params = {
            "days": 30,
            "include_sales": True
        }
        
        response = await client.get(f"/products/{product_id}/price-history", params=params)
        
        if response.get("success"):
            histories = response["data"]
            
            print(f"Price history for {len(histories)} supermarkets")
            
            for history in histories:
                supermarket = history["supermarket"]["name"]
                stats = history["statistics"]
                trends = history["trends"]
                
                print(f"\n{supermarket}:")
                print(f"  Price range: €{stats['min_price']:.2f} - €{stats['max_price']:.2f}")
                print(f"  Average: €{stats['avg_price']:.2f}")
                print(f"  Volatility: {stats['volatility']:.2f}")
                print(f"  Overall trend: {trends['overall_direction']} ({trends['overall_change_percentage']:.1f}%)")
                print(f"  Price status: {trends['price_status']}")
                
                # Show recent price points
                recent_points = history["price_points"][-5:]  # Last 5 days
                print("  Recent prices:")
                for point in recent_points:
                    sale_info = " (ON SALE)" if point["is_on_sale"] else ""
                    print(f"    {point['date']}: €{point['price']:.2f}{sale_info}")
        else:
            print(f"Error: {response.get('message')}")

async def example_price_trends():
    """Example: Get price trends for different periods"""
    print("=== Price Trends Example ===")
    
    async with PriceHistoryAPIClient() as client:
        product_id = "123e4567-e89b-12d3-a456-426614174000"
        
        params = {
            "periods": ["7d", "30d", "90d"]
        }
        
        response = await client.get(f"/products/{product_id}/price-trends", params=params)
        
        if response.get("success"):
            trends = response["data"]
            
            print("Price trends analysis:")
            
            for period, trend in trends.items():
                print(f"\n{period}:")
                print(f"  Direction: {trend['direction']}")
                print(f"  Change: {trend['change_percentage']:.2f}%")
                print(f"  Volatility: {trend['volatility']:.2f}%")
                print(f"  Confidence: {trend['confidence']}")
        else:
            print(f"Error: {response.get('message')}")

async def example_price_alerts():
    """Example: Get price alerts for a product"""
    print("=== Price Alerts Example ===")
    
    async with PriceHistoryAPIClient() as client:
        product_id = "123e4567-e89b-12d3-a456-426614174000"
        
        params = {"days": 7}
        
        response = await client.get(f"/products/{product_id}/price-alerts", params=params)
        
        if response.get("success"):
            data = response["data"]
            alerts = data["alerts"]
            summary = data["alert_summary"]
            
            print(f"Found {summary['total_alerts']} alerts")
            print(f"Price drops: {summary['price_drops']}")
            print(f"Price spikes: {summary['price_spikes']}")
            print(f"Significant changes: {summary['significant_changes']}")
            
            if alerts:
                print("\nAlerts:")
                for alert in alerts:
                    print(f"- {alert['alert_type'].upper()}: {alert['message']}")
                    print(f"  Current price: €{alert['current_price']:.2f}")
                    print(f"  Triggered: {alert['triggered_at']}")
            
            # Show recent changes
            recent_changes = data.get("recent_changes", [])
            if recent_changes:
                print("\nRecent significant changes:")
                for change in recent_changes:
                    print(f"- {change['product_name']} at {change['supermarket_name']}")
                    print(f"  {change['change_type']}: {change['change_percentage']:.1f}%")
        else:
            print(f"Error: {response.get('message')}")

async def example_price_comparison():
    """Example: Compare prices for a product"""
    print("=== Price Comparison Example ===")
    
    async with PriceHistoryAPIClient() as client:
        product_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = await client.get(f"/products/{product_id}/price-comparison")
        
        if response.get("success"):
            comparison = response["data"]
            
            print(f"Price comparison for: {comparison['product']['name']}")
            print(f"Cheapest store: {comparison['cheapest_store']['name']}")
            print(f"Most expensive store: {comparison['most_expensive_store']['name']}")
            print(f"Price range: €{comparison['price_range']:.2f}")
            print(f"Savings opportunity: {comparison['savings_percentage']:.1f}%")
            
            # Market position
            market = comparison["market_position"]
            print(f"\nMarket position:")
            print(f"  25th percentile: €{market['percentile_25']:.2f}")
            print(f"  Median: €{market['percentile_50']:.2f}")
            print(f"  75th percentile: €{market['percentile_75']:.2f}")
            
            # Show all prices
            print(f"\nAll prices:")
            for price in comparison["prices"]:
                status = "⚠ UNAVAILABLE" if not price["is_available"] else "✓ Available"
                sale = f" (SALE: {price['discount_percentage']:.1f}% off)" if price["is_on_sale"] else ""
                print(f"  {price['supermarket']['name']}: €{price['price']:.2f} {status}{sale}")
        else:
            print(f"Error: {response.get('message')}")

async def example_product_search():
    """Example: Search for products with price comparison"""
    print("=== Product Search Example ===")
    
    async with PriceHistoryAPIClient() as client:
        params = {
            "q": "melk",
            "compare_prices": True,
            "page": 1,
            "limit": 5
        }
        
        response = await client.get("/products/search", params=params)
        
        if response.get("success"):
            results = response["data"]
            pagination = response["pagination"]
            
            print(f"Found {pagination['total']} products (showing {len(results)})")
            
            for result in results:
                product = result["product"]
                print(f"\n{product['name']}")
                if product['brand']:
                    print(f"  Brand: {product['brand']}")
                
                print(f"  Cheapest: €{result['cheapest_price']:.2f} at {result['cheapest_store']['name']}")
                print(f"  Price range: €{result['price_range']:.2f}")
                print(f"  Available at: {result['availability_count']} stores")
                
                # Show price comparison
                if len(result["current_prices"]) > 1:
                    print("  All prices:")
                    for price in result["current_prices"]:
                        print(f"    {price['supermarket']['name']}: €{price['price']:.2f}")
        else:
            print(f"Error: {response.get('message')}")

async def example_bulk_price_comparison():
    """Example: Bulk price comparison for multiple products"""
    print("=== Bulk Price Comparison Example ===")
    
    async with PriceHistoryAPIClient() as client:
        # Multiple product IDs
        product_ids = [
            "123e4567-e89b-12d3-a456-426614174000",
            "234e5678-e89b-12d3-a456-426614174000",
            "345e6789-e89b-12d3-a456-426614174000"
        ]
        
        data = {
            "product_ids": product_ids,
            "include_unavailable": False
        }
        
        response = await client.post("/supermarkets/price-comparison", data=data)
        
        if response.get("success"):
            data = response["data"]
            comparisons = data["comparisons"]
            summary = data["summary"]
            
            print(f"Bulk comparison for {summary['total_products']} products")
            print(f"Total savings available: €{summary['total_savings_available']:.2f}")
            print(f"Average savings per product: €{summary['avg_savings_per_product']:.2f}")
            
            print("\nProduct comparisons:")
            for comp in comparisons:
                print(f"- {comp['product_name']}")
                print(f"  Price range: €{comp['min_price']:.2f} - €{comp['max_price']:.2f}")
                print(f"  Savings: €{comp['price_range']:.2f} ({comp['savings_percentage']:.1f}%)")
                print(f"  Available at: {comp['supermarket_count']} stores")
        else:
            print(f"Error: {response.get('message')}")

async def example_analytics_price_trends():
    """Example: Get analytics for price trends"""
    print("=== Analytics Price Trends Example ===")
    
    async with PriceHistoryAPIClient() as client:
        params = {
            "days": 30,
            "category": "zuivel-eieren"
        }
        
        response = await client.get("/analytics/price-trends", params=params)
        
        if response.get("success"):
            analytics = response["data"]
            context = analytics["context"]
            
            print(f"Price trends analytics ({analytics['period']})")
            print(f"Overall trend: {analytics['trend']}")
            
            # Market summary
            market = context["market_summary"]
            print(f"\nMarket summary:")
            print(f"  Overall direction: {market['overall_direction']}")
            print(f"  Average change: {market['avg_change_percentage']:.2f}%")
            print(f"  Products analyzed: {market['products_analyzed']}")
            print(f"  Rising products: {market['rising_products']}")
            print(f"  Falling products: {market['falling_products']}")
            print(f"  Volatile products: {market['volatile_products']}")
            
            # Category trends
            category_trends = context["category_trends"]
            print(f"\nCategory trends:")
            for category, trend in category_trends.items():
                print(f"  {category}:")
                print(f"    Products: {trend['product_count']}")
                print(f"    Avg volatility: {trend['avg_volatility']:.2f}%")
                print(f"    High volatility: {trend['high_volatility_count']}")
        else:
            print(f"Error: {response.get('message')}")

async def example_analytics_top_deals():
    """Example: Get top deals analytics"""
    print("=== Analytics Top Deals Example ===")
    
    async with PriceHistoryAPIClient() as client:
        params = {
            "days": 7,
            "limit": 10,
            "min_discount": 25.0
        }
        
        response = await client.get("/analytics/top-deals", params=params)
        
        if response.get("success"):
            analytics = response["data"]
            context = analytics["context"]
            deals = context["deals"]
            summary = context["summary"]
            
            print(f"Top deals analysis ({analytics['period']})")
            print(f"Total deals found: {summary['total_deals']}")
            print(f"Current sales: {summary['current_sales']}")
            print(f"Recent price drops: {summary['recent_drops']}")
            print(f"Average discount: {summary['avg_discount']:.1f}%")
            
            print(f"\nTop deals:")
            for deal in deals[:5]:  # Show top 5
                if deal['deal_type'] == 'sale':
                    print(f"- {deal['product']['name']} at {deal['supermarket']['name']}")
                    print(f"  Price: €{deal['current_price']:.2f} (was €{deal['original_price']:.2f})")
                    print(f"  Discount: {deal['discount_percentage']:.1f}%")
                elif deal['deal_type'] == 'price_drop':
                    print(f"- {deal['product']['name']} at {deal['supermarket']['name']}")
                    print(f"  New price: €{deal['current_price']:.2f}")
                    print(f"  Price drop: {deal['change_percentage']:.1f}%")
                print()
        else:
            print(f"Error: {response.get('message')}")

async def example_analytics_volatility():
    """Example: Get price volatility analytics"""
    print("=== Analytics Volatility Example ===")
    
    async with PriceHistoryAPIClient() as client:
        params = {
            "days": 30,
            "threshold": 20.0
        }
        
        response = await client.get("/analytics/price-volatility", params=params)
        
        if response.get("success"):
            analytics = response["data"]
            context = analytics["context"]
            
            print(f"Price volatility analytics ({analytics['period']})")
            print(f"High volatility products: {analytics['value']}")
            
            # Market stability
            stability = context["market_stability"]
            print(f"\nMarket stability:")
            print(f"  Stability score: {stability['stability_score']:.1f}%")
            print(f"  Total products: {stability['total_products']}")
            print(f"  High volatility: {stability['high_volatility_count']}")
            print(f"  Average volatility: {stability['avg_volatility']:.2f}%")
            
            # Volatility distribution
            distribution = context["volatility_distribution"]
            print(f"\nVolatility distribution:")
            print(f"  Low volatility: {distribution['low']} products")
            print(f"  Medium volatility: {distribution['medium']} products")
            print(f"  High volatility: {distribution['high']} products")
            
            # Category analysis
            category_analysis = context["category_analysis"]
            print(f"\nCategory analysis:")
            for category, data in list(category_analysis.items())[:3]:  # Show top 3
                print(f"  {category}:")
                print(f"    Products: {data['count']}")
                print(f"    Avg volatility: {data['avg_volatility']:.2f}%")
                print(f"    High volatility rate: {data['volatility_rate']:.1f}%")
        else:
            print(f"Error: {response.get('message')}")

async def example_health_check():
    """Example: Check API health"""
    print("=== Health Check Example ===")
    
    async with PriceHistoryAPIClient() as client:
        response = await client.get("/health")
        
        if response.get("success"):
            health = response["data"]
            print(f"API Status: {health['status']}")
            print(f"Database: {health['database']}")
            print(f"Cache: {health['cache']}")
            print(f"Version: {health['version']}")
        else:
            print(f"API Health Check Failed: {response.get('message')}")

async def example_pagination():
    """Example: Demonstrate pagination"""
    print("=== Pagination Example ===")
    
    async with PriceHistoryAPIClient() as client:
        supermarket_id = "456e7890-e89b-12d3-a456-426614174000"
        
        # First page
        params = {"page": 1, "limit": 5}
        response = await client.get(f"/supermarkets/{supermarket_id}/products", params=params)
        
        if response.get("success"):
            products = response["data"]
            pagination = response["pagination"]
            
            print(f"Page {pagination['page']} of {pagination['pages']}")
            print(f"Total products: {pagination['total']}")
            print(f"Showing {len(products)} products")
            
            print("\nProducts:")
            for product in products:
                print(f"- {product['product']['name']}: €{product['price']:.2f}")
            
            # Show pagination info
            print(f"\nPagination:")
            print(f"  Has next page: {pagination['has_next']}")
            print(f"  Has previous page: {pagination['has_prev']}")
            
            # Get next page if available
            if pagination['has_next']:
                params["page"] = 2
                response = await client.get(f"/supermarkets/{supermarket_id}/products", params=params)
                
                if response.get("success"):
                    next_products = response["data"]
                    print(f"\nNext page ({len(next_products)} products):")
                    for product in next_products:
                        print(f"- {product['product']['name']}: €{product['price']:.2f}")
        else:
            print(f"Error: {response.get('message')}")

async def example_filtering():
    """Example: Demonstrate filtering options"""
    print("=== Filtering Example ===")
    
    async with PriceHistoryAPIClient() as client:
        supermarket_id = "456e7890-e89b-12d3-a456-426614174000"
        
        # Filter by price range and sale status
        params = {
            "page": 1,
            "limit": 10,
            "on_sale": True,
            "min_price": 2.0,
            "max_price": 5.0
        }
        
        response = await client.get(f"/supermarkets/{supermarket_id}/products", params=params)
        
        if response.get("success"):
            products = response["data"]
            metadata = response["metadata"]
            
            print(f"Products on sale between €2.00 - €5.00:")
            print(f"Found {len(products)} products")
            
            filters = metadata["filters_applied"]
            print(f"Filters applied: {filters}")
            
            for product in products:
                print(f"- {product['product']['name']}")
                print(f"  Price: €{product['price']:.2f}")
                print(f"  Discount: {product['discount_percentage']:.1f}%")
                print(f"  Was: €{product['original_price']:.2f}")
                print()
        else:
            print(f"Error: {response.get('message')}")

async def example_real_time_monitoring():
    """Example: Real-time price monitoring"""
    print("=== Real-time Monitoring Example ===")
    
    async with PriceHistoryAPIClient() as client:
        product_id = "123e4567-e89b-12d3-a456-426614174000"
        
        # Monitor price changes every 30 seconds
        for i in range(3):  # Run 3 iterations for demo
            print(f"\n--- Monitoring Cycle {i+1} ---")
            
            # Get current prices
            response = await client.get(f"/products/{product_id}/current-price")
            
            if response.get("success"):
                prices = response["data"]
                
                print(f"Current prices ({len(prices)} stores):")
                for price in prices:
                    change_indicator = ""
                    if price['price_change_percentage_24h']:
                        change = price['price_change_percentage_24h']
                        if abs(change) > 0.1:
                            change_indicator = f" ({change:+.1f}%)"
                    
                    print(f"  {price['supermarket']['name']}: €{price['price']:.2f}{change_indicator}")
                
                # Check for alerts
                alert_response = await client.get(f"/products/{product_id}/price-alerts")
                if alert_response.get("success"):
                    alerts = alert_response["data"]["alerts"]
                    if alerts:
                        print(f"  ⚠ {len(alerts)} active alerts")
                    else:
                        print("  ✓ No alerts")
            
            # Wait before next check (in real scenario, you'd use proper scheduling)
            if i < 2:
                print("Waiting 10 seconds for next check...")
                await asyncio.sleep(10)

async def main():
    """Run all examples"""
    print("Price History API Examples")
    print("=" * 50)
    print("Make sure the API is running at http://localhost:8000")
    print()
    
    examples = [
        example_health_check,
        example_current_prices,
        example_cheapest_store,
        example_supermarket_products,
        example_price_history,
        example_price_trends,
        example_price_alerts,
        example_price_comparison,
        example_product_search,
        example_bulk_price_comparison,
        example_analytics_price_trends,
        example_analytics_top_deals,
        example_analytics_volatility,
        example_pagination,
        example_filtering,
        example_real_time_monitoring
    ]
    
    for i, example in enumerate(examples, 1):
        try:
            print(f"\n{i}. Running {example.__name__}...")
            await example()
            print("-" * 50)
        except Exception as e:
            print(f"Error in {example.__name__}: {e}")
            print("-" * 50)
    
    print("\nAll examples completed!")

if __name__ == "__main__":
    asyncio.run(main())