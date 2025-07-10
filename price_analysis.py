"""
Price History Analysis Module
============================

Comprehensive module for analyzing price history data from CheckjeBon imports.
Provides functions for trend analysis, comparisons, alerts, and reporting.

Features:
- Price trend analysis with volatility detection
- Cross-supermarket price comparisons
- Automated alert generation
- Data export and reporting
- API helper functions with caching
- Statistical analysis and insights

Usage:
    from price_analysis import PriceAnalyzer
    
    analyzer = PriceAnalyzer(supabase_client)
    trends = analyzer.get_price_trends(product_id, days=30)
    alerts = analyzer.check_price_alerts()
"""

import os
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from collections import defaultdict
import asyncio
from functools import wraps

# Third-party imports
import numpy as np
import pandas as pd
from supabase import Client
from postgrest import APIError

# Configuration
@dataclass
class AnalysisConfig:
    """Configuration for price analysis"""
    cache_ttl: int = 300  # 5 minutes
    max_results: int = 1000
    default_days: int = 30
    
    # Volatility thresholds
    low_volatility_threshold: float = 5.0  # percentage
    high_volatility_threshold: float = 20.0  # percentage
    
    # Alert thresholds
    price_drop_threshold: float = 15.0  # percentage
    price_spike_threshold: float = 25.0  # percentage
    
    # Seasonal analysis
    seasonal_window_days: int = 365
    seasonal_min_data_points: int = 50

@dataclass
class PriceTrend:
    """Price trend data structure"""
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

@dataclass
class PriceComparison:
    """Price comparison data structure"""
    product_id: str
    product_name: str
    comparison_date: date
    prices: List[Dict[str, Any]]
    cheapest_store: str
    most_expensive_store: str
    price_range: float
    avg_price: float
    std_deviation: float

@dataclass
class PriceAlert:
    """Price alert data structure"""
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

