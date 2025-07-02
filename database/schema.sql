-- Supabase Database Schema for Dutch Supermarkets
-- This file contains the complete database schema for the Boodschappen App

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Supermarkets table
CREATE TABLE supermarkets (
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
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) NOT NULL UNIQUE,
    parent_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    icon_name VARCHAR(50),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Products base table
CREATE TABLE products (
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
CREATE TABLE product_prices (
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
CREATE TABLE shopping_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_favorite BOOLEAN DEFAULT false,
    total_estimated_price DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Shopping list items
CREATE TABLE shopping_list_items (
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
CREATE TABLE price_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    supermarket_id UUID NOT NULL REFERENCES supermarkets(id) ON DELETE CASCADE,
    price DECIMAL(10,2) NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User favorites
CREATE TABLE user_favorites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_products_barcode ON products(barcode);
CREATE INDEX idx_products_name ON products USING gin(to_tsvector('dutch', name));
CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_product_prices_product ON product_prices(product_id);
CREATE INDEX idx_product_prices_supermarket ON product_prices(supermarket_id);
CREATE INDEX idx_product_prices_updated ON product_prices(last_updated);
CREATE INDEX idx_price_history_product_supermarket ON price_history(product_id, supermarket_id);
CREATE INDEX idx_shopping_list_items_list ON shopping_list_items(shopping_list_id);
CREATE INDEX idx_categories_parent ON categories(parent_id);

-- Views for common queries
CREATE VIEW product_price_comparison AS
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

-- Triggers for updated_at
CREATE TRIGGER update_products_updated_at 
    BEFORE UPDATE ON products 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shopping_lists_updated_at 
    BEFORE UPDATE ON shopping_lists 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) - Enable for user data
ALTER TABLE shopping_lists ENABLE ROW LEVEL SECURITY;
ALTER TABLE shopping_list_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_favorites ENABLE ROW LEVEL SECURITY;

-- Policies (for when user authentication is added)
-- CREATE POLICY "Users can view their own shopping lists" ON shopping_lists
--     FOR SELECT USING (auth.uid() = user_id);
-- 
-- CREATE POLICY "Users can create their own shopping lists" ON shopping_lists
--     FOR INSERT WITH CHECK (auth.uid() = user_id);
--
-- CREATE POLICY "Users can update their own shopping lists" ON shopping_lists
--     FOR UPDATE USING (auth.uid() = user_id);
--
-- CREATE POLICY "Users can delete their own shopping lists" ON shopping_lists
--     FOR DELETE USING (auth.uid() = user_id);