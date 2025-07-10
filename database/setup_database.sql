-- Complete database setup for boodschappen_app
-- Run this script in your Supabase SQL editor to set up all tables

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Supermarkets table
CREATE TABLE IF NOT EXISTS supermarkets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(50) NOT NULL UNIQUE,
    logo_url TEXT,
    website_url TEXT,
    color_primary VARCHAR(7), -- Hex color code
    color_secondary VARCHAR(7), -- Hex color code
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Product categories table
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) NOT NULL UNIQUE,
    parent_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    icon_name VARCHAR(50),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Products base table
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    brand VARCHAR(100),
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    barcode VARCHAR(20),
    image_url TEXT,
    unit_type VARCHAR(20) DEFAULT 'piece', -- piece, kg, liter, gram, etc.
    package_size DECIMAL(10,3), -- Size of the package
    package_unit VARCHAR(10), -- Unit of the package (kg, l, pieces, etc.)
    description TEXT,
    ingredients TEXT,
    nutritional_info JSONB,
    allergens TEXT[],
    is_organic BOOLEAN DEFAULT false,
    is_bio BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Product prices table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS product_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    supermarket_id UUID NOT NULL REFERENCES supermarkets(id) ON DELETE CASCADE,
    price DECIMAL(10,2) NOT NULL,
    original_price DECIMAL(10,2), -- For discounts
    discount_percentage DECIMAL(5,2),
    price_per_unit DECIMAL(10,4), -- Price per kg/liter/piece for comparison
    currency VARCHAR(3) DEFAULT 'EUR',
    is_available BOOLEAN DEFAULT true,
    is_on_sale BOOLEAN DEFAULT false,
    sale_start_date DATE,
    sale_end_date DATE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User shopping lists
CREATE TABLE IF NOT EXISTS shopping_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_favorite BOOLEAN DEFAULT false,
    total_estimated_price DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Shopping list items
