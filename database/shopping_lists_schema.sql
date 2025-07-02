-- Create shopping_lists table
CREATE TABLE public.shopping_lists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_shared BOOLEAN DEFAULT false,
    shared_code VARCHAR(10) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create shopping_list_items table
CREATE TABLE public.shopping_list_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    list_id UUID REFERENCES public.shopping_lists(id) ON DELETE CASCADE,
    product_id UUID REFERENCES public.products(id) ON DELETE SET NULL,
    name VARCHAR(500) NOT NULL,
    quantity INTEGER DEFAULT 1,
    notes TEXT,
    is_checked BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_shopping_lists_created_at ON public.shopping_lists(created_at DESC);
CREATE INDEX idx_shopping_lists_shared_code ON public.shopping_lists(shared_code) WHERE shared_code IS NOT NULL;
CREATE INDEX idx_shopping_list_items_list_id ON public.shopping_list_items(list_id);
CREATE INDEX idx_shopping_list_items_product_id ON public.shopping_list_items(product_id);
CREATE INDEX idx_shopping_list_items_checked ON public.shopping_list_items(is_checked);

-- Enable Row Level Security
ALTER TABLE public.shopping_lists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.shopping_list_items ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (for demo purposes)
CREATE POLICY "Allow public read access on shopping_lists" ON public.shopping_lists FOR SELECT USING (true);
CREATE POLICY "Allow public insert on shopping_lists" ON public.shopping_lists FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update on shopping_lists" ON public.shopping_lists FOR UPDATE USING (true);
CREATE POLICY "Allow public delete on shopping_lists" ON public.shopping_lists FOR DELETE USING (true);

CREATE POLICY "Allow public read access on shopping_list_items" ON public.shopping_list_items FOR SELECT USING (true);
CREATE POLICY "Allow public insert on shopping_list_items" ON public.shopping_list_items FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update on shopping_list_items" ON public.shopping_list_items FOR UPDATE USING (true);
CREATE POLICY "Allow public delete on shopping_list_items" ON public.shopping_list_items FOR DELETE USING (true);

-- Create triggers for updated_at
CREATE TRIGGER update_shopping_lists_updated_at 
    BEFORE UPDATE ON public.shopping_lists 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shopping_list_items_updated_at 
    BEFORE UPDATE ON public.shopping_list_items 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to generate shared codes
CREATE OR REPLACE FUNCTION generate_shared_code() RETURNS TEXT AS $$
DECLARE
    chars TEXT := 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    result TEXT := '';
    i INTEGER;
BEGIN
    FOR i IN 1..6 LOOP
        result := result || substr(chars, (random() * length(chars))::integer + 1, 1);
    END LOOP;
    RETURN result;
END;
$$ LANGUAGE plpgsql;