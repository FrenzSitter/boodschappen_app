-- =====================================================================
-- Supabase Price History Schema
-- =====================================================================
-- Optimized database schema for tracking supermarket product price 
-- history over time with efficient storage and fast queries.
-- 
-- Features:
-- - Time-series price tracking
-- - Fast current price queries
-- - Efficient trend analysis
-- - Product variations support
-- - Partitioned storage for scale
-- - Comprehensive indexing
-- =====================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_partman";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================================
-- CORE MASTER DATA TABLES
-- =====================================================================

-- Supermarkets table - Master data for all supermarket chains
CREATE TABLE IF NOT EXISTS supermarkets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(50) NOT NULL UNIQUE,
    
    -- CheckjeBon integration
    checkjebon_key VARCHAR(50) UNIQUE,
    
    -- Display information
    logo_url TEXT,
    website_url TEXT,
    color_primary VARCHAR(7),
    color_secondary VARCHAR(7),
    
    -- Business information
    country VARCHAR(2) DEFAULT 'NL',
    currency VARCHAR(3) DEFAULT 'EUR',
    timezone VARCHAR(50) DEFAULT 'Europe/Amsterdam',
    
    -- Status and metadata
    is_active BOOLEAN DEFAULT true,
    has_online_data BOOLEAN DEFAULT true,
    data_update_frequency INTEGER DEFAULT 1440, -- minutes (daily)
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_data_sync TIMESTAMP WITH TIME ZONE
);

-- Product categories table - Hierarchical categorization
CREATE TABLE IF NOT EXISTS product_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    
    -- Hierarchy support
    parent_id UUID REFERENCES product_categories(id) ON DELETE CASCADE,
    path TEXT, -- Materialized path for efficient queries
    level INTEGER DEFAULT 0,
    
    -- Localization
    name_nl VARCHAR(200),
    name_en VARCHAR(200),
    description TEXT,
    
    -- Classification
    dutch_keywords TEXT[],
    search_terms TEXT[],
    
    -- Display
    icon_name VARCHAR(50),
    display_order INTEGER DEFAULT 0,
    color VARCHAR(7),
    
    -- Metadata
    is_active BOOLEAN DEFAULT true,
    product_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Products table - Master product information
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Core product information
    name VARCHAR(500) NOT NULL,
    normalized_name VARCHAR(500) NOT NULL,
    brand VARCHAR(100),
    
    -- Unique identifiers
    ean VARCHAR(20), -- European Article Number
    sku VARCHAR(100), -- Stock Keeping Unit
    checkjebon_id VARCHAR(100),
    
    -- Categorization
    category_id UUID REFERENCES product_categories(id) ON DELETE SET NULL,
    subcategory_id UUID REFERENCES product_categories(id) ON DELETE SET NULL,
    
    -- Product specifications
    description TEXT,
    ingredients TEXT,
    allergens TEXT[],
    nutritional_info JSONB,
    
    -- Size and packaging
    size_text VARCHAR(200),
    size_value DECIMAL(10,3),
    size_unit VARCHAR(20),
    package_type VARCHAR(50),
    
    -- Product attributes
    is_organic BOOLEAN DEFAULT false,
    is_bio BOOLEAN DEFAULT false,
    is_fair_trade BOOLEAN DEFAULT false,
    is_private_label BOOLEAN DEFAULT false,
    is_seasonal BOOLEAN DEFAULT false,
    
    -- Media
    image_url TEXT,
    image_urls TEXT[],
    
    -- Full-text search
    search_vector TSVECTOR,
    
    -- Data quality
    quality_score INTEGER DEFAULT 100 CHECK (quality_score >= 0 AND quality_score <= 100),
    data_completeness DECIMAL(3,2) DEFAULT 1.0,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_discontinued BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_verified TIMESTAMP WITH TIME ZONE,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Product variations table - Handle size/brand variations
CREATE TABLE IF NOT EXISTS product_variations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relationships
    master_product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    variation_product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    
    -- Variation type
    variation_type VARCHAR(50) NOT NULL, -- 'size', 'brand', 'package', 'flavor'
    variation_value VARCHAR(200),
    
    -- Similarity score
    similarity_score DECIMAL(3,2) DEFAULT 1.0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(50) DEFAULT 'system',
    
    UNIQUE(master_product_id, variation_product_id),
    CHECK (master_product_id != variation_product_id)
);

-- =====================================================================
-- CURRENT PRICES TABLE - Fast access to latest prices
-- =====================================================================