CREATE TABLE IF NOT EXISTS shopping_list_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shopping_list_id UUID NOT NULL REFERENCES shopping_lists(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    custom_product_name VARCHAR(200), -- For items not in product database
    quantity INTEGER DEFAULT 1,
    is_completed BOOLEAN DEFAULT false,
    notes TEXT,
    preferred_supermarket_id UUID REFERENCES supermarkets(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Price history for tracking changes
CREATE TABLE IF NOT EXISTS price_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    supermarket_id UUID NOT NULL REFERENCES supermarkets(id) ON DELETE CASCADE,
    price DECIMAL(10,2) NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User favorites
CREATE TABLE IF NOT EXISTS user_favorites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_products_name ON products USING gin(to_tsvector('dutch', name));
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_product_prices_product ON product_prices(product_id);
CREATE INDEX IF NOT EXISTS idx_product_prices_supermarket ON product_prices(supermarket_id);
CREATE INDEX IF NOT EXISTS idx_product_prices_updated ON product_prices(last_updated);
CREATE INDEX IF NOT EXISTS idx_price_history_product_supermarket ON price_history(product_id, supermarket_id);
CREATE INDEX IF NOT EXISTS idx_shopping_list_items_list ON shopping_list_items(shopping_list_id);
CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);

-- Views for common queries
CREATE OR REPLACE VIEW product_price_comparison AS
SELECT 
    p.id as product_id,
    p.name as product_name,
    p.brand,
    p.barcode,
    s.name as supermarket_name,
    s.slug as supermarket_slug,
    pp.price,
    pp.original_price,
    pp.discount_percentage,
    pp.price_per_unit,
    pp.is_on_sale,
    pp.last_updated,
    c.name as category_name
FROM products p
JOIN product_prices pp ON p.id = pp.product_id
JOIN supermarkets s ON pp.supermarket_id = s.id
LEFT JOIN categories c ON p.category_id = c.id
WHERE pp.is_available = true AND s.is_active = true;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at (drop and recreate to avoid conflicts)
DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at 
    BEFORE UPDATE ON products 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_shopping_lists_updated_at ON shopping_lists;
CREATE TRIGGER update_shopping_lists_updated_at 
    BEFORE UPDATE ON shopping_lists 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial data

-- Insert supermarkets
INSERT INTO supermarkets (name, slug, logo_url, website_url, color_primary, color_secondary, is_active) VALUES 
('Albert Heijn', 'albert-heijn', 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Albert_Heijn_Logo.svg/1200px-Albert_Heijn_Logo.svg.png', 'https://www.ah.nl', '#0051A5', '#FFFFFF', true),
('Jumbo', 'jumbo', 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Jumbo_Logo.svg/1200px-Jumbo_Logo.svg.png', 'https://www.jumbo.com', '#FFD800', '#000000', true),
('Lidl', 'lidl', 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Lidl-Logo.svg/1200px-Lidl-Logo.svg.png', 'https://www.lidl.nl', '#0050AA', '#FFED00', true),
('Aldi', 'aldi', 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Aldi_Nord_Logo.svg/1200px-Aldi_Nord_Logo.svg.png', 'https://www.aldi.nl', '#009CDA', '#FFFFFF', true),
('Plus', 'plus', 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c6/Plus_logo.svg/1200px-Plus_logo.svg.png', 'https://www.plus.nl', '#E30613', '#FFFFFF', true),
('COOP', 'coop', 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Coop_logo.svg/1200px-Coop_logo.svg.png', 'https://www.coop.nl', '#E30613', '#FFFFFF', true),
('Spar', 'spar', 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Spar-logo.svg/1200px-Spar-logo.svg.png', 'https://www.spar.nl', '#00843D', '#FFFFFF', true),
('Nettorama', 'nettorama', '', 'https://www.nettorama.nl', '#E30613', '#FFFFFF', true),
('Dirk', 'dirk', 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Dirk_supermarket_logo.svg/1200px-Dirk_supermarket_logo.svg.png', 'https://www.dirk.nl', '#009CDA', '#FFFFFF', true),
('Hoogvliet', 'hoogvliet', 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/Hoogvliet_Logo.svg/1200px-Hoogvliet_Logo.svg.png', 'https://www.hoogvliet.com', '#E30613', '#FFFFFF', true),
('Vomar', 'vomar', 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Vomar_logo.svg/1200px-Vomar_logo.svg.png', 'https://www.vomar.nl', '#009CDA', '#FFFFFF', true),
('DekaMarkt', 'dekamarkt', 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/DekaMarkt_Logo.svg/1200px-DekaMarkt_Logo.svg.png', 'https://www.dekamarkt.nl', '#E30613', '#FFFFFF', true)
ON CONFLICT (slug) DO NOTHING;

-- Insert main categories
INSERT INTO categories (id, name, slug, parent_id, icon_name, display_order) VALUES
('33333333-3333-3333-3333-333333333333', 'Alle producten', 'alle-producten', null, 'shopping_cart', 0),
(uuid_generate_v4(), 'Verse producten', 'verse-producten', null, 'local_florist', 1),
(uuid_generate_v4(), 'Vlees, vis & vegetarisch', 'vlees-vis-vegetarisch', null, 'set_meal', 2),
(uuid_generate_v4(), 'Zuivel & eieren', 'zuivel-eieren', null, 'egg', 3),
(uuid_generate_v4(), 'Brood & gebak', 'brood-gebak', null, 'bakery_dining', 4),
(uuid_generate_v4(), 'Groente & fruit', 'groente-fruit', null, 'eco', 5),
(uuid_generate_v4(), 'Diepvries', 'diepvries', null, 'ac_unit', 6),
(uuid_generate_v4(), 'Houdbaar', 'houdbaar', null, 'inventory_2', 7),
(uuid_generate_v4(), 'Dranken', 'dranken', null, 'local_drink', 8),
(uuid_generate_v4(), 'Snacks & snoep', 'snacks-snoep', null, 'cookie', 9),
(uuid_generate_v4(), 'Verzorging', 'verzorging', null, 'local_pharmacy', 10),
(uuid_generate_v4(), 'Huishouden', 'huishouden', null, 'cleaning_services', 11),
(uuid_generate_v4(), 'Baby & kind', 'baby-kind', null, 'child_care', 12),
(uuid_generate_v4(), 'Dieren', 'dieren', null, 'pets', 13),
(uuid_generate_v4(), 'Koken & tafelen', 'koken-tafelen', null, 'restaurant', 14),
(uuid_generate_v4(), 'Biologisch', 'biologisch', null, 'nature', 15)
ON CONFLICT (slug) DO NOTHING;

-- Success message
SELECT 'Database setup completed successfully!' as result;