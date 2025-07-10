-- =====================================================================
-- Price History Analysis Queries
-- =====================================================================
-- Comprehensive set of example queries for analyzing supermarket 
-- product price history and trends using the optimized schema.
-- =====================================================================

-- =====================================================================
-- 1. CURRENT PRICE QUERIES
-- =====================================================================

-- Get current prices for all products in a specific supermarket
SELECT 
    p.name as product_name,
    p.brand,
    p.size_text,
    cp.price,
    cp.price_per_unit,
    cp.is_on_sale,
    cp.discount_percentage,
    cp.last_updated
FROM current_prices cp
JOIN products p ON cp.product_id = p.id
JOIN supermarkets s ON cp.supermarket_id = s.id
WHERE s.slug = 'albert-heijn'
  AND cp.is_available = true
ORDER BY p.name;

-- Find cheapest price for a specific product across all supermarkets
SELECT 
    p.name as product_name,
    s.name as supermarket_name,
    cp.price,
    cp.price_per_unit,
    cp.is_on_sale,
    cp.discount_percentage,
    RANK() OVER (ORDER BY cp.price ASC) as price_rank
FROM current_prices cp
JOIN products p ON cp.product_id = p.id
JOIN supermarkets s ON cp.supermarket_id = s.id
WHERE p.name ILIKE '%melk%'
  AND cp.is_available = true
ORDER BY cp.price ASC;

-- Products with highest discounts currently
SELECT 
    p.name as product_name,
    p.brand,
    s.name as supermarket_name,
    cp.original_price,
    cp.price as current_price,
    cp.discount_amount,
    cp.discount_percentage,
    cp.sale_start_date,
    cp.sale_end_date
FROM current_prices cp
JOIN products p ON cp.product_id = p.id
JOIN supermarkets s ON cp.supermarket_id = s.id
WHERE cp.is_on_sale = true
  AND cp.discount_percentage > 20
ORDER BY cp.discount_percentage DESC;

-- =====================================================================
-- 2. PRICE HISTORY ANALYSIS
-- =====================================================================

-- Price history for a specific product across all supermarkets (last 30 days)
SELECT 
    ph.price_date,
    p.name as product_name,
    s.name as supermarket_name,
    ph.price,
    ph.price_change,
    ph.price_change_percentage,
    ph.is_on_sale,
    ph.change_reason
FROM price_history ph
JOIN products p ON ph.product_id = p.id
JOIN supermarkets s ON ph.supermarket_id = s.id
WHERE p.name ILIKE '%coca cola%'
  AND ph.price_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY ph.price_date DESC, s.name;

-- Average price trends for a product category over time
SELECT 
    ph.price_date,
    pc.name as category_name,
    COUNT(*) as product_count,
    AVG(ph.price) as avg_price,
    MIN(ph.price) as min_price,
    MAX(ph.price) as max_price,
    STDDEV(ph.price) as price_volatility
FROM price_history ph
JOIN products p ON ph.product_id = p.id
JOIN product_categories pc ON p.category_id = pc.id
WHERE pc.slug = 'zuivel-eieren'
  AND ph.price_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY ph.price_date, pc.name
ORDER BY ph.price_date DESC;

-- Biggest price changes in the last week
SELECT 
    ph.price_date,
    p.name as product_name,
    p.brand,
    s.name as supermarket_name,
    ph.previous_price,
    ph.price as current_price,
    ph.price_change,
    ph.price_change_percentage,
    ph.change_reason
FROM price_history ph
JOIN products p ON ph.product_id = p.id
JOIN supermarkets s ON ph.supermarket_id = s.id
WHERE ph.price_date >= CURRENT_DATE - INTERVAL '7 days'
  AND ABS(ph.price_change_percentage) > 10
ORDER BY ABS(ph.price_change_percentage) DESC;

-- =====================================================================
-- 3. PRICE COMPARISON ANALYSIS
-- =====================================================================

-- Compare prices for similar products across supermarkets
WITH product_prices AS (
    SELECT 
        p.id as product_id,
        p.name as product_name,
        p.brand,
        p.size_text,
        s.name as supermarket_name,
        cp.price,
        cp.price_per_unit,
        cp.is_on_sale
    FROM current_prices cp
    JOIN products p ON cp.product_id = p.id
    JOIN supermarkets s ON cp.supermarket_id = s.id
    WHERE p.name ILIKE '%yoghurt%'
      AND cp.is_available = true
),
price_stats AS (
    SELECT 
        product_id,
        product_name,
        brand,
        size_text,
        COUNT(*) as available_stores,
        MIN(price) as min_price,
        MAX(price) as max_price,
        AVG(price) as avg_price,
        STDDEV(price) as price_std
    FROM product_prices
    GROUP BY product_id, product_name, brand, size_text
)
SELECT 
    ps.product_name,
    ps.brand,
    ps.size_text,
    ps.available_stores,
    ps.min_price,
    ps.max_price,
    ps.avg_price,
    ROUND(ps.price_std, 2) as price_variation,
    ROUND(((ps.max_price - ps.min_price) / ps.avg_price) * 100, 2) as price_spread_percentage
