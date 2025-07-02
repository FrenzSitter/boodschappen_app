-- Seed data for Dutch supermarkets
-- Insert major Dutch supermarket chains

INSERT INTO supermarkets (name, slug, logo_url, website_url, color_primary, color_secondary, is_active) VALUES
('Albert Heijn', 'albert-heijn', NULL, 'https://www.ah.nl', '#0051A5', '#FFFFFF', true),
('Jumbo', 'jumbo', NULL, 'https://www.jumbo.com', '#FFD800', '#000000', true),
('Lidl', 'lidl', NULL, 'https://www.lidl.nl', '#0050AA', '#FFD800', true),
('Aldi', 'aldi', NULL, 'https://www.aldi.nl', '#009CDA', '#FFFFFF', true),
('Plus', 'plus', NULL, 'https://www.plus.nl', '#E30613', '#FFFFFF', true),
('COOP', 'coop', NULL, 'https://www.coop.nl', '#E30613', '#FFFFFF', true),
('Spar', 'spar', NULL, 'https://www.spar.nl', '#009639', '#FFFFFF', true),
('Vomar', 'vomar', NULL, 'https://www.vomar.nl', '#E30613', '#FFFFFF', true),
('Hoogvliet', 'hoogvliet', NULL, 'https://www.hoogvliet.com', '#E30613', '#FFFFFF', true),
('Jan Linders', 'jan-linders', NULL, 'https://www.janlinders.nl', '#0066CC', '#FFFFFF', true);

-- Insert product categories
INSERT INTO categories (name, slug, parent_id, icon_name, display_order) VALUES
('Verse producten', 'fresh-products', NULL, 'local_florist', 1),
('Vlees, vis & vegetarisch', 'meat-fish-vegetarian', NULL, 'set_meal', 2),
('Zuivel & eieren', 'dairy-eggs', NULL, 'egg', 3),
('Brood & gebak', 'bread-bakery', NULL, 'bakery_dining', 4),
('Groente & fruit', 'vegetables-fruit', NULL, 'eco', 5),
('Diepvries', 'frozen', NULL, 'ac_unit', 6),
('Houdbaar', 'shelf-stable', NULL, 'inventory_2', 7),
('Dranken', 'drinks', NULL, 'local_drink', 8),
('Baby & kind', 'baby-child', NULL, 'child_care', 9),
('Verzorging & gezondheid', 'health-care', NULL, 'health_and_safety', 10),
('Huishouden & schoonmaak', 'household-cleaning', NULL, 'cleaning_services', 11),
('Huisdieren', 'pets', NULL, 'pets', 12);

-- Insert subcategories for Groente & fruit
INSERT INTO categories (name, slug, parent_id, icon_name, display_order) VALUES
('Fruit', 'fruit', (SELECT id FROM categories WHERE slug = 'vegetables-fruit'), 'apple', 1),
('Groenten', 'vegetables', (SELECT id FROM categories WHERE slug = 'vegetables-fruit'), 'grass', 2),
('Aardappelen', 'potatoes', (SELECT id FROM categories WHERE slug = 'vegetables-fruit'), 'eco', 3),
('Sla & kruiden', 'salad-herbs', (SELECT id FROM categories WHERE slug = 'vegetables-fruit'), 'grass', 4);

-- Insert subcategories for Zuivel & eieren
INSERT INTO categories (name, slug, parent_id, icon_name, display_order) VALUES
('Melk', 'milk', (SELECT id FROM categories WHERE slug = 'dairy-eggs'), 'local_drink', 1),
('Yoghurt & kwark', 'yogurt-quark', (SELECT id FROM categories WHERE slug = 'dairy-eggs'), 'emoji_food_beverage', 2),
('Kaas', 'cheese', (SELECT id FROM categories WHERE slug = 'dairy-eggs'), 'emoji_food_beverage', 3),
('Eieren', 'eggs', (SELECT id FROM categories WHERE slug = 'dairy-eggs'), 'egg', 4),
('Boter & margarine', 'butter-margarine', (SELECT id FROM categories WHERE slug = 'dairy-eggs'), 'emoji_food_beverage', 5);