-- Current prices table - Optimized for fast current price queries
CREATE TABLE IF NOT EXISTS current_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Product and supermarket
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    supermarket_id UUID NOT NULL REFERENCES supermarkets(id) ON DELETE CASCADE,
    
    -- Price information
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    original_price DECIMAL(10,2) CHECK (original_price >= 0),
    price_per_unit DECIMAL(10,4) CHECK (price_per_unit >= 0),
    
    -- Currency (future-proofing)
    currency VARCHAR(3) DEFAULT 'EUR',
    
    -- Discount information
    discount_amount DECIMAL(10,2) DEFAULT 0,
    discount_percentage DECIMAL(5,2) DEFAULT 0,
    is_on_sale BOOLEAN DEFAULT false,
    
    -- Sale period
    sale_start_date DATE,
    sale_end_date DATE,
    sale_type VARCHAR(50), -- 'percentage', 'fixed_amount', 'bogo', '2_for_1'
    
    -- Availability
    is_available BOOLEAN DEFAULT true,
    stock_status VARCHAR(20) DEFAULT 'in_stock', -- 'in_stock', 'low_stock', 'out_of_stock'
    
    -- Data source and quality
    data_source VARCHAR(50) DEFAULT 'checkjebon',
    confidence_score INTEGER DEFAULT 100 CHECK (confidence_score >= 0 AND confidence_score <= 100),
    
    -- Timestamps
    effective_date DATE NOT NULL DEFAULT CURRENT_DATE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure unique current price per product per supermarket
    UNIQUE(product_id, supermarket_id)
);

-- =====================================================================
-- PRICE HISTORY TABLE - Partitioned for efficient time-series storage
-- =====================================================================

-- Price history table - Time-series data with partitioning
CREATE TABLE IF NOT EXISTS price_history (
    id UUID DEFAULT uuid_generate_v4(),
    
    -- Product and supermarket
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    supermarket_id UUID NOT NULL REFERENCES supermarkets(id) ON DELETE CASCADE,
    
    -- Date (partition key)
    price_date DATE NOT NULL,
    
    -- Price information
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    original_price DECIMAL(10,2) CHECK (original_price >= 0),
    price_per_unit DECIMAL(10,4) CHECK (price_per_unit >= 0),
    
    -- Currency
    currency VARCHAR(3) DEFAULT 'EUR',
    
    -- Price change tracking
    price_change DECIMAL(10,2) DEFAULT 0,
    price_change_percentage DECIMAL(5,2) DEFAULT 0,
    previous_price DECIMAL(10,2),
    
    -- Discount information
    discount_amount DECIMAL(10,2) DEFAULT 0,
    discount_percentage DECIMAL(5,2) DEFAULT 0,
    is_on_sale BOOLEAN DEFAULT false,
    
    -- Sale information
    sale_start_date DATE,
    sale_end_date DATE,
    sale_type VARCHAR(50),
    
    -- Availability
    is_available BOOLEAN DEFAULT true,
    stock_status VARCHAR(20) DEFAULT 'in_stock',
    
    -- Data source and quality
    data_source VARCHAR(50) DEFAULT 'checkjebon',
    confidence_score INTEGER DEFAULT 100 CHECK (confidence_score >= 0 AND confidence_score <= 100),
    import_batch_id UUID,
    
    -- Change tracking
    change_type VARCHAR(20) DEFAULT 'update', -- 'new', 'update', 'discontinued'
    change_reason VARCHAR(100),
    
    -- Timestamps
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Composite primary key including partition key
    PRIMARY KEY (id, price_date),
    
    -- Unique constraint to prevent duplicate daily entries
    UNIQUE(product_id, supermarket_id, price_date)
) PARTITION BY RANGE (price_date);

-- =====================================================================
-- PARTITION MANAGEMENT FOR PRICE HISTORY
-- =====================================================================

-- Create initial partitions (current year and next year)
DO $$
DECLARE
    start_date DATE := DATE_TRUNC('year', CURRENT_DATE);
    end_date DATE := start_date + INTERVAL '1 year';
BEGIN
    -- Create partition for current year
    EXECUTE format('CREATE TABLE IF NOT EXISTS price_history_%s PARTITION OF price_history 
                    FOR VALUES FROM (%L) TO (%L)', 
                    EXTRACT(YEAR FROM start_date), 
                    start_date, 
                    end_date);
    
    -- Create partition for next year
    start_date := end_date;
    end_date := start_date + INTERVAL '1 year';
    
    EXECUTE format('CREATE TABLE IF NOT EXISTS price_history_%s PARTITION OF price_history 
                    FOR VALUES FROM (%L) TO (%L)', 
                    EXTRACT(YEAR FROM start_date), 
                    start_date, 
                    end_date);
