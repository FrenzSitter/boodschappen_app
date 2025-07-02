-- Drop existing tables if they exist
DROP TABLE IF EXISTS public.prices CASCADE;
DROP TABLE IF EXISTS public.products CASCADE;
DROP TABLE IF EXISTS public.supermarkets CASCADE;
DROP TABLE IF EXISTS public.categories CASCADE;

-- Create categories table
CREATE TABLE public.categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    parent_id UUID REFERENCES public.categories(id),
    icon_name VARCHAR(100),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create supermarkets table
CREATE TABLE public.supermarkets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    logo_url TEXT,
    website_url TEXT,
    color_primary VARCHAR(7),
    color_secondary VARCHAR(7),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create products table
CREATE TABLE public.products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(500) NOT NULL,
    brand VARCHAR(255),
    category_id UUID REFERENCES public.categories(id),
    barcode VARCHAR(50),
    image_url TEXT,
    unit_type VARCHAR(50) DEFAULT 'piece',
    package_size DECIMAL(10,3),
    package_unit VARCHAR(20),
    description TEXT,
    is_organic BOOLEAN DEFAULT false,
    is_bio BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create prices table
CREATE TABLE public.prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES public.products(id) ON DELETE CASCADE,
    supermarket_id UUID REFERENCES public.supermarkets(id) ON DELETE CASCADE,
    price DECIMAL(10,2) NOT NULL,
    original_price DECIMAL(10,2),
    price_per_unit DECIMAL(10,4),
    currency VARCHAR(3) DEFAULT 'EUR',
    is_available BOOLEAN DEFAULT true,
    is_on_sale BOOLEAN DEFAULT false,
    sale_start_date TIMESTAMP WITH TIME ZONE,
    sale_end_date TIMESTAMP WITH TIME ZONE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_products_name ON public.products USING gin(to_tsvector('dutch', name));
CREATE INDEX idx_products_brand ON public.products(brand);
CREATE INDEX idx_products_category ON public.products(category_id);
CREATE INDEX idx_products_barcode ON public.products(barcode);
CREATE INDEX idx_prices_product ON public.prices(product_id);
CREATE INDEX idx_prices_supermarket ON public.prices(supermarket_id);
CREATE INDEX idx_prices_price ON public.prices(price);
CREATE INDEX idx_prices_available ON public.prices(is_available);
CREATE INDEX idx_prices_sale ON public.prices(is_on_sale);

-- Enable Row Level Security
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.supermarkets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.prices ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access
CREATE POLICY "Allow public read access on categories" ON public.categories FOR SELECT USING (true);
CREATE POLICY "Allow public read access on supermarkets" ON public.supermarkets FOR SELECT USING (true);
CREATE POLICY "Allow public read access on products" ON public.products FOR SELECT USING (true);
CREATE POLICY "Allow public read access on prices" ON public.prices FOR SELECT USING (true);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON public.categories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_supermarkets_updated_at BEFORE UPDATE ON public.supermarkets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON public.products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_prices_updated_at BEFORE UPDATE ON public.prices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();