-- Insert subcategories for Dranken
INSERT INTO categories (name, slug, parent_id, icon_name, display_order) VALUES
('Frisdrank', 'soft-drinks', (SELECT id FROM categories WHERE slug = 'drinks'), 'local_drink', 1),
('Water', 'water', (SELECT id FROM categories WHERE slug = 'drinks'), 'water_drop', 2),
('Sap', 'juice', (SELECT id FROM categories WHERE slug = 'drinks'), 'local_drink', 3),
('Koffie & thee', 'coffee-tea', (SELECT id FROM categories WHERE slug = 'drinks'), 'local_cafe', 4),
('Alcoholische dranken', 'alcoholic-drinks', (SELECT id FROM categories WHERE slug = 'drinks'), 'wine_bar', 5);

-- Sample products (you can expand this)
INSERT INTO products (name, brand, category_id, barcode, unit_type, package_size, package_unit, description, is_organic, is_bio) VALUES
('Melk halfvol', 'AH Basic', (SELECT id FROM categories WHERE slug = 'milk'), '8718906115892', 'liter', 1.0, 'l', 'Halfvolle melk 1 liter', false, false),
('Bananen', 'Chiquita', (SELECT id FROM categories WHERE slug = 'fruit'), NULL, 'kg', 1.0, 'kg', 'Verse bananen per kilo', false, false),
('Eieren vrije uitloop', 'AH', (SELECT id FROM categories WHERE slug = 'eggs'), '8718906142465', 'piece', 12.0, 'stuks', '12 eieren van vrije uitloop kippen', false, false),
('Coca Cola', 'Coca-Cola', (SELECT id FROM categories WHERE slug = 'soft-drinks'), '5449000000996', 'liter', 1.5, 'l', 'Coca Cola 1.5 liter fles', false, false),
('Brood wit', 'AH Basic', (SELECT id FROM categories WHERE slug = 'bread-bakery'), '8718906176447', 'piece', 800.0, 'g', 'Wit brood heel 800 gram', false, false);

-- Sample price data
INSERT INTO product_prices (product_id, supermarket_id, price, price_per_unit, is_available, last_updated) VALUES
-- Melk halfvol prices
((SELECT id FROM products WHERE barcode = '8718906115892'), (SELECT id FROM supermarkets WHERE slug = 'albert-heijn'), 1.19, 1.19, true, NOW()),
((SELECT id FROM products WHERE barcode = '8718906115892'), (SELECT id FROM supermarkets WHERE slug = 'jumbo'), 1.15, 1.15, true, NOW()),
((SELECT id FROM products WHERE barcode = '8718906115892'), (SELECT id FROM supermarkets WHERE slug = 'lidl'), 0.89, 0.89, true, NOW()),

-- Bananen prices
((SELECT id FROM products WHERE name = 'Bananen'), (SELECT id FROM supermarkets WHERE slug = 'albert-heijn'), 1.99, 1.99, true, NOW()),
((SELECT id FROM products WHERE name = 'Bananen'), (SELECT id FROM supermarkets WHERE slug = 'jumbo'), 1.89, 1.89, true, NOW()),
((SELECT id FROM products WHERE name = 'Bananen'), (SELECT id FROM supermarkets WHERE slug = 'lidl'), 1.49, 1.49, true, NOW()),

-- Eieren prices
((SELECT id FROM products WHERE barcode = '8718906142465'), (SELECT id FROM supermarkets WHERE slug = 'albert-heijn'), 2.89, 0.24, true, NOW()),
((SELECT id FROM products WHERE barcode = '8718906142465'), (SELECT id FROM supermarkets WHERE slug = 'jumbo'), 2.79, 0.23, true, NOW()),

-- Coca Cola prices
((SELECT id FROM products WHERE barcode = '5449000000996'), (SELECT id FROM supermarkets WHERE slug = 'albert-heijn'), 2.19, 1.46, true, NOW()),
((SELECT id FROM products WHERE barcode = '5449000000996'), (SELECT id FROM supermarkets WHERE slug = 'jumbo'), 1.99, 1.33, true, NOW()),
((SELECT id FROM products WHERE barcode = '5449000000996'), (SELECT id FROM supermarkets WHERE slug = 'lidl'), 1.79, 1.19, true, NOW()),

-- Brood wit prices
((SELECT id FROM products WHERE barcode = '8718906176447'), (SELECT id FROM supermarkets WHERE slug = 'albert-heijn'), 1.09, 1.36, true, NOW()),
((SELECT id FROM products WHERE barcode = '8718906176447'), (SELECT id FROM supermarkets WHERE slug = 'jumbo'), 0.99, 1.24, true, NOW());