FROM price_stats ps
WHERE ps.available_stores >= 3
ORDER BY price_spread_percentage DESC;

-- Supermarket price positioning analysis
SELECT 
    s.name as supermarket_name,
    COUNT(*) as total_products,
    AVG(cp.price) as avg_price,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cp.price) as median_price,
    COUNT(CASE WHEN cp.is_on_sale THEN 1 END) as products_on_sale,
    ROUND(COUNT(CASE WHEN cp.is_on_sale THEN 1 END)::DECIMAL / COUNT(*) * 100, 2) as sale_percentage,
    AVG(cp.discount_percentage) as avg_discount_percentage
FROM current_prices cp
JOIN supermarkets s ON cp.supermarket_id = s.id
WHERE cp.is_available = true
GROUP BY s.name
ORDER BY avg_price;

-- =====================================================================
-- 4. TREND ANALYSIS
-- =====================================================================

-- Monthly price trends for a specific product
SELECT 
    DATE_TRUNC('month', ph.price_date) as month,
    p.name as product_name,
    s.name as supermarket_name,
    AVG(ph.price) as avg_monthly_price,
    MIN(ph.price) as min_monthly_price,
    MAX(ph.price) as max_monthly_price,
    COUNT(*) as days_available,
    COUNT(CASE WHEN ph.is_on_sale THEN 1 END) as days_on_sale
FROM price_history ph
JOIN products p ON ph.product_id = p.id
JOIN supermarkets s ON ph.supermarket_id = s.id
WHERE p.name ILIKE '%melk%'
  AND ph.price_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', ph.price_date), p.name, s.name
ORDER BY month DESC, s.name;

-- Price volatility analysis by product category
SELECT 
    pc.name as category_name,
    COUNT(DISTINCT p.id) as product_count,
    AVG(ph.price) as avg_price,
    STDDEV(ph.price) as price_volatility,
    ROUND(STDDEV(ph.price) / AVG(ph.price) * 100, 2) as volatility_coefficient,
    COUNT(CASE WHEN ABS(ph.price_change_percentage) > 5 THEN 1 END) as significant_changes,
    AVG(ABS(ph.price_change_percentage)) as avg_change_percentage
FROM price_history ph
JOIN products p ON ph.product_id = p.id
JOIN product_categories pc ON p.category_id = pc.id
WHERE ph.price_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY pc.name
ORDER BY volatility_coefficient DESC;

-- Seasonal price patterns
SELECT 
    EXTRACT(MONTH FROM ph.price_date) as month,
    TO_CHAR(ph.price_date, 'Month') as month_name,
    pc.name as category_name,
    AVG(ph.price) as avg_price,
    STDDEV(ph.price) as price_volatility,
    COUNT(*) as data_points
FROM price_history ph
JOIN products p ON ph.product_id = p.id
JOIN product_categories pc ON p.category_id = pc.id
WHERE ph.price_date >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY EXTRACT(MONTH FROM ph.price_date), TO_CHAR(ph.price_date, 'Month'), pc.name
ORDER BY month, pc.name;

-- =====================================================================
-- 5. PRICE ALERT QUERIES
-- =====================================================================

-- Products that dropped below alert thresholds
SELECT 
    pa.id as alert_id,
    p.name as product_name,
    s.name as supermarket_name,
    pa.target_price,
    cp.price as current_price,
    pa.target_price - cp.price as price_difference,
    pa.user_email,
    pa.created_at as alert_created
FROM price_alerts pa
JOIN products p ON pa.product_id = p.id
LEFT JOIN supermarkets s ON pa.supermarket_id = s.id
JOIN current_prices cp ON p.id = cp.product_id 
    AND (pa.supermarket_id IS NULL OR cp.supermarket_id = pa.supermarket_id)
WHERE pa.is_active = true
  AND pa.alert_type = 'price_drop'
  AND cp.price <= pa.target_price
  AND cp.is_available = true;

-- Products back in stock (for stock alerts)
SELECT 
    pa.id as alert_id,
    p.name as product_name,
    s.name as supermarket_name,
    cp.price as current_price,
    cp.stock_status,
    pa.user_email,
    pa.created_at as alert_created