END $$;

-- =====================================================================
-- PRICE ALERTS TABLE - User-defined price monitoring
-- =====================================================================

-- Price alerts table - User-defined price thresholds
CREATE TABLE IF NOT EXISTS price_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- User information (for future user system)
    user_id UUID,
    user_email VARCHAR(255),
    
    -- Product and supermarket
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    supermarket_id UUID REFERENCES supermarkets(id) ON DELETE CASCADE, -- NULL = any supermarket
    
    -- Alert conditions
    alert_type VARCHAR(20) NOT NULL CHECK (alert_type IN ('price_drop', 'price_increase', 'back_in_stock', 'on_sale')),
    target_price DECIMAL(10,2),
    threshold_percentage DECIMAL(5,2),
    
    -- Alert settings
    is_active BOOLEAN DEFAULT true,
    notification_method VARCHAR(20) DEFAULT 'email', -- 'email', 'webhook', 'sms'
    webhook_url TEXT,
    
    -- Tracking
    last_triggered TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    max_triggers INTEGER DEFAULT 10,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- =====================================================================
-- PRICE STATISTICS TABLE - Aggregated price metrics
-- =====================================================================

-- Price statistics table - Pre-computed aggregations for performance
CREATE TABLE IF NOT EXISTS price_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Product and supermarket
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    supermarket_id UUID REFERENCES supermarkets(id) ON DELETE CASCADE, -- NULL = all supermarkets
    
    -- Time period
    period_type VARCHAR(20) NOT NULL CHECK (period_type IN ('daily', 'weekly', 'monthly', 'yearly')),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Price statistics
    min_price DECIMAL(10,2) NOT NULL,
    max_price DECIMAL(10,2) NOT NULL,
    avg_price DECIMAL(10,2) NOT NULL,
    median_price DECIMAL(10,2),
    
    -- Availability statistics
    days_available INTEGER,
    days_on_sale INTEGER,
    avg_discount_percentage DECIMAL(5,2),
    
    -- Change statistics
    price_volatility DECIMAL(10,4), -- Standard deviation
    total_price_changes INTEGER,
    largest_price_drop DECIMAL(10,2),
    largest_price_increase DECIMAL(10,2),
    
    -- Metadata
    data_points INTEGER,
    last_calculated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(product_id, supermarket_id, period_type, period_start)
);

-- =====================================================================
-- COMPREHENSIVE INDEXING STRATEGY
-- =====================================================================

