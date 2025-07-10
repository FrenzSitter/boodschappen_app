-- =====================================================================
-- CheckjeBon Optimized Supabase Database Schema
-- =====================================================================
-- Designed for 95,289+ products across 11 Dutch supermarkets
-- Optimized for fast price comparisons and multi-supermarket data
-- Based on CheckjeBon JSON structure analysis
-- =====================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================================
-- CORE TABLES
-- =====================================================================

-- Supermarkets table - stores all Dutch supermarket chains
CREATE TABLE IF NOT EXISTS supermarkets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(50) NOT NULL UNIQUE,
    
    -- CheckjeBon specific fields
    checkjebon_key VARCHAR(50) UNIQUE, -- Maps to 'n' field in JSON
    
    -- Display information
    logo_url TEXT,
    website_url TEXT,
    color_primary VARCHAR(7), -- Hex color code
    color_secondary VARCHAR(7),
    
    -- Status and metadata
    is_active BOOLEAN DEFAULT true,
    has_online_data BOOLEAN DEFAULT false, -- Whether we have online pricing
    last_data_update TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Product categories table - hierarchical structure for Dutch products
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) NOT NULL UNIQUE,
    
    -- Hierarchical structure
    parent_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    
    -- Dutch-specific categorization
    dutch_keywords TEXT[], -- Keywords for auto-categorization
    
    -- Display information
    icon_name VARCHAR(50),
    description TEXT,
    display_order INTEGER DEFAULT 0,
    
    -- Metadata
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Products table - core product information
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Core product information
    name VARCHAR(500) NOT NULL, -- Longer for Dutch product names
    normalized_name VARCHAR(500), -- Normalized for search/comparison
    brand VARCHAR(100),
    
    -- CheckjeBon specific fields
    checkjebon_link VARCHAR(500), -- Maps to 'l' field in JSON
    source_supermarket_id UUID REFERENCES supermarkets(id), -- Original source
    
    -- Categorization
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    auto_category VARCHAR(100), -- Auto-inferred category
    
    -- Product identification
    barcode VARCHAR(20),
    sku VARCHAR(100),
    
    -- Product details
    description TEXT,
    size_text VARCHAR(200), -- Maps to 's' field in JSON
    unit_type VARCHAR(20) DEFAULT 'piece', -- piece, kg, liter, gram, ml, etc.
    package_size DECIMAL(10,3), -- Numeric size extracted from size_text
    package_unit VARCHAR(20), -- Unit extracted from size_text
    
    -- Product attributes
    brand_extracted VARCHAR(100), -- Auto-extracted brand
    is_organic BOOLEAN DEFAULT false,
    is_bio BOOLEAN DEFAULT false,
    is_private_label BOOLEAN DEFAULT false,
    
    -- Content information
    ingredients TEXT,
    allergens TEXT[],
    nutritional_info JSONB,
    
    -- Media
    image_url TEXT,
    image_urls TEXT[], -- Multiple images
    
    -- Search optimization
    search_vector TSVECTOR, -- Full-text search
    
    -- Status and metadata
    is_active BOOLEAN DEFAULT true,
    quality_score INTEGER DEFAULT 100, -- Data quality scoring
    last_verified TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Product prices table - current and historical pricing
CREATE TABLE IF NOT EXISTS product_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Core relationships
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    supermarket_id UUID NOT NULL REFERENCES supermarkets(id) ON DELETE CASCADE,
    
    -- Pricing information
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    original_price DECIMAL(10,2), -- For discounts/sales
    price_per_unit DECIMAL(10,4), -- Calculated per kg/liter/piece
    discount_percentage DECIMAL(5,2),
    
    -- Currency and availability
    currency VARCHAR(3) DEFAULT 'EUR',
    is_available BOOLEAN DEFAULT true,
    is_on_sale BOOLEAN DEFAULT false,
    
    -- Sale information
    sale_start_date DATE,
    sale_end_date DATE,
    sale_type VARCHAR(50), -- '2-for-1', 'percentage', 'fixed-amount'
    
    -- Data source and quality
    data_source VARCHAR(50) DEFAULT 'checkjebon', -- 'checkjebon', 'scraper', 'manual'
    confidence_score INTEGER DEFAULT 100, -- 0-100, data reliability
    
    -- CheckjeBon specific
    checkjebon_link VARCHAR(500), -- Product-specific link from JSON
    
    -- Metadata
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure unique current price per product per supermarket
    UNIQUE(product_id, supermarket_id)
);