class PriceAnalyzer:
    """Main price analysis class"""
    
    def __init__(self, supabase_client: Client, config: AnalysisConfig = None):
        self.supabase = supabase_client
        self.config = config or AnalysisConfig()
        self.logger = self._setup_logging()
        self._cache = {}
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('price_analyzer')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        import hashlib
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached result if available and not expired"""
        if key in self._cache:
            cached_data, timestamp = self._cache[key]
            if (datetime.now() - timestamp).total_seconds() < self.config.cache_ttl:
                return cached_data
            else:
                del self._cache[key]
        return None
    
    def _set_cached(self, key: str, data: Any):
        """Set cached result"""
        self._cache[key] = (data, datetime.now())
    
    def cache_result(self, ttl: int = None):
        """Decorator to cache function results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = self._cache_key(func.__name__, *args, **kwargs)
                
                # Try to get cached result
                cached = self._get_cached(cache_key)
                if cached is not None:
                    return cached
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self._set_cached(cache_key, result)
                
                return result
            return wrapper
        return decorator
    
    # =====================================================================
    # 1. PRICE TREND ANALYSIS
    # =====================================================================
    
    @cache_result()
    def get_price_trends(self, product_id: str = None, supermarket_id: str = None, 
                        days: int = None) -> List[PriceTrend]:
        """
        Calculate price trends for products over specified time period
        
        Args:
            product_id: Specific product ID (optional)
            supermarket_id: Specific supermarket ID (optional)
            days: Number of days to analyze (default: 30)
            
        Returns:
            List of PriceTrend objects
        """
        try:
            days = days or self.config.default_days
            start_date = (date.today() - timedelta(days=days)).isoformat()
            
            # Build query
            query = self.supabase.table("price_history").select(
                "product_id, supermarket_id, price_date, price, "
                "products!inner(name), supermarkets!inner(name)"
            ).gte("price_date", start_date).order("price_date")
            
            if product_id:
                query = query.eq("product_id", product_id)
            if supermarket_id:
                query = query.eq("supermarket_id", supermarket_id)
            
            response = query.execute()
            
            if not response.data:
                return []
            
            # Group data by product and supermarket
            grouped_data = defaultdict(list)
            for row in response.data:
                key = (row['product_id'], row['supermarket_id'])
                grouped_data[key].append(row)
            
            trends = []
            for (prod_id, super_id), prices in grouped_data.items():
                if len(prices) < 2:
                    continue
                
                # Sort by date
                prices.sort(key=lambda x: x['price_date'])
                
                # Calculate trend statistics
                price_values = [p['price'] for p in prices]
                start_price = price_values[0]
                end_price = price_values[-1]
                price_change = end_price - start_price
                price_change_percentage = (price_change / start_price) * 100 if start_price > 0 else 0
                
                # Calculate volatility (coefficient of variation)
                avg_price = np.mean(price_values)
                std_price = np.std(price_values)
                volatility = (std_price / avg_price) * 100 if avg_price > 0 else 0
                
                trend = PriceTrend(
                    product_id=prod_id,
                    product_name=prices[0]['products']['name'],
                    supermarket_id=super_id,
                    supermarket_name=prices[0]['supermarkets']['name'],
                    start_date=date.fromisoformat(prices[0]['price_date']),
                    end_date=date.fromisoformat(prices[-1]['price_date']),
                    start_price=start_price,
                    end_price=end_price,
                    price_change=price_change,
                    price_change_percentage=price_change_percentage,
                    avg_price=avg_price,
                    min_price=min(price_values),
                    max_price=max(price_values),
                    volatility=volatility,
                    data_points=len(prices)
                )
                trends.append(trend)
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error calculating price trends: {e}")
            return []
    
    @cache_result()
    def get_price_volatility(self, product_id: str = None, days: int = None) -> List[Dict]:
        """
        Calculate price volatility for products
        
        Args:
            product_id: Specific product ID (optional)
            days: Number of days to analyze (default: 30)
            
        Returns:
            List of volatility data with classifications
        """
        try:
            trends = self.get_price_trends(product_id=product_id, days=days)
            
            volatility_data = []
            for trend in trends:
                # Classify volatility
                if trend.volatility < self.config.low_volatility_threshold:
                    volatility_class = "low"
                elif trend.volatility > self.config.high_volatility_threshold:
                    volatility_class = "high"
                else:
                    volatility_class = "medium"
                
                volatility_data.append({
                    'product_id': trend.product_id,
                    'product_name': trend.product_name,
                    'supermarket_id': trend.supermarket_id,
                    'supermarket_name': trend.supermarket_name,
                    'volatility': trend.volatility,
                    'volatility_class': volatility_class,
                    'price_range': trend.max_price - trend.min_price,
                    'avg_price': trend.avg_price,
                    'data_points': trend.data_points
                })
            
            # Sort by volatility descending
            volatility_data.sort(key=lambda x: x['volatility'], reverse=True)
            
            return volatility_data
            
        except Exception as e:
            self.logger.error(f"Error calculating price volatility: {e}")
            return []
    
    @cache_result()
    def detect_seasonal_patterns(self, product_id: str, years: int = 2) -> Dict:
        """
        Detect seasonal price patterns for a product
        
        Args:
            product_id: Product ID to analyze
            years: Number of years to analyze
            
        Returns:
            Dictionary with seasonal analysis results
        """
        try:
            start_date = (date.today() - timedelta(days=years * 365)).isoformat()
            
            response = self.supabase.table("price_history").select(
                "price_date, price, supermarket_id, supermarkets!inner(name)"
            ).eq("product_id", product_id).gte("price_date", start_date).order("price_date").execute()
            
            if not response.data or len(response.data) < self.config.seasonal_min_data_points:
                return {"error": "Insufficient data for seasonal analysis"}
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(response.data)
            df['price_date'] = pd.to_datetime(df['price_date'])
            df['month'] = df['price_date'].dt.month
            df['quarter'] = df['price_date'].dt.quarter
            df['day_of_year'] = df['price_date'].dt.dayofyear
            
            # Monthly patterns
            monthly_stats = df.groupby('month')['price'].agg([
                'mean', 'std', 'min', 'max', 'count'
            ]).round(2)
            
            # Quarterly patterns
            quarterly_stats = df.groupby('quarter')['price'].agg([
                'mean', 'std', 'min', 'max', 'count'
            ]).round(2)
            
            # Find peak and low seasons
            peak_month = monthly_stats['mean'].idxmax()
            low_month = monthly_stats['mean'].idxmin()
            
            seasonal_analysis = {
                'product_id': product_id,
                'analysis_period': f"{years} years",
                'data_points': len(df),
                'monthly_patterns': monthly_stats.to_dict(),
                'quarterly_patterns': quarterly_stats.to_dict(),
                'peak_season': {
                    'month': peak_month,
                    'avg_price': float(monthly_stats.loc[peak_month, 'mean'])
                },
                'low_season': {
                    'month': low_month,
                    'avg_price': float(monthly_stats.loc[low_month, 'mean'])
                },
                'seasonal_variation': float(monthly_stats['mean'].max() - monthly_stats['mean'].min()),
                'price_stability': float(df['price'].std() / df['price'].mean() * 100)
            }
            
            return seasonal_analysis
            
        except Exception as e:
            self.logger.error(f"Error detecting seasonal patterns: {e}")
            return {"error": str(e)}
    
    @cache_result()
    def detect_significant_changes(self, days: int = 7, threshold: float = 15.0) -> List[Dict]:
        """
        Detect significant price changes in recent period
        
        Args:
            days: Number of days to look back
            threshold: Percentage threshold for significant change
            
        Returns:
            List of significant price changes
        """
        try:
            start_date = (date.today() - timedelta(days=days)).isoformat()
            
            response = self.supabase.table("price_history").select(
                "product_id, supermarket_id, price_date, price, price_change_percentage, "
                "products!inner(name), supermarkets!inner(name)"
            ).gte("price_date", start_date).order("price_date", desc=True).execute()
            
            significant_changes = []
            for row in response.data:
                if row['price_change_percentage'] and abs(row['price_change_percentage']) >= threshold:
                    change_type = "increase" if row['price_change_percentage'] > 0 else "decrease"
                    severity = "major" if abs(row['price_change_percentage']) >= threshold * 2 else "significant"
                    
                    significant_changes.append({
                        'product_id': row['product_id'],
                        'product_name': row['products']['name'],
                        'supermarket_id': row['supermarket_id'],
                        'supermarket_name': row['supermarkets']['name'],
                        'price_date': row['price_date'],
                        'current_price': row['price'],
                        'change_percentage': row['price_change_percentage'],
                        'change_type': change_type,
                        'severity': severity
                    })
            
            return significant_changes
            
        except Exception as e:
            self.logger.error(f"Error detecting significant changes: {e}")
            return []
    
    # =====================================================================
    # 2. COMPARISON FUNCTIONS
    # =====================================================================
    
    @cache_result()
    def compare_current_prices(self, product_id: str = None, category_id: str = None) -> List[PriceComparison]:
        """
        Compare current prices across supermarkets
        
        Args:
            product_id: Specific product ID (optional)
            category_id: Specific category ID (optional)
            
        Returns:
            List of PriceComparison objects
        """
        try:
            # Build query
            query = self.supabase.table("current_prices").select(
                "product_id, supermarket_id, price, last_updated, "
                "products!inner(name, category_id), supermarkets!inner(name)"
            ).eq("is_available", True)
            
            if product_id:
                query = query.eq("product_id", product_id)
            if category_id:
                query = query.eq("products.category_id", category_id)
            
            response = query.execute()
            
            if not response.data:
                return []
            
            # Group by product
            grouped_data = defaultdict(list)
            for row in response.data:
                grouped_data[row['product_id']].append(row)
            
            comparisons = []
            for product_id, prices in grouped_data.items():
                if len(prices) < 2:  # Need at least 2 stores for comparison
                    continue
                
                # Sort by price
                prices.sort(key=lambda x: x['price'])
                
                price_values = [p['price'] for p in prices]
                
                # Format price data
                formatted_prices = []
                for price_data in prices:
                    formatted_prices.append({
                        'supermarket_id': price_data['supermarket_id'],
                        'supermarket_name': price_data['supermarkets']['name'],
                        'price': price_data['price'],
                        'last_updated': price_data['last_updated']
                    })
                
                comparison = PriceComparison(
                    product_id=product_id,
                    product_name=prices[0]['products']['name'],
                    comparison_date=date.today(),
                    prices=formatted_prices,
                    cheapest_store=prices[0]['supermarkets']['name'],
                    most_expensive_store=prices[-1]['supermarkets']['name'],
                    price_range=max(price_values) - min(price_values),
                    avg_price=np.mean(price_values),
                    std_deviation=np.std(price_values)
                )
                comparisons.append(comparison)
            
            return comparisons
            
        except Exception as e:
            self.logger.error(f"Error comparing current prices: {e}")
            return []
    
    @cache_result()
    def compare_historical_prices(self, product_id: str, days: int = 30) -> Dict:
        """
        Compare historical prices for a product across supermarkets
        
        Args:
            product_id: Product ID to compare
            days: Number of days to analyze
            
        Returns:
            Dictionary with historical comparison data
        """
        try:
            start_date = (date.today() - timedelta(days=days)).isoformat()
            
            response = self.supabase.table("price_history").select(
                "supermarket_id, price_date, price, supermarkets!inner(name)"
            ).eq("product_id", product_id).gte("price_date", start_date).order("price_date").execute()
            
            if not response.data:
                return {"error": "No historical data found"}
            
            # Get product name
            product_response = self.supabase.table("products").select("name").eq("id", product_id).single().execute()
            product_name = product_response.data['name'] if product_response.data else "Unknown"
            
            # Group by supermarket
            supermarket_data = defaultdict(list)
            for row in response.data:
                supermarket_data[row['supermarket_id']].append({
                    'date': row['price_date'],
                    'price': row['price'],
                    'supermarket_name': row['supermarkets']['name']
                })
            
            # Calculate statistics for each supermarket
            supermarket_stats = {}
            for supermarket_id, prices in supermarket_data.items():
                price_values = [p['price'] for p in prices]
                supermarket_stats[supermarket_id] = {
                    'supermarket_name': prices[0]['supermarket_name'],
                    'avg_price': np.mean(price_values),
                    'min_price': min(price_values),
                    'max_price': max(price_values),
                    'latest_price': prices[-1]['price'],
                    'price_trend': prices[-1]['price'] - prices[0]['price'],
                    'data_points': len(prices)
                }
            
            # Find best and worst performing stores
            best_store = min(supermarket_stats.items(), key=lambda x: x[1]['avg_price'])
            worst_store = max(supermarket_stats.items(), key=lambda x: x[1]['avg_price'])
            
            return {
                'product_id': product_id,
                'product_name': product_name,
                'analysis_period': f"{days} days",
                'supermarket_stats': supermarket_stats,
                'best_store': {
                    'supermarket_id': best_store[0],
                    'supermarket_name': best_store[1]['supermarket_name'],
                    'avg_price': best_store[1]['avg_price']
                },
                'worst_store': {
                    'supermarket_id': worst_store[0],
                    'supermarket_name': worst_store[1]['supermarket_name'],
                    'avg_price': worst_store[1]['avg_price']
                },
                'price_spread': worst_store[1]['avg_price'] - best_store[1]['avg_price']
            }
            
        except Exception as e:
            self.logger.error(f"Error comparing historical prices: {e}")
            return {"error": str(e)}
    
    @cache_result()
    def get_price_ranges(self, category_id: str = None, days: int = 30) -> List[Dict]:
        """
        Get price ranges (min/max/avg) for products
        
        Args:
            category_id: Specific category ID (optional)
            days: Number of days to analyze
            
        Returns:
            List of price range data
        """
        try:
            start_date = (date.today() - timedelta(days=days)).isoformat()
            
            # Build query
            query = self.supabase.table("price_history").select(
                "product_id, price, products!inner(name, category_id)"
            ).gte("price_date", start_date)
            
            if category_id:
                query = query.eq("products.category_id", category_id)
            
            response = query.execute()
            
            if not response.data:
                return []
            
            # Group by product
            product_prices = defaultdict(list)
            for row in response.data:
                product_prices[row['product_id']].append({
                    'price': row['price'],
                    'product_name': row['products']['name']
                })
            
            price_ranges = []
            for product_id, prices in product_prices.items():
                price_values = [p['price'] for p in prices]
                
                price_ranges.append({
                    'product_id': product_id,
                    'product_name': prices[0]['product_name'],
                    'min_price': min(price_values),
                    'max_price': max(price_values),
                    'avg_price': np.mean(price_values),
                    'median_price': np.median(price_values),
                    'price_range': max(price_values) - min(price_values),
                    'std_deviation': np.std(price_values),
                    'data_points': len(price_values)
                })
            
            # Sort by price range descending
            price_ranges.sort(key=lambda x: x['price_range'], reverse=True)
            
            return price_ranges
            
        except Exception as e:
            self.logger.error(f"Error getting price ranges: {e}")
            return []
    
    @cache_result()
    def find_cheapest_stores(self, product_id: str = None, days: int = 30) -> List[Dict]:
        """
        Find cheapest stores for products over time
        
        Args:
            product_id: Specific product ID (optional)
            days: Number of days to analyze
            
        Returns:
            List of cheapest store data
        """
        try:
            start_date = (date.today() - timedelta(days=days)).isoformat()
            
            # Build query
            query = self.supabase.table("price_history").select(
                "product_id, supermarket_id, price, "
                "products!inner(name), supermarkets!inner(name)"
            ).gte("price_date", start_date)
            
            if product_id:
                query = query.eq("product_id", product_id)
            
            response = query.execute()
            
            if not response.data:
                return []
            
            # Group by product and supermarket
            product_supermarket_prices = defaultdict(lambda: defaultdict(list))
            for row in response.data:
                product_supermarket_prices[row['product_id']][row['supermarket_id']].append({
                    'price': row['price'],
                    'product_name': row['products']['name'],
                    'supermarket_name': row['supermarkets']['name']
                })
            
            cheapest_stores = []
            for product_id, supermarket_prices in product_supermarket_prices.items():
                # Calculate average price for each supermarket
                supermarket_avg_prices = {}
                for supermarket_id, prices in supermarket_prices.items():
                    avg_price = np.mean([p['price'] for p in prices])
                    supermarket_avg_prices[supermarket_id] = {
                        'avg_price': avg_price,
                        'supermarket_name': prices[0]['supermarket_name'],
                        'product_name': prices[0]['product_name'],
                        'data_points': len(prices)
                    }
                
                # Find cheapest store
                cheapest_store_id = min(supermarket_avg_prices.keys(), 
                                      key=lambda x: supermarket_avg_prices[x]['avg_price'])
                cheapest_data = supermarket_avg_prices[cheapest_store_id]
                
                # Calculate savings compared to most expensive
                most_expensive_price = max(data['avg_price'] for data in supermarket_avg_prices.values())
                savings = most_expensive_price - cheapest_data['avg_price']
                savings_percentage = (savings / most_expensive_price) * 100 if most_expensive_price > 0 else 0
                
                cheapest_stores.append({
                    'product_id': product_id,
                    'product_name': cheapest_data['product_name'],
                    'cheapest_store_id': cheapest_store_id,
                    'cheapest_store_name': cheapest_data['supermarket_name'],
                    'avg_price': cheapest_data['avg_price'],
                    'savings_amount': savings,
                    'savings_percentage': savings_percentage,
                    'stores_compared': len(supermarket_avg_prices),
                    'data_points': cheapest_data['data_points']
                })
            
            # Sort by savings percentage descending
            cheapest_stores.sort(key=lambda x: x['savings_percentage'], reverse=True)
            
            return cheapest_stores
            
        except Exception as e:
            self.logger.error(f"Error finding cheapest stores: {e}")
            return []
    
    # =====================================================================
    # 3. ALERT FUNCTIONS
    # =====================================================================
    
    def check_price_alerts(self, drop_threshold: float = None, spike_threshold: float = None) -> List[PriceAlert]:
        """
        Check for price alerts based on recent changes
        
        Args:
            drop_threshold: Percentage threshold for price drops
            spike_threshold: Percentage threshold for price spikes
            
        Returns:
            List of PriceAlert objects
        """
        try:
            drop_threshold = drop_threshold or self.config.price_drop_threshold
            spike_threshold = spike_threshold or self.config.price_spike_threshold
            
            # Get recent price changes
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            
            response = self.supabase.table("price_history").select(
                "product_id, supermarket_id, price, price_change_percentage, price_date, "
                "products!inner(name), supermarkets!inner(name)"
            ).gte("price_date", yesterday).order("price_date", desc=True).execute()
            
            alerts = []
            alert_id = 1
            
            for row in response.data:
                change_pct = row['price_change_percentage']
                if not change_pct:
                    continue
                
                alert_type = None
                severity = "low"
                
                # Check for price drops
                if change_pct <= -drop_threshold:
                    alert_type = "price_drop"
                    if change_pct <= -drop_threshold * 2:
                        severity = "high"
                    elif change_pct <= -drop_threshold * 1.5:
                        severity = "medium"
                
                # Check for price spikes
                elif change_pct >= spike_threshold:
                    alert_type = "price_spike"
                    if change_pct >= spike_threshold * 2:
                        severity = "high"
                    elif change_pct >= spike_threshold * 1.5:
                        severity = "medium"
                
                if alert_type:
                    alert = PriceAlert(
                        alert_id=str(alert_id),
                        product_id=row['product_id'],
                        product_name=row['products']['name'],
                        supermarket_id=row['supermarket_id'],
                        supermarket_name=row['supermarkets']['name'],
                        alert_type=alert_type,
                        current_price=row['price'],
                        previous_price=row['price'] / (1 + change_pct/100),
                        change_percentage=change_pct,
                        alert_date=datetime.now(),
                        severity=severity
                    )
                    alerts.append(alert)
                    alert_id += 1
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error checking price alerts: {e}")
            return []
    
    def detect_new_products(self, days: int = 7) -> List[Dict]:
        """
        Detect new products added in recent period
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of new product data
        """
        try:
            start_date = (date.today() - timedelta(days=days)).isoformat()
            
            response = self.supabase.table("products").select(
                "id, name, brand, created_at, category_id, "
                "product_categories!inner(name)"
            ).gte("created_at", start_date).order("created_at", desc=True).execute()
            
            new_products = []
            for row in response.data:
                new_products.append({
                    'product_id': row['id'],
                    'product_name': row['name'],
                    'brand': row['brand'],
                    'category_name': row['product_categories']['name'],
                    'created_at': row['created_at']
                })
            
            return new_products
            
        except Exception as e:
            self.logger.error(f"Error detecting new products: {e}")
            return []
    
    def find_store_specific_deals(self, supermarket_id: str, discount_threshold: float = 20.0) -> List[Dict]:
        """
        Find deals specific to a store
        
        Args:
            supermarket_id: Supermarket ID to check
            discount_threshold: Minimum discount percentage
            
        Returns:
            List of store deals
        """
        try:
            response = self.supabase.table("current_prices").select(
                "product_id, price, original_price, discount_percentage, "
                "products!inner(name), supermarkets!inner(name)"
            ).eq("supermarket_id", supermarket_id).eq("is_on_sale", True).gte(
                "discount_percentage", discount_threshold
            ).order("discount_percentage", desc=True).execute()
            
            deals = []
            for row in response.data:
                deals.append({
                    'product_id': row['product_id'],
                    'product_name': row['products']['name'],
                    'supermarket_name': row['supermarkets']['name'],
                    'current_price': row['price'],
                    'original_price': row['original_price'],
                    'discount_percentage': row['discount_percentage'],
                    'savings_amount': row['original_price'] - row['price']
                })
            
            return deals
            
        except Exception as e:
            self.logger.error(f"Error finding store deals: {e}")
            return []
    
    # =====================================================================
    # 4. REPORTING FUNCTIONS
    # =====================================================================
    
    def generate_price_history_report(self, product_id: str, days: int = 90) -> Dict:
        """
        Generate comprehensive price history report for a product
        
        Args:
            product_id: Product ID to report on
            days: Number of days to include
            
        Returns:
            Dictionary with comprehensive report data
        """
        try:
            # Get product info
            product_response = self.supabase.table("products").select(
                "name, brand, category_id, product_categories!inner(name)"
            ).eq("id", product_id).single().execute()
            
            if not product_response.data:
                return {"error": "Product not found"}
            
            product_info = product_response.data
            
            # Get price trends
            trends = self.get_price_trends(product_id=product_id, days=days)
            
            # Get historical comparison
            historical_comparison = self.compare_historical_prices(product_id, days)
            
            # Get current prices
            current_comparison = self.compare_current_prices(product_id=product_id)
            
            # Get seasonal patterns if enough data
            seasonal_patterns = self.detect_seasonal_patterns(product_id, years=1)
            
            # Get recent alerts
            alerts = [alert for alert in self.check_price_alerts() if alert.product_id == product_id]
            
            report = {
                'product_info': {
                    'id': product_id,
                    'name': product_info['name'],
                    'brand': product_info['brand'],
                    'category': product_info['product_categories']['name']
                },
                'analysis_period': f"{days} days",
                'generated_at': datetime.now().isoformat(),
                'price_trends': [asdict(trend) for trend in trends],
                'historical_comparison': historical_comparison,
                'current_comparison': [asdict(comp) for comp in current_comparison],
                'seasonal_patterns': seasonal_patterns,
                'recent_alerts': [asdict(alert) for alert in alerts],
                'summary': {
                    'total_stores_tracking': len(trends),
                    'most_volatile_store': max(trends, key=lambda x: x.volatility).supermarket_name if trends else None,
                    'best_price_store': min(trends, key=lambda x: x.end_price).supermarket_name if trends else None,
                    'avg_price_change': np.mean([t.price_change_percentage for t in trends]) if trends else 0
                }
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating price history report: {e}")
            return {"error": str(e)}
    
    def export_data_for_visualization(self, product_id: str = None, days: int = 30, format: str = "json") -> Union[str, Dict]:
        """
        Export price data for visualization tools
        
        Args:
            product_id: Specific product ID (optional)
            days: Number of days to export
            format: Export format ('json', 'csv')
            
        Returns:
            Formatted data for visualization
        """
        try:
            start_date = (date.today() - timedelta(days=days)).isoformat()
            
            # Build query
            query = self.supabase.table("price_history").select(
                "product_id, supermarket_id, price_date, price, "
                "products!inner(name), supermarkets!inner(name)"
            ).gte("price_date", start_date).order("price_date")
            
            if product_id:
                query = query.eq("product_id", product_id)
            
            response = query.execute()
            
            if not response.data:
                return {"error": "No data found"}
            
            # Format data for visualization
            visualization_data = []
            for row in response.data:
                visualization_data.append({
                    'date': row['price_date'],
                    'price': row['price'],
                    'product_name': row['products']['name'],
                    'supermarket_name': row['supermarkets']['name'],
                    'product_id': row['product_id'],
                    'supermarket_id': row['supermarket_id']
                })
            
            if format == "json":
                return {
                    'data': visualization_data,
                    'metadata': {
                        'total_records': len(visualization_data),
                        'date_range': f"{days} days",
                        'generated_at': datetime.now().isoformat()
                    }
                }
            elif format == "csv":
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=visualization_data[0].keys())
                writer.writeheader()
                writer.writerows(visualization_data)
                
                return output.getvalue()
            
            return {"error": "Unsupported format"}
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            return {"error": str(e)}
    
    def get_summary_statistics(self, days: int = 30) -> Dict:
        """
        Get summary statistics for the analysis period
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with summary statistics
        """
        try:
            start_date = (date.today() - timedelta(days=days)).isoformat()
            
            # Get basic counts
            products_response = self.supabase.table("products").select("id", count="exact").execute()
            supermarkets_response = self.supabase.table("supermarkets").select("id", count="exact").execute()
            
            # Get price records count
            price_records_response = self.supabase.table("price_history").select(
                "id", count="exact"
            ).gte("price_date", start_date).execute()
            
            # Get price changes
            price_changes_response = self.supabase.table("price_history").select(
                "price_change_percentage"
            ).gte("price_date", start_date).neq("price_change_percentage", 0).execute()
            
            # Calculate statistics
            if price_changes_response.data:
                changes = [row['price_change_percentage'] for row in price_changes_response.data if row['price_change_percentage']]
                avg_change = np.mean(changes) if changes else 0
                volatility = np.std(changes) if changes else 0
                positive_changes = len([c for c in changes if c > 0])
                negative_changes = len([c for c in changes if c < 0])
            else:
                avg_change = volatility = positive_changes = negative_changes = 0
            
            # Get alerts
            alerts = self.check_price_alerts()
            
            summary = {
                'analysis_period': f"{days} days",
                'generated_at': datetime.now().isoformat(),
                'basic_stats': {
                    'total_products': products_response.count,
                    'total_supermarkets': supermarkets_response.count,
                    'price_records': price_records_response.count,
                    'price_changes': len(price_changes_response.data) if price_changes_response.data else 0
                },
                'price_change_stats': {
                    'avg_change_percentage': round(avg_change, 2),
                    'volatility': round(volatility, 2),
                    'positive_changes': positive_changes,
                    'negative_changes': negative_changes
                },
                'alerts': {
                    'total_alerts': len(alerts),
                    'price_drops': len([a for a in alerts if a.alert_type == 'price_drop']),
                    'price_spikes': len([a for a in alerts if a.alert_type == 'price_spike']),
                    'high_severity': len([a for a in alerts if a.severity == 'high'])
                }
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting summary statistics: {e}")
            return {"error": str(e)}
    
    # =====================================================================
    # 5. API HELPER FUNCTIONS
    # =====================================================================
    
    def format_for_api(self, data: Any, include_metadata: bool = True) -> Dict:
        """
        Format data for API consumption
        
        Args:
            data: Data to format
            include_metadata: Whether to include metadata
            
        Returns:
            API-formatted response
        """
        try:
            response = {
                'success': True,
                'data': data
            }
            
            if include_metadata:
                response['metadata'] = {
                    'generated_at': datetime.now().isoformat(),
                    'cache_ttl': self.config.cache_ttl,
                    'version': '1.0'
                }
            
            return response
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    def paginate_results(self, data: List[Any], page: int = 1, limit: int = 50) -> Dict:
        """
        Paginate results for API responses
        
        Args:
            data: List of data to paginate
            page: Page number (1-based)
            limit: Items per page
            
        Returns:
            Paginated response
        """
        try:
            total = len(data)
            start_index = (page - 1) * limit
            end_index = start_index + limit
            
            paginated_data = data[start_index:end_index]
            
            return {
                'data': paginated_data,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': (total + limit - 1) // limit,
                    'has_next': end_index < total,
                    'has_prev': page > 1
                }
            }
            
        except Exception as e:
            return {
                'data': [],
                'pagination': None,
                'error': str(e)
            }
    
    def clear_cache(self):
        """Clear all cached results"""
        self._cache.clear()
        self.logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'cache_size': len(self._cache),
            'cache_ttl': self.config.cache_ttl,
            'cached_functions': list(set(key.split(':')[0] for key in self._cache.keys()))
        }

# Convenience functions for direct usage
def create_analyzer(supabase_url: str, supabase_key: str, config: AnalysisConfig = None) -> PriceAnalyzer:
    """
    Create a PriceAnalyzer instance with Supabase client
    
    Args:
        supabase_url: Supabase project URL
        supabase_key: Supabase API key
        config: Analysis configuration
        
    Returns:
        PriceAnalyzer instance
    """
    from supabase import create_client
    
    supabase = create_client(supabase_url, supabase_key)
    return PriceAnalyzer(supabase, config)

# Example usage
if __name__ == "__main__":
    # Example usage (requires environment variables)
    import os
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if supabase_url and supabase_key:
        analyzer = create_analyzer(supabase_url, supabase_key)
        
        # Example: Get price trends
        trends = analyzer.get_price_trends(days=30)
        print(f"Found {len(trends)} price trends")
        
        # Example: Check alerts
        alerts = analyzer.check_price_alerts()
        print(f"Found {len(alerts)} price alerts")
        
        # Example: Get summary statistics
        summary = analyzer.get_summary_statistics()
        print(f"Summary: {summary}")
    else:
        print("Please set SUPABASE_URL and SUPABASE_KEY environment variables")