-- Supermarkets indexes
CREATE INDEX IF NOT EXISTS idx_supermarkets_active ON supermarkets(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_supermarkets_slug ON supermarkets(slug);
CREATE INDEX IF NOT EXISTS idx_supermarkets_checkjebon_key ON supermarkets(checkjebon_key);

-- Product categories indexes
CREATE INDEX IF NOT EXISTS idx_categories_parent ON product_categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_categories_active ON product_categories(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_categories_path ON product_categories USING gin(path gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_categories_keywords ON product_categories USING gin(dutch_keywords);

-- Products indexes - Optimized for search and filtering
CREATE INDEX IF NOT EXISTS idx_products_name ON products USING gin(to_tsvector('dutch', name));
CREATE INDEX IF NOT EXISTS idx_products_normalized_name ON products(normalized_name);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_ean ON products(ean) WHERE ean IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku) WHERE sku IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_checkjebon_id ON products(checkjebon_id) WHERE checkjebon_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_products_search_vector ON products USING gin(search_vector);
CREATE INDEX IF NOT EXISTS idx_products_size_value ON products(size_value) WHERE size_value IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_organic ON products(is_organic) WHERE is_organic = true;
CREATE INDEX IF NOT EXISTS idx_products_updated_at ON products(updated_at DESC);

-- Product variations indexes
CREATE INDEX IF NOT EXISTS idx_variations_master ON product_variations(master_product_id);
CREATE INDEX IF NOT EXISTS idx_variations_variation ON product_variations(variation_product_id);
CREATE INDEX IF NOT EXISTS idx_variations_type ON product_variations(variation_type);

-- Current prices indexes - Critical for performance
CREATE INDEX IF NOT EXISTS idx_current_prices_product ON current_prices(product_id);
CREATE INDEX IF NOT EXISTS idx_current_prices_supermarket ON current_prices(supermarket_id);
CREATE INDEX IF NOT EXISTS idx_current_prices_price ON current_prices(price);
CREATE INDEX IF NOT EXISTS idx_current_prices_available ON current_prices(is_available) WHERE is_available = true;
CREATE INDEX IF NOT EXISTS idx_current_prices_sale ON current_prices(is_on_sale) WHERE is_on_sale = true;
CREATE INDEX IF NOT EXISTS idx_current_prices_updated ON current_prices(last_updated DESC);
CREATE INDEX IF NOT EXISTS idx_current_prices_composite ON current_prices(product_id, supermarket_id, is_available);

-- Price history indexes - Optimized for time-series queries
CREATE INDEX IF NOT EXISTS idx_price_history_product_date ON price_history(product_id, price_date DESC);
CREATE INDEX IF NOT EXISTS idx_price_history_supermarket_date ON price_history(supermarket_id, price_date DESC);
CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(price_date DESC);
CREATE INDEX IF NOT EXISTS idx_price_history_product_supermarket ON price_history(product_id, supermarket_id, price_date DESC);
CREATE INDEX IF NOT EXISTS idx_price_history_price ON price_history(price);
CREATE INDEX IF NOT EXISTS idx_price_history_change ON price_history(price_change) WHERE price_change != 0;
CREATE INDEX IF NOT EXISTS idx_price_history_available ON price_history(is_available) WHERE is_available = true;
CREATE INDEX IF NOT EXISTS idx_price_history_batch ON price_history(import_batch_id) WHERE import_batch_id IS NOT NULL;

-- Price alerts indexes
CREATE INDEX IF NOT EXISTS idx_price_alerts_product ON price_alerts(product_id);
CREATE INDEX IF NOT EXISTS idx_price_alerts_supermarket ON price_alerts(supermarket_id);
CREATE INDEX IF NOT EXISTS idx_price_alerts_active ON price_alerts(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_price_alerts_user ON price_alerts(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_price_alerts_type ON price_alerts(alert_type);

-- Price statistics indexes
CREATE INDEX IF NOT EXISTS idx_price_stats_product ON price_statistics(product_id);
CREATE INDEX IF NOT EXISTS idx_price_stats_period ON price_statistics(period_type, period_start);
CREATE INDEX IF NOT EXISTS idx_price_stats_product_period ON price_statistics(product_id, period_type, period_start);

-- =====================================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================================

-- Current prices view with product and supermarket details
CREATE OR REPLACE VIEW v_current_prices AS
SELECT 
    cp.id,
    cp.product_id,
    cp.supermarket_id,
    p.name as product_name,
    p.brand as product_brand,
    p.size_text as product_size,
    p.ean as product_ean,
    s.name as supermarket_name,
    s.slug as supermarket_slug,
    cp.price,
    cp.original_price,
    cp.price_per_unit,
    cp.discount_amount,
    cp.discount_percentage,
    cp.is_on_sale,
    cp.sale_start_date,
    cp.sale_end_date,
    cp.is_available,
    cp.stock_status,
    cp.effective_date,
    cp.last_updated,
    pc.name as category_name,
    pc.slug as category_slug
FROM current_prices cp
JOIN products p ON cp.product_id = p.id
JOIN supermarkets s ON cp.supermarket_id = s.id
LEFT JOIN product_categories pc ON p.category_id = pc.id
WHERE cp.is_available = true 
  AND s.is_active = true 
  AND p.is_active = true;

-- Price comparison view - Best prices across supermarkets
CREATE OR REPLACE VIEW v_price_comparison AS
WITH ranked_prices AS (
    SELECT 
        product_id,
        supermarket_id,
        price,
        price_per_unit,
        is_on_sale,
        discount_percentage,
        is_available,
        ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY price ASC) as price_rank
    FROM current_prices 
    WHERE is_available = true
)
SELECT 
    p.id as product_id,
    p.name as product_name,
    p.brand as product_brand,
    p.size_text as product_size,
    s.name as supermarket_name,
    s.slug as supermarket_slug,
    rp.price as best_price,
    rp.price_per_unit,
    rp.is_on_sale,
    rp.discount_percentage,
    pc.name as category_name,
    pc.slug as category_slug
FROM ranked_prices rp
JOIN products p ON rp.product_id = p.id
JOIN supermarkets s ON rp.supermarket_id = s.id
LEFT JOIN product_categories pc ON p.category_id = pc.id
WHERE rp.price_rank = 1
  AND p.is_active = true
  AND s.is_active = true;

-- Price trends view - Recent price changes
CREATE OR REPLACE VIEW v_price_trends AS
SELECT 
    ph.product_id,
    ph.supermarket_id,
    p.name as product_name,
    p.brand as product_brand,
    s.name as supermarket_name,
    ph.price_date,
    ph.price,
    ph.price_change,
    ph.price_change_percentage,
    ph.previous_price,
    ph.is_on_sale,
    ph.change_type,
    ph.change_reason,
    -- Calculate 7-day moving average
    AVG(ph.price) OVER (
        PARTITION BY ph.product_id, ph.supermarket_id 
        ORDER BY ph.price_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as price_7day_avg,
    -- Calculate price volatility
    STDDEV(ph.price) OVER (
        PARTITION BY ph.product_id, ph.supermarket_id 
        ORDER BY ph.price_date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as price_volatility_30d
FROM price_history ph
JOIN products p ON ph.product_id = p.id
JOIN supermarkets s ON ph.supermarket_id = s.id
WHERE ph.price_date >= CURRENT_DATE - INTERVAL '90 days'
  AND p.is_active = true
  AND s.is_active = true;

-- Product availability view
CREATE OR REPLACE VIEW v_product_availability AS
SELECT 
    p.id as product_id,
    p.name as product_name,
    p.brand as product_brand,
    COUNT(cp.id) as available_supermarkets,
    COUNT(s.id) as total_supermarkets,
    ROUND(COUNT(cp.id)::DECIMAL / COUNT(s.id) * 100, 2) as availability_percentage,
    MIN(cp.price) as min_price,
    MAX(cp.price) as max_price,
    AVG(cp.price) as avg_price,
    COUNT(CASE WHEN cp.is_on_sale THEN 1 END) as supermarkets_on_sale
FROM products p
CROSS JOIN supermarkets s
LEFT JOIN current_prices cp ON p.id = cp.product_id AND s.id = cp.supermarket_id AND cp.is_available = true
WHERE p.is_active = true AND s.is_active = true
GROUP BY p.id, p.name, p.brand
HAVING COUNT(cp.id) > 0;

-- =====================================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================================

-- Function to update product search vector
CREATE OR REPLACE FUNCTION update_product_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('dutch', 
        COALESCE(NEW.name, '') || ' ' ||
        COALESCE(NEW.brand, '') || ' ' ||
        COALESCE(NEW.description, '') || ' ' ||
        COALESCE(NEW.size_text, '') || ' ' ||
        COALESCE(array_to_string(NEW.allergens, ' '), '')
    );
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to update normalized product name
CREATE OR REPLACE FUNCTION update_normalized_product_name()
RETURNS TRIGGER AS $$
BEGIN
    NEW.normalized_name := LOWER(TRIM(REGEXP_REPLACE(NEW.name, '[^a-zA-Z0-9\s]', '', 'g')));
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to update category materialized path
CREATE OR REPLACE FUNCTION update_category_path()
RETURNS TRIGGER AS $$
DECLARE
    parent_path TEXT;
BEGIN
    IF NEW.parent_id IS NULL THEN
        NEW.path := NEW.id::TEXT;
        NEW.level := 0;
    ELSE
        SELECT path, level INTO parent_path, NEW.level 
        FROM product_categories 
        WHERE id = NEW.parent_id;
        
        NEW.path := parent_path || '.' || NEW.id::TEXT;
        NEW.level := NEW.level + 1;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to track price changes
CREATE OR REPLACE FUNCTION track_price_changes()
RETURNS TRIGGER AS $$
DECLARE
    old_price DECIMAL(10,2);
    price_diff DECIMAL(10,2);
    price_diff_pct DECIMAL(5,2);
BEGIN
    -- Get the previous price from current_prices
    SELECT price INTO old_price 
    FROM current_prices 
    WHERE product_id = NEW.product_id 
      AND supermarket_id = NEW.supermarket_id;
    
    -- Calculate price change
    IF old_price IS NOT NULL AND old_price != NEW.price THEN
        price_diff := NEW.price - old_price;
        price_diff_pct := CASE 
            WHEN old_price > 0 THEN (price_diff / old_price) * 100 
            ELSE 0 
        END;
        
        NEW.price_change := price_diff;
        NEW.price_change_percentage := price_diff_pct;
        NEW.previous_price := old_price;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to update product category counts
CREATE OR REPLACE FUNCTION update_category_product_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Update old category count
    IF OLD.category_id IS NOT NULL THEN
        UPDATE product_categories 
        SET product_count = product_count - 1
        WHERE id = OLD.category_id;
    END IF;
    
    -- Update new category count
    IF NEW.category_id IS NOT NULL THEN
        UPDATE product_categories 
        SET product_count = product_count + 1
        WHERE id = NEW.category_id;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =====================================================================
-- TRIGGER DEFINITIONS
-- =====================================================================

-- Product triggers
DROP TRIGGER IF EXISTS update_products_search_vector ON products;
CREATE TRIGGER update_products_search_vector
    BEFORE INSERT OR UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_product_search_vector();

DROP TRIGGER IF EXISTS update_products_normalized_name ON products;
CREATE TRIGGER update_products_normalized_name
    BEFORE INSERT OR UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_normalized_product_name();

DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_products_category_count ON products;
CREATE TRIGGER update_products_category_count
    AFTER UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_category_product_count();

-- Category triggers
DROP TRIGGER IF EXISTS update_categories_path ON product_categories;
CREATE TRIGGER update_categories_path
    BEFORE INSERT OR UPDATE ON product_categories
    FOR EACH ROW EXECUTE FUNCTION update_category_path();

DROP TRIGGER IF EXISTS update_categories_updated_at ON product_categories;
CREATE TRIGGER update_categories_updated_at
    BEFORE UPDATE ON product_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Price history triggers
DROP TRIGGER IF EXISTS track_price_history_changes ON price_history;
CREATE TRIGGER track_price_history_changes
    BEFORE INSERT ON price_history
    FOR EACH ROW EXECUTE FUNCTION track_price_changes();

-- Supermarket triggers
DROP TRIGGER IF EXISTS update_supermarkets_updated_at ON supermarkets;
CREATE TRIGGER update_supermarkets_updated_at
    BEFORE UPDATE ON supermarkets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================================
-- STORED PROCEDURES FOR COMMON OPERATIONS
-- =====================================================================

-- Procedure to update current prices from price history
CREATE OR REPLACE FUNCTION update_current_prices_from_history()
RETURNS VOID AS $$
BEGIN
    INSERT INTO current_prices (
        product_id, supermarket_id, price, original_price, price_per_unit,
        discount_amount, discount_percentage, is_on_sale,
        sale_start_date, sale_end_date, sale_type,
        is_available, stock_status, data_source, confidence_score,
        effective_date, last_updated
    )
    SELECT DISTINCT ON (product_id, supermarket_id)
        product_id, supermarket_id, price, original_price, price_per_unit,
        discount_amount, discount_percentage, is_on_sale,
        sale_start_date, sale_end_date, sale_type,
        is_available, stock_status, data_source, confidence_score,
        price_date, recorded_at
    FROM price_history
    WHERE price_date = CURRENT_DATE
    ORDER BY product_id, supermarket_id, recorded_at DESC
    ON CONFLICT (product_id, supermarket_id)
    DO UPDATE SET
        price = EXCLUDED.price,
        original_price = EXCLUDED.original_price,
        price_per_unit = EXCLUDED.price_per_unit,
        discount_amount = EXCLUDED.discount_amount,
        discount_percentage = EXCLUDED.discount_percentage,
        is_on_sale = EXCLUDED.is_on_sale,
        sale_start_date = EXCLUDED.sale_start_date,
        sale_end_date = EXCLUDED.sale_end_date,
        sale_type = EXCLUDED.sale_type,
        is_available = EXCLUDED.is_available,
        stock_status = EXCLUDED.stock_status,
        data_source = EXCLUDED.data_source,
        confidence_score = EXCLUDED.confidence_score,
        effective_date = EXCLUDED.effective_date,
        last_updated = EXCLUDED.last_updated;
END;
$$ LANGUAGE plpgsql;

-- Procedure to calculate price statistics
CREATE OR REPLACE FUNCTION calculate_price_statistics(
    p_product_id UUID DEFAULT NULL,
    p_supermarket_id UUID DEFAULT NULL,
    p_period_type VARCHAR DEFAULT 'monthly',
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL
)
RETURNS VOID AS $$
DECLARE
    start_date DATE;
    end_date DATE;
BEGIN
    -- Set default date range
    IF p_start_date IS NULL THEN
        start_date := CURRENT_DATE - INTERVAL '1 year';
    ELSE
        start_date := p_start_date;
    END IF;
    
    IF p_end_date IS NULL THEN
        end_date := CURRENT_DATE;
    ELSE
        end_date := p_end_date;
    END IF;
    
    -- Calculate statistics
    INSERT INTO price_statistics (
        product_id, supermarket_id, period_type, period_start, period_end,
        min_price, max_price, avg_price, median_price,
        days_available, days_on_sale, avg_discount_percentage,
        price_volatility, total_price_changes, largest_price_drop, largest_price_increase,
        data_points
    )
    SELECT 
        ph.product_id,
        ph.supermarket_id,
        p_period_type,
        start_date,
        end_date,
        MIN(ph.price) as min_price,
        MAX(ph.price) as max_price,
        AVG(ph.price) as avg_price,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ph.price) as median_price,
        COUNT(CASE WHEN ph.is_available THEN 1 END) as days_available,
        COUNT(CASE WHEN ph.is_on_sale THEN 1 END) as days_on_sale,
        AVG(ph.discount_percentage) as avg_discount_percentage,
        STDDEV(ph.price) as price_volatility,
        COUNT(CASE WHEN ph.price_change != 0 THEN 1 END) as total_price_changes,
        MIN(ph.price_change) as largest_price_drop,
        MAX(ph.price_change) as largest_price_increase,
        COUNT(*) as data_points
    FROM price_history ph
    WHERE ph.price_date BETWEEN start_date AND end_date
      AND (p_product_id IS NULL OR ph.product_id = p_product_id)
      AND (p_supermarket_id IS NULL OR ph.supermarket_id = p_supermarket_id)
    GROUP BY ph.product_id, ph.supermarket_id
    ON CONFLICT (product_id, supermarket_id, period_type, period_start)
    DO UPDATE SET
        period_end = EXCLUDED.period_end,
        min_price = EXCLUDED.min_price,
        max_price = EXCLUDED.max_price,
        avg_price = EXCLUDED.avg_price,
        median_price = EXCLUDED.median_price,
        days_available = EXCLUDED.days_available,
        days_on_sale = EXCLUDED.days_on_sale,
        avg_discount_percentage = EXCLUDED.avg_discount_percentage,
        price_volatility = EXCLUDED.price_volatility,
        total_price_changes = EXCLUDED.total_price_changes,
        largest_price_drop = EXCLUDED.largest_price_drop,
        largest_price_increase = EXCLUDED.largest_price_increase,
        data_points = EXCLUDED.data_points,
        last_calculated = NOW();
END;
$$ LANGUAGE plpgsql;

-- Procedure to archive old price history data
CREATE OR REPLACE FUNCTION archive_old_price_history(p_cutoff_date DATE DEFAULT NULL)
RETURNS INTEGER AS $$
DECLARE
    cutoff_date DATE;
    archived_count INTEGER;
BEGIN
    -- Set default cutoff date (2 years ago)
    IF p_cutoff_date IS NULL THEN
        cutoff_date := CURRENT_DATE - INTERVAL '2 years';
    ELSE
        cutoff_date := p_cutoff_date;
    END IF;
    
    -- Create archive table if it doesn't exist
    CREATE TABLE IF NOT EXISTS price_history_archive (
        LIKE price_history INCLUDING ALL
    );
    
    -- Move old data to archive
    WITH moved_data AS (
        DELETE FROM price_history 
        WHERE price_date < cutoff_date
        RETURNING *
    )
    INSERT INTO price_history_archive 
    SELECT * FROM moved_data;
    
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- INITIAL DATA SEEDING
-- =====================================================================

-- Insert Dutch supermarkets
INSERT INTO supermarkets (name, slug, checkjebon_key, color_primary, is_active, has_online_data) VALUES 
('Albert Heijn', 'albert-heijn', 'ah', '#0051A5', true, true),
('Jumbo', 'jumbo', 'jumbo', '#FFD800', true, true),
('Plus', 'plus', 'plus', '#E30613', true, true),
('Coop', 'coop', 'coop', '#E30613', true, true),
('Dirk', 'dirk', 'dirk', '#009CDA', true, true),
('Aldi', 'aldi', 'aldi', '#009CDA', true, true),
('Lidl', 'lidl', 'lidl', '#0050AA', true, true),
('Hoogvliet', 'hoogvliet', 'hoogvliet', '#E30613', true, true),
('Vomar', 'vomar', 'vomar', '#009CDA', true, true),
('Spar', 'spar', 'spar', '#00843D', true, true),
('DekaMarkt', 'dekamarkt', 'dekamarkt', '#E30613', true, true)
ON CONFLICT (slug) DO NOTHING;

-- Insert main product categories
INSERT INTO product_categories (id, name, slug, name_nl, name_en, dutch_keywords, display_order) VALUES
(uuid_generate_v4(), 'Zuivel & Eieren', 'zuivel-eieren', 'Zuivel & Eieren', 'Dairy & Eggs', 
 ARRAY['melk', 'yoghurt', 'kaas', 'boter', 'eieren', 'kwark', 'room', 'vla'], 1),
(uuid_generate_v4(), 'Brood & Gebak', 'brood-gebak', 'Brood & Gebak', 'Bread & Bakery', 
 ARRAY['brood', 'stokbrood', 'croissant', 'beschuit', 'cake', 'koek', 'taart'], 2),
(uuid_generate_v4(), 'Groente & Fruit', 'groente-fruit', 'Groente & Fruit', 'Vegetables & Fruit', 
 ARRAY['appel', 'banaan', 'tomaat', 'ui', 'wortel', 'sla', 'komkommer', 'paprika'], 3),
(uuid_generate_v4(), 'Vlees, Vis & Vegetarisch', 'vlees-vis-vegetarisch', 'Vlees, Vis & Vegetarisch', 'Meat, Fish & Vegetarian', 
 ARRAY['vlees', 'kip', 'vis', 'gehakt', 'worst', 'ham', 'vegetarisch', 'vegan'], 4),
(uuid_generate_v4(), 'Dranken', 'dranken', 'Dranken', 'Drinks', 
 ARRAY['cola', 'sap', 'water', 'bier', 'koffie', 'thee', 'wijn', 'frisdrank'], 5),
(uuid_generate_v4(), 'Diepvries', 'diepvries', 'Diepvries', 'Frozen', 
 ARRAY['diepvries', 'frozen', 'ijs', 'ijsje', 'bevroren'], 6),
(uuid_generate_v4(), 'Houdbaar', 'houdbaar', 'Houdbaar', 'Pantry', 
 ARRAY['conserven', 'pasta', 'rijst', 'meel', 'suiker', 'blik'], 7),
(uuid_generate_v4(), 'Snacks & Snoep', 'snacks-snoep', 'Snacks & Snoep', 'Snacks & Candy', 
 ARRAY['chips', 'koekjes', 'chocolade', 'snoep', 'noten', 'reep'], 8),
(uuid_generate_v4(), 'Verzorging', 'verzorging', 'Verzorging', 'Personal Care', 
 ARRAY['shampoo', 'tandpasta', 'zeep', 'deodorant', 'parfum', 'creme'], 9),
(uuid_generate_v4(), 'Huishouden', 'huishouden', 'Huishouden', 'Household', 
 ARRAY['wasmiddel', 'afwasmiddel', 'toiletpapier', 'keukenrol', 'schoonmaak'], 10),
(uuid_generate_v4(), 'Baby & Kind', 'baby-kind', 'Baby & Kind', 'Baby & Child', 
 ARRAY['baby', 'luier', 'flesvoeding', 'kindje', 'pampers'], 11),
(uuid_generate_v4(), 'Dieren', 'dieren', 'Dieren', 'Pets', 
 ARRAY['hond', 'kat', 'voer', 'dier', 'brokken'], 12)
ON CONFLICT (slug) DO NOTHING;

-- =====================================================================
-- PERFORMANCE OPTIMIZATION SETTINGS
-- =====================================================================

-- Analyze tables for better query planning
ANALYZE supermarkets;
ANALYZE product_categories;
ANALYZE products;
ANALYZE current_prices;
ANALYZE price_history;

-- Update table statistics
UPDATE pg_stat_user_tables SET n_tup_upd = n_tup_upd + 1 WHERE relname IN ('supermarkets', 'product_categories', 'products');

-- =====================================================================
-- SUCCESS MESSAGE
-- =====================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Price History Database Schema Created Successfully!';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Schema Features:';
    RAISE NOTICE '   • Time-series price tracking with partitioning';
    RAISE NOTICE '   • Fast current price queries with dedicated table';
    RAISE NOTICE '   • Comprehensive indexing for performance';
    RAISE NOTICE '   • Product variations and categorization';
    RAISE NOTICE '   • Price statistics and trend analysis';
    RAISE NOTICE '   • Automated archiving for old data';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Next Steps:';
    RAISE NOTICE '   1. Run example queries to test performance';
    RAISE NOTICE '   2. Import your CheckjeBon data';
    RAISE NOTICE '   3. Set up scheduled tasks for maintenance';
    RAISE NOTICE '   4. Configure price alerts as needed';
    RAISE NOTICE '';
    RAISE NOTICE '💡 Key Views Available:';
    RAISE NOTICE '   • v_current_prices - Current prices with product details';
    RAISE NOTICE '   • v_price_comparison - Best prices across supermarkets';
    RAISE NOTICE '   • v_price_trends - Recent price changes and trends';
    RAISE NOTICE '   • v_product_availability - Product availability statistics';
END $$;