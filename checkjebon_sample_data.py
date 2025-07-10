#!/usr/bin/env python3
"""
Sample CheckjeBon Data Generator
===============================

Generates sample CheckjeBon data for testing the import script
when the actual CheckjeBon API is not available.

This script creates realistic sample data that matches the expected
format of the CheckjeBon API responses.
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict

# Sample data for realistic product generation
SUPERMARKETS = [
    {"key": "albert-heijn", "name": "Albert Heijn"},
    {"key": "jumbo", "name": "Jumbo"},
    {"key": "lidl", "name": "Lidl"},
    {"key": "aldi", "name": "Aldi"},
    {"key": "plus", "name": "Plus"},
    {"key": "coop", "name": "Coop"},
    {"key": "vomar", "name": "Vomar"},
    {"key": "dirk", "name": "Dirk van den Broek"},
    {"key": "hoogvliet", "name": "Hoogvliet"},
    {"key": "spar", "name": "Spar"},
    {"key": "boni", "name": "Boni"},
]

CATEGORIES = [
    "zuivel-eieren",
    "brood-gebak",
    "groente-fruit",
    "vlees-vis-vegetarisch",
    "dranken",
    "rijst-pasta-internationale-keuken",
    "soepen-conserven-sauzen",
    "snoep-koek-chips",
    "diepvries",
    "baby-verzorging",
    "huishouden-dieren",
    "persoonlijke-verzorging",
]

BRANDS = [
    "Albert Heijn", "Jumbo", "Campina", "Douwe Egberts", "Coca Cola",
    "Heineken", "Unilever", "Nestlé", "Danone", "Verkade",
    "Calvé", "Conimex", "Honig", "Maggi", "Knorr",
    "Friesche Vlag", "Melkunie", "Johma", "Hak", "Hero",
    "Iglo", "Findus", "McCain", "Ben & Jerry's", "Häagen-Dazs",
    "Mora", "Kips", "Knaks", "Hema", "Kruidvat"
]

PRODUCT_TEMPLATES = {
    "zuivel-eieren": [
        {"name": "Melk halfvol", "sizes": ["1L", "500ml", "250ml"], "price_range": (0.89, 1.49)},
        {"name": "Melk vol", "sizes": ["1L", "500ml"], "price_range": (0.95, 1.55)},
        {"name": "Yoghurt naturel", "sizes": ["500g", "1kg", "150g"], "price_range": (0.65, 2.99)},
        {"name": "Eieren", "sizes": ["6 stuks", "12 stuks", "18 stuks"], "price_range": (1.49, 4.99)},
        {"name": "Boter", "sizes": ["250g", "500g"], "price_range": (1.99, 3.99)},
        {"name": "Kaas jong belegen", "sizes": ["300g", "450g"], "price_range": (2.99, 5.99)},
        {"name": "Kwark naturel", "sizes": ["500g", "1kg"], "price_range": (1.29, 2.49)},
        {"name": "Roomboter", "sizes": ["250g", "500g"], "price_range": (2.49, 4.99)},
    ],
    "brood-gebak": [
        {"name": "Volkoren brood", "sizes": ["800g", "400g"], "price_range": (1.49, 2.99)},
        {"name": "Wit brood", "sizes": ["800g", "400g"], "price_range": (1.29, 2.49)},
        {"name": "Croissants", "sizes": ["4 stuks", "6 stuks"], "price_range": (1.99, 3.49)},
        {"name": "Beschuit", "sizes": ["125g", "250g"], "price_range": (1.79, 3.49)},
        {"name": "Ontbijtkoek", "sizes": ["475g", "950g"], "price_range": (1.99, 3.99)},
    ],
    "groente-fruit": [
        {"name": "Appels", "sizes": ["1kg", "2kg", "500g"], "price_range": (1.99, 3.99)},
        {"name": "Bananen", "sizes": ["1kg", "500g"], "price_range": (1.49, 2.99)},
        {"name": "Tomaten", "sizes": ["500g", "1kg"], "price_range": (1.99, 3.49)},
        {"name": "Komkommer", "sizes": ["1 stuk"], "price_range": (0.79, 1.29)},
        {"name": "Aardappelen", "sizes": ["2kg", "5kg", "1kg"], "price_range": (1.99, 4.99)},
        {"name": "Wortelen", "sizes": ["1kg", "500g"], "price_range": (0.99, 1.99)},
        {"name": "Sla", "sizes": ["1 stuk"], "price_range": (0.89, 1.49)},
    ],
    "dranken": [
        {"name": "Coca Cola", "sizes": ["330ml", "500ml", "1.5L", "2L"], "price_range": (0.79, 2.99)},
        {"name": "Spa blauw", "sizes": ["500ml", "1.5L", "6x500ml"], "price_range": (0.49, 2.49)},
        {"name": "Koffie", "sizes": ["250g", "500g", "1kg"], "price_range": (2.99, 8.99)},
        {"name": "Thee", "sizes": ["20 zakjes", "40 zakjes"], "price_range": (1.49, 3.99)},
        {"name": "Bier", "sizes": ["330ml", "500ml", "6x330ml"], "price_range": (0.69, 5.99)},
        {"name": "Sinaasappelsap", "sizes": ["1L", "500ml"], "price_range": (1.29, 2.49)},
    ],
    "vlees-vis-vegetarisch": [
        {"name": "Gehakt", "sizes": ["500g", "1kg"], "price_range": (3.99, 7.99)},
        {"name": "Kipfilet", "sizes": ["300g", "500g"], "price_range": (2.99, 5.99)},
        {"name": "Zalm", "sizes": ["200g", "400g"], "price_range": (4.99, 9.99)},
        {"name": "Vegetarische burger", "sizes": ["2 stuks", "4 stuks"], "price_range": (2.99, 5.99)},
        {"name": "Worst", "sizes": ["200g", "400g"], "price_range": (1.99, 3.99)},
    ],
}

def generate_ean() -> str:
    """Generate a fake EAN-13 barcode"""
    return "87" + "".join([str(random.randint(0, 9)) for _ in range(11)])

def generate_product_for_supermarket(supermarket: str, template: Dict, category: str) -> Dict:
    """Generate a single product for a supermarket"""
    base_price = random.uniform(template["price_range"][0], template["price_range"][1])
    size = random.choice(template["sizes"])
    brand = random.choice(BRANDS) if random.random() > 0.3 else None
    
    # Create product name
    name = template["name"]
    if brand and random.random() > 0.5:
        name = f"{brand} {name}"
    
    # Add size to name sometimes
    if random.random() > 0.7:
        name = f"{name} {size}"
    
    # Generate variations in price between supermarkets
    price_variation = random.uniform(0.8, 1.2)
    price = round(base_price * price_variation, 2)
    
    # Sometimes products are on sale
    is_on_sale = random.random() < 0.15
    original_price = None
    discount_percentage = None
    
    if is_on_sale:
        original_price = price
        discount_percentage = random.randint(10, 40)
        price = round(price * (1 - discount_percentage / 100), 2)
    
    # Parse unit size for price per unit calculation
    unit_size = None
    unit_type = None
    
    if "ml" in size:
        unit_size = int(size.replace("ml", ""))
        unit_type = "ml"
    elif "L" in size:
        unit_size = int(float(size.replace("L", "")) * 1000)
        unit_type = "ml"
    elif "g" in size:
        unit_size = int(size.replace("g", ""))
        unit_type = "g"
    elif "kg" in size:
        unit_size = int(float(size.replace("kg", "")) * 1000)
        unit_type = "g"
    elif "stuks" in size:
        unit_size = int(size.split()[0])
        unit_type = "stuks"
    
    product = {
        "name": name,
        "brand": brand,
        "size": size,
        "ean": generate_ean(),
        "price": price,
        "supermarket": supermarket,
        "category": category,
        "description": f"{name} - {size}",
        "image_url": f"https://example.com/images/{generate_ean()}.jpg",
        "unit_size": unit_size,
        "unit_type": unit_type,
        "is_available": random.random() > 0.05,  # 95% availability
        "is_on_sale": is_on_sale,
        "original_price": original_price,
        "discount_percentage": discount_percentage,
    }
    
    return product

def generate_sample_data(supermarket: str = None, limit: int = 1000) -> List[Dict]:
    """Generate sample CheckjeBon data"""
    products = []
    
    # Select supermarkets to generate data for
    if supermarket:
        supermarkets = [sm for sm in SUPERMARKETS if sm["key"] == supermarket]
        if not supermarkets:
            raise ValueError(f"Unknown supermarket: {supermarket}")
    else:
        supermarkets = SUPERMARKETS
    
    # Generate products for each supermarket
    products_per_supermarket = limit // len(supermarkets) if limit else 100
    
    for sm in supermarkets:
        supermarket_products = []
        
        # Generate products for each category
        for category in CATEGORIES:
            if category in PRODUCT_TEMPLATES:
                templates = PRODUCT_TEMPLATES[category]
                
                # Generate multiple products per template
                for template in templates:
                    # Generate 1-3 variations per template
                    for _ in range(random.randint(1, 3)):
                        if len(supermarket_products) < products_per_supermarket:
                            product = generate_product_for_supermarket(sm["key"], template, category)
                            supermarket_products.append(product)
        
        # Add some random products to reach the limit
        while len(supermarket_products) < products_per_supermarket:
            category = random.choice(CATEGORIES)
            if category in PRODUCT_TEMPLATES:
                template = random.choice(PRODUCT_TEMPLATES[category])
                product = generate_product_for_supermarket(sm["key"], template, category)
                supermarket_products.append(product)
        
        products.extend(supermarket_products[:products_per_supermarket])
    
    return products[:limit] if limit else products

def save_sample_data(filename: str = "sample_checkjebon_data.json", **kwargs):
    """Save sample data to JSON file"""
    data = generate_sample_data(**kwargs)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Generated {len(data)} sample products and saved to {filename}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate sample CheckjeBon data")
    parser.add_argument("--supermarket", help="Generate data for specific supermarket")
    parser.add_argument("--limit", type=int, default=1000, help="Number of products to generate")
    parser.add_argument("--output", default="sample_checkjebon_data.json", help="Output filename")
    
    args = parser.parse_args()
    
    save_sample_data(
        filename=args.output,
        supermarket=args.supermarket,
        limit=args.limit
    )