-- Price history table - track price changes over time
CREATE TABLE IF NOT EXISTS price_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relationships
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    supermarket_id UUID NOT NULL REFERENCES supermarkets(id) ON DELETE CASCADE,
    
    -- Historical pricing
    price DECIMAL(10,2) NOT NULL,
    original_price DECIMAL(10,2),
    price_per_unit DECIMAL(10,4),
    
    -- Change tracking
    price_change DECIMAL(10,2), -- Difference from previous price
    price_change_percentage DECIMAL(5,2),
    
    -- Context
    change_reason VARCHAR(100), -- 'sale_start', 'sale_end', 'regular_update'
    data_source VARCHAR(50) DEFAULT 'checkjebon',
    
    -- Timing
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    effective_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    effective_until TIMESTAMP WITH TIME ZONE
);

-- Product variants table - handle size/packaging variations
CREATE TABLE IF NOT EXISTS product_variants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relationships
    parent_product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    variant_product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    
    -- Variant information
    variant_type VARCHAR(50), -- 'size', 'packaging', 'flavor', 'brand'
    variant_value VARCHAR(200),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(parent_product_id, variant_product_id)
);

-- =====================================================================
-- USER-RELATED TABLES
-- =====================================================================

-- Shopping lists
CREATE TABLE IF NOT EXISTS shopping_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID, -- For future user authentication
    
    -- List information
    name VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- Settings
    preferred_supermarket_id UUID REFERENCES supermarkets(id),
    budget_limit DECIMAL(10,2),
    is_favorite BOOLEAN DEFAULT false,
    is_template BOOLEAN DEFAULT false,
    
    -- Calculated totals
    total_items INTEGER DEFAULT 0,
    total_estimated_price DECIMAL(10,2) DEFAULT 0,
    
    -- Sharing and collaboration
    is_shared BOOLEAN DEFAULT false,
    share_token VARCHAR(100) UNIQUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Shopping list items
CREATE TABLE IF NOT EXISTS shopping_list_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relationships
    shopping_list_id UUID NOT NULL REFERENCES shopping_lists(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    
    -- Item information
    custom_product_name VARCHAR(200), -- For items not in product database
    quantity DECIMAL(8,2) DEFAULT 1,
    unit VARCHAR(20) DEFAULT 'piece',
    
    -- Preferences
    preferred_supermarket_id UUID REFERENCES supermarkets(id) ON DELETE SET NULL,
    max_price DECIMAL(10,2), -- Price alert threshold
    
    -- Status
    is_completed BOOLEAN DEFAULT false,
    is_essential BOOLEAN DEFAULT false,
    
    -- Notes and alternatives
    notes TEXT,
    alternative_products UUID[], -- Array of product IDs
    
    -- Calculated pricing
    estimated_price DECIMAL(10,2),
    best_price DECIMAL(10,2),
    best_price_supermarket_id UUID REFERENCES supermarkets(id),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User favorites and preferences
CREATE TABLE IF NOT EXISTS user_favorites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID, -- For future user authentication
    
    -- Relationships
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    supermarket_id UUID REFERENCES supermarkets(id) ON DELETE SET NULL,
    
    -- Preferences
    preferred_size VARCHAR(100),
    price_alert_threshold DECIMAL(10,2),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, product_id)
);

-- =====================================================================
-- ANALYTICS AND REPORTING TABLES
-- =====================================================================