FROM price_alerts pa
JOIN products p ON pa.product_id = p.id
LEFT JOIN supermarkets s ON pa.supermarket_id = s.id
JOIN current_prices cp ON p.id = cp.product_id 
    AND (pa.supermarket_id IS NULL OR cp.supermarket_id = pa.supermarket_id)
WHERE pa.is_active = true
  AND pa.alert_type = 'back_in_stock'
  AND cp.is_available = true
  AND cp.stock_status = 'in_stock';

-- =====================================================================
-- 6. ADVANCED ANALYTICS
-- =====================================================================

-- Market basket analysis - Products frequently bought together
WITH product_combinations AS (
    SELECT 
        p1.name as product_1,
        p2.name as product_2,
        COUNT(*) as co_occurrence_count
    FROM current_prices cp1
    JOIN current_prices cp2 ON cp1.supermarket_id = cp2.supermarket_id
    JOIN products p1 ON cp1.product_id = p1.id
    JOIN products p2 ON cp2.product_id = p2.id
    WHERE cp1.product_id < cp2.product_id  -- Avoid duplicates
      AND cp1.is_available = true
      AND cp2.is_available = true
      AND p1.category_id = p2.category_id  -- Same category
    GROUP BY p1.name, p2.name
    HAVING COUNT(*) >= 5  -- At least 5 supermarkets carry both
)
SELECT 
    product_1,
    product_2,
    co_occurrence_count,
    ROUND(co_occurrence_count::DECIMAL / (SELECT COUNT(*) FROM supermarkets WHERE is_active = true) * 100, 2) as availability_percentage
FROM product_combinations
ORDER BY co_occurrence_count DESC;

-- Price elasticity analysis (price vs. availability correlation)
SELECT 
    pc.name as category_name,
    AVG(cp.price) as avg_price,
    COUNT(*) as total_products,
    COUNT(CASE WHEN cp.is_available THEN 1 END) as available_products,
    ROUND(COUNT(CASE WHEN cp.is_available THEN 1 END)::DECIMAL / COUNT(*) * 100, 2) as availability_percentage,
    CORR(cp.price, CASE WHEN cp.is_available THEN 1 ELSE 0 END) as price_availability_correlation
FROM current_prices cp
JOIN products p ON cp.product_id = p.id
JOIN product_categories pc ON p.category_id = pc.id
GROUP BY pc.name
ORDER BY price_availability_correlation DESC;

-- Competitive pricing analysis
WITH price_rankings AS (
    SELECT 
        p.name as product_name,
        s.name as supermarket_name,
        cp.price,
        RANK() OVER (PARTITION BY p.id ORDER BY cp.price ASC) as price_rank,
        COUNT(*) OVER (PARTITION BY p.id) as total_supermarkets
    FROM current_prices cp
    JOIN products p ON cp.product_id = p.id
    JOIN supermarkets s ON cp.supermarket_id = s.id
    WHERE cp.is_available = true
)
SELECT 
    supermarket_name,
    COUNT(*) as total_products,
    COUNT(CASE WHEN price_rank = 1 THEN 1 END) as cheapest_count,
    COUNT(CASE WHEN price_rank = total_supermarkets THEN 1 END) as most_expensive_count,
    ROUND(COUNT(CASE WHEN price_rank = 1 THEN 1 END)::DECIMAL / COUNT(*) * 100, 2) as cheapest_percentage,
    AVG(price_rank) as avg_price_rank
FROM price_rankings
GROUP BY supermarket_name
ORDER BY cheapest_percentage DESC;

-- =====================================================================
-- 7. PERFORMANCE MONITORING QUERIES
-- =====================================================================

-- Check partition sizes and performance
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation,
    most_common_vals
FROM pg_stats 
WHERE tablename LIKE 'price_history%'
ORDER BY tablename, attname;

-- Index usage statistics
SELECT 
    schemaname,
    tablename,
    attname,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename IN ('current_prices', 'price_history', 'products', 'supermarkets')
ORDER BY idx_scan DESC;

-- Query performance for common operations
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) 
SELECT 
    p.name,
    s.name,
    cp.price,
    cp.last_updated
FROM current_prices cp
JOIN products p ON cp.product_id = p.id
JOIN supermarkets s ON cp.supermarket_id = s.id
WHERE p.name ILIKE '%melk%'
  AND cp.is_available = true
ORDER BY cp.price;

-- =====================================================================
-- 8. DATA QUALITY QUERIES
-- =====================================================================

-- Check for missing or invalid data
SELECT 
    'Missing product names' as issue_type,
    COUNT(*) as count
FROM products 
WHERE name IS NULL OR name = ''
UNION ALL
SELECT 
    'Invalid prices' as issue_type,
    COUNT(*) as count
