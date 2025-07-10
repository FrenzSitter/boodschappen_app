#!/usr/bin/env python3
"""
Price Analysis Examples
=======================

Example usage of the price_analysis module with various scenarios
and use cases for analyzing supermarket price data.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from price_analysis import PriceAnalyzer, AnalysisConfig, create_analyzer

def example_basic_usage():
    """Basic usage example"""
    print("=== Basic Usage Example ===")
    
    # Create analyzer
    analyzer = create_analyzer(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Get price trends for last 30 days
    trends = analyzer.get_price_trends(days=30)
    print(f"Found {len(trends)} price trends")
    
    # Show top 5 most volatile products
    if trends:
        sorted_trends = sorted(trends, key=lambda x: x.volatility, reverse=True)
        print("\nTop 5 most volatile products:")
        for i, trend in enumerate(sorted_trends[:5]):
            print(f"{i+1}. {trend.product_name} ({trend.supermarket_name})")
            print(f"   Volatility: {trend.volatility:.2f}%")
            print(f"   Price change: {trend.price_change_percentage:.2f}%")
            print()

def example_price_comparison():
    """Price comparison example"""
    print("=== Price Comparison Example ===")
    
    analyzer = create_analyzer(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Compare current prices across supermarkets
    comparisons = analyzer.compare_current_prices()
    
    if comparisons:
        # Show products with biggest price differences
        sorted_comparisons = sorted(comparisons, key=lambda x: x.price_range, reverse=True)
        
        print("Products with biggest price differences:")
        for i, comp in enumerate(sorted_comparisons[:5]):
            print(f"{i+1}. {comp.product_name}")
            print(f"   Price range: €{comp.price_range:.2f}")
            print(f"   Cheapest: {comp.cheapest_store}")
            print(f"   Most expensive: {comp.most_expensive_store}")
            print(f"   Average price: €{comp.avg_price:.2f}")
            print()

def example_alerts():
    """Price alerts example"""
    print("=== Price Alerts Example ===")
    
    analyzer = create_analyzer(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Check for price alerts
    alerts = analyzer.check_price_alerts()
    
    if alerts:
        print(f"Found {len(alerts)} price alerts")
        
        # Group by alert type
        drops = [a for a in alerts if a.alert_type == 'price_drop']
        spikes = [a for a in alerts if a.alert_type == 'price_spike']
        
        print(f"Price drops: {len(drops)}")
        print(f"Price spikes: {len(spikes)}")
        
        # Show high severity alerts
        high_severity = [a for a in alerts if a.severity == 'high']
        if high_severity:
            print("\nHigh severity alerts:")
            for alert in high_severity[:5]:
                print(f"- {alert.product_name} ({alert.supermarket_name})")
                print(f"  {alert.alert_type}: {alert.change_percentage:.2f}%")
                print(f"  Price: €{alert.current_price:.2f}")
                print()
    else:
        print("No price alerts found")

def example_seasonal_analysis():
    """Seasonal analysis example"""
    print("=== Seasonal Analysis Example ===")
    
    analyzer = create_analyzer(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Get some products to analyze
    trends = analyzer.get_price_trends(days=30)
    
    if trends:
        # Pick a product with good data coverage
        product_id = trends[0].product_id
        
        # Analyze seasonal patterns
        seasonal_data = analyzer.detect_seasonal_patterns(product_id, years=1)
        
        if 'error' not in seasonal_data:
            print(f"Seasonal analysis for: {trends[0].product_name}")
            print(f"Data points: {seasonal_data['data_points']}")
            print(f"Price stability: {seasonal_data['price_stability']:.2f}%")
            print(f"Seasonal variation: €{seasonal_data['seasonal_variation']:.2f}")
            
            peak_season = seasonal_data['peak_season']
            low_season = seasonal_data['low_season']
            
            print(f"\nPeak season: Month {peak_season['month']} (€{peak_season['avg_price']:.2f})")
            print(f"Low season: Month {low_season['month']} (€{low_season['avg_price']:.2f})")
        else:
            print(f"Error: {seasonal_data['error']}")
    else:
        print("No trend data available for seasonal analysis")

def example_reporting():
    """Reporting example"""
    print("=== Reporting Example ===")
    
    analyzer = create_analyzer(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Generate summary statistics
    summary = analyzer.get_summary_statistics(days=30)
    
    if 'error' not in summary:
        print("Summary Statistics (Last 30 days):")
        print(f"Total products: {summary['basic_stats']['total_products']}")
        print(f"Total supermarkets: {summary['basic_stats']['total_supermarkets']}")
        print(f"Price records: {summary['basic_stats']['price_records']}")
        print(f"Price changes: {summary['basic_stats']['price_changes']}")
        
        print(f"\nPrice change statistics:")
        print(f"Average change: {summary['price_change_stats']['avg_change_percentage']:.2f}%")
        print(f"Volatility: {summary['price_change_stats']['volatility']:.2f}%")
        print(f"Positive changes: {summary['price_change_stats']['positive_changes']}")
        print(f"Negative changes: {summary['price_change_stats']['negative_changes']}")
        
        print(f"\nAlerts:")
        print(f"Total alerts: {summary['alerts']['total_alerts']}")
        print(f"Price drops: {summary['alerts']['price_drops']}")
        print(f"Price spikes: {summary['alerts']['price_spikes']}")
        print(f"High severity: {summary['alerts']['high_severity']}")
    else:
        print(f"Error: {summary['error']}")

def example_cheapest_stores():
    """Cheapest stores example"""
    print("=== Cheapest Stores Example ===")
    
    analyzer = create_analyzer(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Find cheapest stores
    cheapest_stores = analyzer.find_cheapest_stores(days=30)
    
    if cheapest_stores:
        print("Products with best savings opportunities:")
        
        # Show top savings
        for i, store_data in enumerate(cheapest_stores[:10]):
            print(f"{i+1}. {store_data['product_name']}")
            print(f"   Cheapest at: {store_data['cheapest_store_name']}")
            print(f"   Price: €{store_data['avg_price']:.2f}")
            print(f"   Savings: €{store_data['savings_amount']:.2f} ({store_data['savings_percentage']:.1f}%)")
            print(f"   Stores compared: {store_data['stores_compared']}")
            print()
    else:
        print("No cheapest store data available")

def example_api_formatting():
    """API formatting example"""
    print("=== API Formatting Example ===")
    
    analyzer = create_analyzer(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Get some data
    trends = analyzer.get_price_trends(days=7)
    
    # Format for API
    api_response = analyzer.format_for_api(trends[:5])
    
    print("API Response Format:")
    print(json.dumps(api_response, indent=2, default=str))
    
    # Paginate results
    paginated = analyzer.paginate_results(trends, page=1, limit=3)
    
    print("\nPaginated Results:")
    print(f"Page: {paginated['pagination']['page']}")
    print(f"Total: {paginated['pagination']['total']}")
    print(f"Pages: {paginated['pagination']['pages']}")
    print(f"Has next: {paginated['pagination']['has_next']}")

def example_data_export():
    """Data export example"""
    print("=== Data Export Example ===")
    
    analyzer = create_analyzer(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Export data for visualization
    viz_data = analyzer.export_data_for_visualization(days=7, format="json")
    
    if 'error' not in viz_data:
        print(f"Exported {viz_data['metadata']['total_records']} records")
        print(f"Date range: {viz_data['metadata']['date_range']}")
        
        # Show sample data
        if viz_data['data']:
            print("\nSample data points:")
            for i, point in enumerate(viz_data['data'][:3]):
                print(f"{i+1}. {point['product_name']} - {point['supermarket_name']}")
                print(f"   Date: {point['date']}, Price: €{point['price']}")
    else:
        print(f"Export error: {viz_data['error']}")

def example_product_report():
    """Product report example"""
    print("=== Product Report Example ===")
    
    analyzer = create_analyzer(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Get a product to analyze
    trends = analyzer.get_price_trends(days=30)
    
    if trends:
        product_id = trends[0].product_id
        
        # Generate comprehensive report
        report = analyzer.generate_price_history_report(product_id, days=90)
        
        if 'error' not in report:
            print(f"Product Report: {report['product_info']['name']}")
            print(f"Brand: {report['product_info']['brand']}")
            print(f"Category: {report['product_info']['category']}")
            print(f"Analysis period: {report['analysis_period']}")
            
            summary = report['summary']
            print(f"\nSummary:")
            print(f"Stores tracking: {summary['total_stores_tracking']}")
            print(f"Most volatile store: {summary['most_volatile_store']}")
            print(f"Best price store: {summary['best_price_store']}")
            print(f"Average price change: {summary['avg_price_change']:.2f}%")
            
            if report['recent_alerts']:
                print(f"\nRecent alerts: {len(report['recent_alerts'])}")
        else:
            print(f"Report error: {report['error']}")
    else:
        print("No products available for reporting")

def example_custom_config():
    """Custom configuration example"""
    print("=== Custom Configuration Example ===")
    
    # Create custom configuration
    custom_config = AnalysisConfig(
        cache_ttl=600,  # 10 minutes
        max_results=500,
        price_drop_threshold=10.0,  # 10% threshold
        price_spike_threshold=20.0,  # 20% threshold
        high_volatility_threshold=30.0  # 30% threshold
    )
    
    analyzer = create_analyzer(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        config=custom_config
    )
    
    print(f"Custom config - Cache TTL: {custom_config.cache_ttl} seconds")
    print(f"Custom config - Price drop threshold: {custom_config.price_drop_threshold}%")
    
    # Use with custom thresholds
    alerts = analyzer.check_price_alerts()
    print(f"Alerts with custom thresholds: {len(alerts)}")

def example_cache_management():
    """Cache management example"""
    print("=== Cache Management Example ===")
    
    analyzer = create_analyzer(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Initial cache stats
    print("Initial cache stats:")
    print(analyzer.get_cache_stats())
    
    # Run some queries to populate cache
    analyzer.get_price_trends(days=30)
    analyzer.compare_current_prices()
    analyzer.check_price_alerts()
    
    # Check cache stats after queries
    print("\nCache stats after queries:")
    print(analyzer.get_cache_stats())
    
    # Clear cache
    analyzer.clear_cache()
    print("\nCache stats after clearing:")
    print(analyzer.get_cache_stats())

def main():
    """Run all examples"""
    # Check environment variables
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("Error: Please set SUPABASE_URL and SUPABASE_KEY environment variables")
        sys.exit(1)
    
    examples = [
        example_basic_usage,
        example_price_comparison,
        example_alerts,
        example_seasonal_analysis,
        example_reporting,
        example_cheapest_stores,
        example_api_formatting,
        example_data_export,
        example_product_report,
        example_custom_config,
        example_cache_management
    ]
    
    print("Price Analysis Examples")
    print("=" * 50)
    
    for i, example in enumerate(examples, 1):
        try:
            print(f"\n{i}. Running {example.__name__}...")
            example()
            print("-" * 50)
        except Exception as e:
            print(f"Error in {example.__name__}: {e}")
            print("-" * 50)

if __name__ == "__main__":
    main()