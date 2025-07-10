"""
Utility functions for CheckjeBon API
====================================
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def format_error_response(message: str, status_code: int = 500, error_code: str = None, details: Dict[str, Any] = None) -> Dict[str, Any]:
    """Format error response"""
    return {
        "success": False,
        "message": message,
        "error_code": error_code,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat()
    }

def paginate_response(data: List[Any], page: int, limit: int, total: int = None) -> Dict[str, Any]:
    """Add pagination information to response"""
    if total is None:
        total = len(data)
    
    total_pages = (total + limit - 1) // limit
    has_next = page < total_pages
    has_prev = page > 1
    
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev,
        "next_page": page + 1 if has_next else None,
        "prev_page": page - 1 if has_prev else None
    }

def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID format"""
    try:
        import uuid
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False

def clean_search_query(query: str) -> str:
    """Clean and normalize search query"""
    if not query:
        return ""
    
    # Remove special characters and extra spaces
    import re
    cleaned = re.sub(r'[^\w\s]', ' ', query)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    return cleaned.strip().lower()

def calculate_price_per_unit(price: float, package_size: float, package_unit: str) -> Optional[float]:
    """Calculate price per unit"""
    if not price or not package_size:
        return None
    
    # Convert to standard units
    if package_unit in ['g', 'gram']:
        # Convert to kg
        return price / (package_size / 1000)
    elif package_unit in ['ml', 'milliliter']:
        # Convert to liter
        return price / (package_size / 1000)
    elif package_unit in ['kg', 'kilogram', 'l', 'liter']:
        return price / package_size
    else:
        # For pieces, etc.
        return price / package_size

def extract_brand_from_name(product_name: str) -> Optional[str]:
    """Extract brand from product name"""
    if not product_name:
        return None
    
    # Common Dutch brands
    brands = [
        'AH', 'Albert Heijn', 'Jumbo', 'Plus', 'Coop', 'Dirk', 'Aldi',
        'Campina', 'Douwe Egberts', 'Coca Cola', 'Heineken', 'Unilever',
        'Nestlé', 'Danone', 'Friesche Vlag', 'Verkade', 'Liga', 'Calvé',
        'Knorr', 'Maggi', 'Hero', 'Ben & Jerry', 'Magnum', 'Cornetto'
    ]
    
    product_lower = product_name.lower()
    
    for brand in brands:
        if brand.lower() in product_lower:
            return brand
    
    # Try to extract first word as potential brand
    words = product_name.split()
    if words and len(words[0]) > 2 and words[0].isalpha():
        return words[0]
    
    return None

def categorize_product(product_name: str) -> Optional[str]:
    """Categorize product based on name"""
    if not product_name:
        return None
    
    name_lower = product_name.lower()
    
    # Category keywords
    categories = {
        'zuivel-eieren': ['melk', 'yoghurt', 'kaas', 'boter', 'ei', 'eieren', 'kwark', 'room'],
        'brood-gebak': ['brood', 'stokbrood', 'croissant', 'beschuit', 'cake', 'koek'],
        'groente-fruit': ['appel', 'banaan', 'tomaat', 'ui', 'wortel', 'sla', 'komkommer'],
        'vlees-vis-vegetarisch': ['vlees', 'kip', 'vis', 'gehakt', 'worst', 'ham'],
        'dranken': ['cola', 'sap', 'water', 'bier', 'koffie', 'thee', 'wijn'],
        'diepvries': ['diepvries', 'frozen', 'ijs', 'ijsje'],
        'houdbaar': ['pasta', 'rijst', 'meel', 'suiker', 'conserven'],
        'snacks-snoep': ['chips', 'koekjes', 'chocolade', 'snoep', 'noten'],
        'verzorging': ['shampoo', 'tandpasta', 'zeep', 'deodorant'],
        'huishouden': ['wasmiddel', 'afwasmiddel', 'toiletpapier', 'keukenrol']
    }
    
    for category, keywords in categories.items():
        if any(keyword in name_lower for keyword in keywords):
            return category
    
    return 'houdbaar'  # Default category

def format_price(price: float, currency: str = 'EUR') -> str:
    """Format price for display"""
    if currency == 'EUR':
        return f"€{price:.2f}"
    else:
        return f"{price:.2f} {currency}"

def calculate_discount_percentage(original_price: float, current_price: float) -> float:
    """Calculate discount percentage"""
    if not original_price or original_price <= 0:
        return 0.0
    
    discount = original_price - current_price
    return (discount / original_price) * 100

def parse_size_text(size_text: str) -> Dict[str, Any]:
    """Parse size text into structured data"""
    if not size_text:
        return {}
    
    import re
    
    # Common patterns
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(ml|l|liter|gram|g|kg|kilogram|stuks?|st)',
        r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(ml|l|gram|g|kg)',
        r'(\d+(?:\.\d+)?)\s*(ml|l|gram|g|kg)'
    ]
    
    size_lower = size_text.lower()
    
    for pattern in patterns:
        match = re.search(pattern, size_lower)
        if match:
            if len(match.groups()) == 2:
                size, unit = match.groups()
                return {
                    'size': float(size),
                    'unit': unit,
                    'original_text': size_text
                }
            elif len(match.groups()) == 3:
                count, size, unit = match.groups()
                return {
                    'size': float(count) * float(size),
                    'unit': unit,
                    'count': float(count),
                    'individual_size': float(size),
                    'original_text': size_text
                }
    
    return {'original_text': size_text}

def generate_search_terms(product_name: str) -> List[str]:
    """Generate search terms for full-text search"""
    if not product_name:
        return []
    
    # Clean the name
    clean_name = clean_search_query(product_name)
    
    # Split into words
    words = clean_name.split()
    
    # Generate terms
    terms = []
    
    # Individual words
    terms.extend(words)
    
    # Bigrams
    for i in range(len(words) - 1):
        terms.append(f"{words[i]} {words[i+1]}")
    
    # Trigrams
    for i in range(len(words) - 2):
        terms.append(f"{words[i]} {words[i+1]} {words[i+2]}")
    
    # Remove duplicates and short terms
    terms = list(set(term for term in terms if len(term) >= 2))
    
    return terms

def log_api_request(endpoint: str, method: str, user_ip: str, response_time: float, status_code: int):
    """Log API request"""
    logger.info(f"API Request: {method} {endpoint} - IP: {user_ip} - Time: {response_time:.3f}s - Status: {status_code}")

def validate_price_range(min_price: float, max_price: float) -> bool:
    """Validate price range"""
    if min_price is not None and min_price < 0:
        return False
    
    if max_price is not None and max_price < 0:
        return False
    
    if min_price is not None and max_price is not None and min_price > max_price:
        return False
    
    return True

def sanitize_input(input_string: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    if not input_string:
        return ""
    
    # Remove potentially harmful characters
    import re
    sanitized = re.sub(r'[<>"\']', '', input_string)
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()

def get_client_ip(request) -> str:
    """Get client IP address from request"""
    # Check for forwarded headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to remote address
    return getattr(request.client, "host", "unknown")

def create_api_response(success: bool, message: str, data: Any = None, 
                       pagination: Dict[str, Any] = None, errors: List[str] = None) -> Dict[str, Any]:
    """Create standardized API response"""
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if pagination:
        response["pagination"] = pagination
    
    if errors:
        response["errors"] = errors
    
    return response