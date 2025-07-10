-- Seed data for Dutch supermarkets
-- This script populates the database with real Dutch supermarket chains

-- First, insert supermarkets
INSERT INTO supermarkets (id, name, slug, logo_url, website_url, color_primary, color_secondary, is_active) VALUES 
(uuid_generate_v4(), 'Albert Heijn', 'albert-heijn', 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Albert_Heijn_Logo.svg/1200px-Albert_Heijn_Logo.svg.png', 'https://www.ah.nl', '#0051A5', '#FFFFFF', true),
(uuid_generate_v4(), 'Jumbo', 'jumbo', 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Jumbo_Logo.svg/1200px-Jumbo_Logo.svg.png', 'https://www.jumbo.com', '#FFD800', '#000000', true),
(uuid_generate_v4(), 'Lidl', 'lidl', 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Lidl-Logo.svg/1200px-Lidl-Logo.svg.png', 'https://www.lidl.nl', '#0050AA', '#FFED00', true),
(uuid_generate_v4(), 'Aldi', 'aldi', 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Aldi_Nord_Logo.svg/1200px-Aldi_Nord_Logo.svg.png', 'https://www.aldi.nl', '#009CDA', '#FFFFFF', true),
(uuid_generate_v4(), 'Plus', 'plus', 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c6/Plus_logo.svg/1200px-Plus_logo.svg.png', 'https://www.plus.nl', '#E30613', '#FFFFFF', true),
(uuid_generate_v4(), 'COOP', 'coop', 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Coop_logo.svg/1200px-Coop_logo.svg.png', 'https://www.coop.nl', '#E30613', '#FFFFFF', true),
(uuid_generate_v4(), 'Spar', 'spar', 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Spar-logo.svg/1200px-Spar-logo.svg.png', 'https://www.spar.nl', '#00843D', '#FFFFFF', true),
(uuid_generate_v4(), 'Nettorama', 'nettorama', '', 'https://www.nettorama.nl', '#E30613', '#FFFFFF', true),
(uuid_generate_v4(), 'Dirk', 'dirk', 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Dirk_supermarket_logo.svg/1200px-Dirk_supermarket_logo.svg.png', 'https://www.dirk.nl', '#009CDA', '#FFFFFF', true),
(uuid_generate_v4(), 'Hoogvliet', 'hoogvliet', 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/Hoogvliet_Logo.svg/1200px-Hoogvliet_Logo.svg.png', 'https://www.hoogvliet.com', '#E30613', '#FFFFFF', true),
(uuid_generate_v4(), 'Vomar', 'vomar', 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Vomar_logo.svg/1200px-Vomar_logo.svg.png', 'https://www.vomar.nl', '#009CDA', '#FFFFFF', true),
(uuid_generate_v4(), 'DekaMarkt', 'dekamarkt', 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/DekaMarkt_Logo.svg/1200px-DekaMarkt_Logo.svg.png', 'https://www.dekamarkt.nl', '#E30613', '#FFFFFF', true);

-- Insert main categories
INSERT INTO categories (id, name, slug, parent_id, icon_name, display_order) VALUES
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
(uuid_generate_v4(), 'Biologisch', 'biologisch', null, 'nature', 15);

-- Insert some subcategories for better organization
INSERT INTO categories (id, name, slug, parent_id, icon_name, display_order) VALUES
-- Groente & fruit subcategories
(uuid_generate_v4(), 'Groenten', 'groenten', (SELECT id FROM categories WHERE slug = 'groente-fruit'), 'eco', 1),
(uuid_generate_v4(), 'Fruit', 'fruit', (SELECT id FROM categories WHERE slug = 'groente-fruit'), 'apple', 2),
(uuid_generate_v4(), 'Kruiden', 'kruiden', (SELECT id FROM categories WHERE slug = 'groente-fruit'), 'grass', 3),

-- Zuivel & eieren subcategories
(uuid_generate_v4(), 'Melk', 'melk', (SELECT id FROM categories WHERE slug = 'zuivel-eieren'), 'local_drink', 1),
(uuid_generate_v4(), 'Yoghurt', 'yoghurt', (SELECT id FROM categories WHERE slug = 'zuivel-eieren'), 'local_drink', 2),
(uuid_generate_v4(), 'Kaas', 'kaas', (SELECT id FROM categories WHERE slug = 'zuivel-eieren'), 'local_dining', 3),
(uuid_generate_v4(), 'Eieren', 'eieren', (SELECT id FROM categories WHERE slug = 'zuivel-eieren'), 'egg', 4),

-- Dranken subcategories
(uuid_generate_v4(), 'Frisdrank', 'frisdrank', (SELECT id FROM categories WHERE slug = 'dranken'), 'local_drink', 1),
(uuid_generate_v4(), 'Sappen', 'sappen', (SELECT id FROM categories WHERE slug = 'dranken'), 'local_drink', 2),
(uuid_generate_v4(), 'Koffie & thee', 'koffie-thee', (SELECT id FROM categories WHERE slug = 'dranken'), 'local_cafe', 3),
(uuid_generate_v4(), 'Alcoholische dranken', 'alcoholische-dranken', (SELECT id FROM categories WHERE slug = 'dranken'), 'wine_bar', 4),

-- Brood & gebak subcategories
(uuid_generate_v4(), 'Brood', 'brood', (SELECT id FROM categories WHERE slug = 'brood-gebak'), 'bakery_dining', 1),
(uuid_generate_v4(), 'Gebak', 'gebak', (SELECT id FROM categories WHERE slug = 'brood-gebak'), 'cake', 2),
(uuid_generate_v4(), 'Koekjes', 'koekjes', (SELECT id FROM categories WHERE slug = 'brood-gebak'), 'cookie', 3);

-- Let's also create a default "Alle producten" category for general searches
INSERT INTO categories (id, name, slug, parent_id, icon_name, display_order) VALUES
('33333333-3333-3333-3333-333333333333', 'Alle producten', 'alle-producten', null, 'shopping_cart', 0);

-- Update the updated_at timestamp for all records
UPDATE supermarkets SET updated_at = NOW();
UPDATE categories SET created_at = NOW();