-- Price alerts
CREATE TABLE IF NOT EXISTS price_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    
    -- Target
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    supermarket_id UUID REFERENCES supermarkets(id) ON DELETE SET NULL,
    
    -- Alert conditions
    target_price DECIMAL(10,2) NOT NULL,
    alert_type VARCHAR(50) DEFAULT 'below', -- 'below', 'above', 'change'
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_triggered TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Search analytics (optional)
CREATE TABLE IF NOT EXISTS search_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Search information
    search_query VARCHAR(500),
    search_type VARCHAR(50), -- 'text', 'category', 'barcode'
    results_count INTEGER,
    
    -- User context
    user_session VARCHAR(100),
    user_location VARCHAR(100),
    
    -- Timestamps
    searched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================================

-- Supermarkets indexes
CREATE INDEX IF NOT EXISTS idx_supermarkets_active ON supermarkets(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_supermarkets_checkjebon_key ON supermarkets(checkjebon_key);

-- Categories indexes
CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_categories_active ON categories(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_categories_keywords ON categories USING gin(dutch_keywords);

-- Products indexes - optimized for search and filtering
CREATE INDEX IF NOT EXISTS idx_products_name ON products USING gin(to_tsvector('dutch', name));
CREATE INDEX IF NOT EXISTS idx_products_normalized_name ON products(normalized_name);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode) WHERE barcode IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_checkjebon_link ON products(checkjebon_link);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_products_search_vector ON products USING gin(search_vector);
CREATE INDEX IF NOT EXISTS idx_products_source_supermarket ON products(source_supermarket_id);

-- Product prices indexes - critical for price comparison performance
CREATE INDEX IF NOT EXISTS idx_product_prices_product ON product_prices(product_id);
CREATE INDEX IF NOT EXISTS idx_product_prices_supermarket ON product_prices(supermarket_id);
CREATE INDEX IF NOT EXISTS idx_product_prices_price ON product_prices(price);
CREATE INDEX IF NOT EXISTS idx_product_prices_available ON product_prices(is_available) WHERE is_available = true;
CREATE INDEX IF NOT EXISTS idx_product_prices_updated ON product_prices(last_updated DESC);
CREATE INDEX IF NOT EXISTS idx_product_prices_composite ON product_prices(product_id, supermarket_id, is_available);
CREATE INDEX IF NOT EXISTS idx_product_prices_sale ON product_prices(is_on_sale) WHERE is_on_sale = true;

-- Price history indexes - for trend analysis
CREATE INDEX IF NOT EXISTS idx_price_history_product_supermarket ON price_history(product_id, supermarket_id);
CREATE INDEX IF NOT EXISTS idx_price_history_recorded_at ON price_history(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_price_history_product_date ON price_history(product_id, recorded_at DESC);

-- Shopping lists indexes
CREATE INDEX IF NOT EXISTS idx_shopping_list_items_list ON shopping_list_items(shopping_list_id);
CREATE INDEX IF NOT EXISTS idx_shopping_list_items_product ON shopping_list_items(product_id);
CREATE INDEX IF NOT EXISTS idx_shopping_lists_user ON shopping_lists(user_id);

-- User favorites indexes
CREATE INDEX IF NOT EXISTS idx_user_favorites_user ON user_favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_user_favorites_product ON user_favorites(product_id);

-- =====================================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================================

-- Current price comparison view - most used query
CREATE OR REPLACE VIEW current_price_comparison AS
SELECT 
    p.id as product_id,
    p.name as product_name,
    p.brand,
    p.normalized_name,
    p.size_text,
    p.package_size,
    p.package_unit,
    s.name as supermarket_name,
    s.slug as supermarket_slug,
    s.checkjebon_key,
    pp.price,
    pp.original_price,
    pp.price_per_unit,
    pp.discount_percentage,
    pp.is_on_sale,
    pp.is_available,
    pp.last_updated,
    c.name as category_name,
    c.slug as category_slug
FROM products p
JOIN product_prices pp ON p.id = pp.product_id
JOIN supermarkets s ON pp.supermarket_id = s.id
LEFT JOIN categories c ON p.category_id = c.id
WHERE pp.is_available = true 
  AND s.is_active = true 
  AND p.is_active = true;

-- Cheapest prices view - for finding best deals
CREATE OR REPLACE VIEW cheapest_prices AS
WITH ranked_prices AS (
    SELECT 
        product_id,
        supermarket_id,
        price,
        price_per_unit,
        is_on_sale,
        ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY price ASC) as price_rank
    FROM product_prices 
    WHERE is_available = true
)
SELECT 
    p.id as product_id,
    p.name as product_name,
    p.brand,
    p.size_text,
    s.name as supermarket_name,
    s.slug as supermarket_slug,
    rp.price as cheapest_price,
    rp.price_per_unit,
    rp.is_on_sale,
    c.name as category_name
FROM ranked_prices rp
JOIN products p ON rp.product_id = p.id
JOIN supermarkets s ON rp.supermarket_id = s.id
LEFT JOIN categories c ON p.category_id = c.id
WHERE rp.price_rank = 1
  AND p.is_active = true;

-- Price trends view - for analytics
CREATE OR REPLACE VIEW price_trends AS
SELECT 
    p.id as product_id,
    p.name as product_name,
    s.name as supermarket_name,
    ph.price,
    ph.price_change,
    ph.price_change_percentage,
    ph.recorded_at,
    LAG(ph.price) OVER (PARTITION BY p.id, s.id ORDER BY ph.recorded_at) as previous_price,
    AVG(ph.price) OVER (PARTITION BY p.id, s.id ORDER BY ph.recorded_at ROWS BETWEEN 30 PRECEDING AND CURRENT ROW) as avg_price_30d
FROM price_history ph
JOIN products p ON ph.product_id = p.id
JOIN supermarkets s ON ph.supermarket_id = s.id
WHERE p.is_active = true;

-- =====================================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to update search vector
CREATE OR REPLACE FUNCTION update_product_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('dutch', 
        COALESCE(NEW.name, '') || ' ' ||
        COALESCE(NEW.brand, '') || ' ' ||
        COALESCE(NEW.description, '') || ' ' ||
        COALESCE(NEW.size_text, '')
    );
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to normalize product names
CREATE OR REPLACE FUNCTION normalize_product_name()
RETURNS TRIGGER AS $$
BEGIN
    NEW.normalized_name := LOWER(TRIM(REGEXP_REPLACE(NEW.name, '[^a-zA-Z0-9\s]', '', 'g')));
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
    -- Get the old price if this is an update
    IF TG_OP = 'UPDATE' AND OLD.price != NEW.price THEN
        old_price := OLD.price;
        price_diff := NEW.price - old_price;
        price_diff_pct := CASE 
            WHEN old_price > 0 THEN (price_diff / old_price) * 100 
            ELSE 0 
        END;
        
        -- Insert into price history
        INSERT INTO price_history (
            product_id, 
            supermarket_id, 
            price, 
            original_price, 
            price_per_unit,
            price_change,
            price_change_percentage,
            change_reason,
            data_source
        ) VALUES (
            NEW.product_id,
            NEW.supermarket_id,
            NEW.price,
            NEW.original_price,
            NEW.price_per_unit,
            price_diff,
            price_diff_pct,
            'price_update',
            NEW.data_source
        );
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to update shopping list totals
CREATE OR REPLACE FUNCTION update_shopping_list_totals()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the shopping list totals
    UPDATE shopping_lists 
    SET 
        total_items = (
            SELECT COUNT(*) 
            FROM shopping_list_items 
            WHERE shopping_list_id = COALESCE(NEW.shopping_list_id, OLD.shopping_list_id)
        ),
        total_estimated_price = (
            SELECT COALESCE(SUM(estimated_price * quantity), 0)
            FROM shopping_list_items 
            WHERE shopping_list_id = COALESCE(NEW.shopping_list_id, OLD.shopping_list_id)
        ),
        updated_at = NOW()
    WHERE id = COALESCE(NEW.shopping_list_id, OLD.shopping_list_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';

-- =====================================================================
-- TRIGGERS
-- =====================================================================

-- Updated_at triggers
DROP TRIGGER IF EXISTS update_supermarkets_updated_at ON supermarkets;
CREATE TRIGGER update_supermarkets_updated_at 
    BEFORE UPDATE ON supermarkets 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at 
    BEFORE UPDATE ON products 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_shopping_lists_updated_at ON shopping_lists;
CREATE TRIGGER update_shopping_lists_updated_at 
    BEFORE UPDATE ON shopping_lists 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_shopping_list_items_updated_at ON shopping_list_items;
CREATE TRIGGER update_shopping_list_items_updated_at 
    BEFORE UPDATE ON shopping_list_items 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Search vector triggers
DROP TRIGGER IF EXISTS update_products_search_vector ON products;
CREATE TRIGGER update_products_search_vector
    BEFORE INSERT OR UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_product_search_vector();

-- Name normalization trigger
DROP TRIGGER IF EXISTS normalize_products_name ON products;
CREATE TRIGGER normalize_products_name
    BEFORE INSERT OR UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION normalize_product_name();

-- Price change tracking trigger
DROP TRIGGER IF EXISTS track_product_price_changes ON product_prices;
CREATE TRIGGER track_product_price_changes
    AFTER INSERT OR UPDATE ON product_prices
    FOR EACH ROW EXECUTE FUNCTION track_price_changes();

-- Shopping list totals triggers
DROP TRIGGER IF EXISTS update_list_totals_on_item_change ON shopping_list_items;
CREATE TRIGGER update_list_totals_on_item_change
    AFTER INSERT OR UPDATE OR DELETE ON shopping_list_items
    FOR EACH ROW EXECUTE FUNCTION update_shopping_list_totals();

-- =====================================================================
-- ROW LEVEL SECURITY (RLS)
-- =====================================================================

-- Enable RLS on user-specific tables
ALTER TABLE shopping_lists ENABLE ROW LEVEL SECURITY;
ALTER TABLE shopping_list_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_alerts ENABLE ROW LEVEL SECURITY;

-- Policies will be added when user authentication is implemented
-- Example policies (commented out for now):
/*
CREATE POLICY "Users can view their own shopping lists" ON shopping_lists
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own shopping lists" ON shopping_lists
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own shopping lists" ON shopping_lists
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own shopping lists" ON shopping_lists
    FOR DELETE USING (auth.uid() = user_id);
*/

-- =====================================================================
-- INITIAL DATA SEEDING
-- =====================================================================

-- Insert Dutch supermarkets (matching CheckjeBon data)
INSERT INTO supermarkets (name, slug, checkjebon_key, color_primary, is_active, has_online_data) VALUES 
('Albert Heijn', 'albert-heijn', 'ah', '#0051A5', true, true),
('Jumbo', 'jumbo', 'jumbo', '#FFD800', true, true),
('Plus', 'plus', 'plus', '#E30613', true, true),
('DekaMarkt', 'dekamarkt', 'dekamarkt', '#E30613', true, true),
('Coop', 'coop', 'coop', '#E30613', true, true),
('Dirk', 'dirk', 'dirk', '#009CDA', true, true),
('Hoogvliet', 'hoogvliet', 'hoogvliet', '#E30613', true, true),
('Aldi', 'aldi', 'aldi', '#009CDA', true, true),
('Vomar', 'vomar', 'vomar', '#009CDA', true, true),
('Picnic', 'picnic', 'picnic', '#00A88F', true, false),
('Spar', 'spar', 'spar', '#00843D', true, false)
ON CONFLICT (slug) DO NOTHING;

-- Insert main Dutch product categories
INSERT INTO categories (id, name, slug, dutch_keywords, icon_name, display_order) VALUES
('33333333-3333-3333-3333-333333333333', 'Alle producten', 'alle-producten', ARRAY['alle'], 'shopping_cart', 0),
(uuid_generate_v4(), 'Zuivel & eieren', 'zuivel-eieren', ARRAY['melk', 'yoghurt', 'kaas', 'boter', 'ei', 'eieren', 'kwark', 'room'], 'egg', 1),
(uuid_generate_v4(), 'Brood & gebak', 'brood-gebak', ARRAY['brood', 'stokbrood', 'croissant', 'beschuit', 'cake', 'koek'], 'bakery_dining', 2),
(uuid_generate_v4(), 'Groente & fruit', 'groente-fruit', ARRAY['appel', 'banaan', 'tomaat', 'ui', 'wortel', 'sla', 'komkommer', 'paprika', 'fruit', 'groente'], 'eco', 3),
(uuid_generate_v4(), 'Vlees, vis & vegetarisch', 'vlees-vis-vegetarisch', ARRAY['vlees', 'kip', 'vis', 'gehakt', 'worst', 'ham', 'vegetarisch', 'vegan'], 'set_meal', 4),
(uuid_generate_v4(), 'Dranken', 'dranken', ARRAY['cola', 'sap', 'water', 'bier', 'koffie', 'thee', 'wijn', 'frisdrank'], 'local_drink', 5),
(uuid_generate_v4(), 'Diepvries', 'diepvries', ARRAY['diepvries', 'frozen', 'ijs', 'ijsje'], 'ac_unit', 6),
(uuid_generate_v4(), 'Houdbaar', 'houdbaar', ARRAY['conserven', 'pasta', 'rijst', 'meel', 'suiker'], 'inventory_2', 7),
(uuid_generate_v4(), 'Snacks & snoep', 'snacks-snoep', ARRAY['chips', 'koekjes', 'chocolade', 'snoep', 'noten'], 'cookie', 8),
(uuid_generate_v4(), 'Verzorging', 'verzorging', ARRAY['shampoo', 'tandpasta', 'zeep', 'deodorant', 'parfum', 'creme'], 'local_pharmacy', 9),
(uuid_generate_v4(), 'Huishouden', 'huishouden', ARRAY['wasmiddel', 'afwasmiddel', 'toiletpapier', 'keukenrol', 'schoonmaak'], 'cleaning_services', 10),
(uuid_generate_v4(), 'Baby & kind', 'baby-kind', ARRAY['baby', 'luier', 'flesvoeding', 'kindje'], 'child_care', 11),
(uuid_generate_v4(), 'Dieren', 'dieren', ARRAY['hond', 'kat', 'voer', 'dier'], 'pets', 12)
ON CONFLICT (slug) DO NOTHING;

-- =====================================================================
-- OPTIMIZATION SETTINGS
-- =====================================================================

-- Optimize for Dutch text search
CREATE TEXT SEARCH CONFIGURATION dutch_config (COPY = dutch);

-- Update table statistics for query planning
ANALYZE supermarkets;
ANALYZE categories;
ANALYZE products;
ANALYZE product_prices;

-- =====================================================================
-- SUCCESS MESSAGE
-- =====================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ CheckjeBon Optimized Database Schema Created Successfully!';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Database Features:';
    RAISE NOTICE '   • 11 Dutch supermarkets ready for 95,289+ products';
    RAISE NOTICE '   • Optimized for fast price comparisons';
    RAISE NOTICE '   • Full-text search in Dutch';
    RAISE NOTICE '   • Automatic price change tracking';
    RAISE NOTICE '   • Shopping lists and user preferences';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Next Steps:';
    RAISE NOTICE '   1. Use the Flutter app admin panel to import CheckjeBon data';
    RAISE NOTICE '   2. Test price comparison queries using the views';
    RAISE NOTICE '   3. Monitor performance with the optimized indexes';
    RAISE NOTICE '';
    RAISE NOTICE '💡 Key Views Created:';
    RAISE NOTICE '   • current_price_comparison - Main price comparison';
    RAISE NOTICE '   • cheapest_prices - Find best deals';
    RAISE NOTICE '   • price_trends - Price analytics';
END $$;