FROM current_prices 
WHERE price <= 0 OR price > 1000
UNION ALL
SELECT 
    'Missing categories' as issue_type,
    COUNT(*) as count
FROM products 
WHERE category_id IS NULL
UNION ALL
SELECT 
    'Stale current prices' as issue_type,
    COUNT(*) as count
FROM current_prices 
WHERE last_updated < CURRENT_DATE - INTERVAL '7 days';

-- Data completeness report
SELECT 
    'Products' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN name IS NOT NULL THEN 1 END) as name_filled,
    COUNT(CASE WHEN brand IS NOT NULL THEN 1 END) as brand_filled,
    COUNT(CASE WHEN category_id IS NOT NULL THEN 1 END) as category_filled,
    COUNT(CASE WHEN size_text IS NOT NULL THEN 1 END) as size_filled,
    COUNT(CASE WHEN ean IS NOT NULL THEN 1 END) as ean_filled
FROM products
UNION ALL
SELECT 
    'Current Prices' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN price > 0 THEN 1 END) as valid_prices,
    COUNT(CASE WHEN price_per_unit > 0 THEN 1 END) as unit_prices,
    COUNT(CASE WHEN is_available = true THEN 1 END) as available,
    COUNT(CASE WHEN last_updated > CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as recent_updates,
    COUNT(CASE WHEN confidence_score >= 90 THEN 1 END) as high_confidence
FROM current_prices;

-- =====================================================================
-- 9. MAINTENANCE QUERIES
-- =====================================================================

-- Clean up old price alerts
DELETE FROM price_alerts 
WHERE expires_at < CURRENT_DATE
   OR (last_triggered IS NOT NULL AND last_triggered < CURRENT_DATE - INTERVAL '30 days');

-- Update price statistics for last month
SELECT calculate_price_statistics(
    NULL, -- all products
    NULL, -- all supermarkets
    'monthly',
    DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'),
    DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 day'
);

-- Archive old price history (older than 2 years)
SELECT archive_old_price_history(CURRENT_DATE - INTERVAL '2 years');

-- =====================================================================
-- 10. REPORTING QUERIES
-- =====================================================================

-- Monthly summary report
SELECT 
    TO_CHAR(ph.price_date, 'YYYY-MM') as month,
    COUNT(DISTINCT ph.product_id) as unique_products,
    COUNT(DISTINCT ph.supermarket_id) as active_supermarkets,
    COUNT(*) as total_price_records,
    AVG(ph.price) as avg_price,
    COUNT(CASE WHEN ph.is_on_sale THEN 1 END) as sale_records,
    COUNT(CASE WHEN ph.price_change > 0 THEN 1 END) as price_increases,
    COUNT(CASE WHEN ph.price_change < 0 THEN 1 END) as price_decreases
FROM price_history ph
WHERE ph.price_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY TO_CHAR(ph.price_date, 'YYYY-MM')
ORDER BY month DESC;

-- Top performing products (most tracked)
SELECT 
    p.name as product_name,
    p.brand,
    pc.name as category_name,
    COUNT(DISTINCT ph.supermarket_id) as supermarket_count,
    COUNT(*) as total_records,
    AVG(ph.price) as avg_price,
    MIN(ph.price) as min_price,
    MAX(ph.price) as max_price,
    STDDEV(ph.price) as price_volatility
FROM price_history ph
JOIN products p ON ph.product_id = p.id
JOIN product_categories pc ON p.category_id = pc.id
WHERE ph.price_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY p.name, p.brand, pc.name
ORDER BY supermarket_count DESC, total_records DESC
LIMIT 20;

-- =====================================================================
-- SAMPLE STORED PROCEDURE CALLS
-- =====================================================================

-- Update current prices from today's price history
SELECT update_current_prices_from_history();

-- Calculate monthly statistics for all products
SELECT calculate_price_statistics(
    NULL, -- all products
    NULL, -- all supermarkets  
    'monthly',
    CURRENT_DATE - INTERVAL '1 month',
    CURRENT_DATE
);

-- Archive price history older than 2 years
SELECT archive_old_price_history(CURRENT_DATE - INTERVAL '2 years');

-- =====================================================================
-- PERFORMANCE BENCHMARKING
-- =====================================================================

-- Benchmark current price lookups
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM v_current_prices 
WHERE product_name ILIKE '%melk%' 
ORDER BY price 
LIMIT 10;

-- Benchmark price history queries
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM v_price_trends 
WHERE product_name ILIKE '%coca cola%' 
  AND price_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY price_date DESC;

-- Benchmark price comparison queries
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM v_price_comparison 
WHERE category_name = 'Zuivel & Eieren'
ORDER BY best_price
LIMIT 20;