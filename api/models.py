"""
Pydantic Models for CheckjeBon API
==================================

Data models for request/response serialization and validation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from pydantic.types import UUID4
from enum import Enum

class SupermarketStatus(str, Enum):
    """Supermarket status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

class Supermarket(BaseModel):
    """Supermarket model"""
    id: UUID4
    name: str = Field(..., description="Supermarket name")
    slug: str = Field(..., description="URL-friendly slug")
    checkjebon_key: Optional[str] = Field(None, description="CheckjeBon identifier")
    logo_url: Optional[str] = Field(None, description="Logo image URL")
    website_url: Optional[str] = Field(None, description="Official website")
    color_primary: Optional[str] = Field(None, description="Primary brand color")
    color_secondary: Optional[str] = Field(None, description="Secondary brand color")
    is_active: bool = Field(True, description="Whether supermarket is active")
    has_online_data: bool = Field(False, description="Whether online data is available")
    last_data_update: Optional[datetime] = Field(None, description="Last data update timestamp")
    created_at: datetime = Field(..., description="Created timestamp")
    updated_at: datetime = Field(..., description="Updated timestamp")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Albert Heijn",
                "slug": "albert-heijn",
                "checkjebon_key": "ah",
                "logo_url": "https://example.com/logo.png",
                "website_url": "https://ah.nl",
                "color_primary": "#0051A5",
                "color_secondary": "#ffffff",
                "is_active": True,
                "has_online_data": True,
                "last_data_update": "2025-01-09T10:00:00Z",
                "created_at": "2025-01-09T09:00:00Z",
                "updated_at": "2025-01-09T10:00:00Z"
            }
        }

class Category(BaseModel):
    """Product category model"""
    id: UUID4
    name: str = Field(..., description="Category name")
    slug: str = Field(..., description="URL-friendly slug")
    parent_id: Optional[UUID4] = Field(None, description="Parent category ID")
    dutch_keywords: Optional[List[str]] = Field(None, description="Dutch keywords for categorization")
    icon_name: Optional[str] = Field(None, description="Icon name")
    description: Optional[str] = Field(None, description="Category description")
    display_order: int = Field(0, description="Display order")
    is_active: bool = Field(True, description="Whether category is active")
    created_at: datetime = Field(..., description="Created timestamp")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Zuivel & eieren",
                "slug": "zuivel-eieren",
                "parent_id": None,
                "dutch_keywords": ["melk", "yoghurt", "kaas", "eieren"],
                "icon_name": "egg",
                "description": "Dairy products and eggs",
                "display_order": 1,
                "is_active": True,
                "created_at": "2025-01-09T09:00:00Z"
            }
        }

class ProductPrice(BaseModel):
    """Product price model"""
    id: UUID4
    product_id: UUID4
    supermarket_id: UUID4
    price: float = Field(..., ge=0, description="Product price")
    original_price: Optional[float] = Field(None, ge=0, description="Original price before discount")
    price_per_unit: Optional[float] = Field(None, ge=0, description="Price per unit (kg/liter)")
    discount_percentage: Optional[float] = Field(None, ge=0, le=100, description="Discount percentage")
    currency: str = Field("EUR", description="Currency code")
    is_available: bool = Field(True, description="Whether product is available")
    is_on_sale: bool = Field(False, description="Whether product is on sale")
    sale_start_date: Optional[datetime] = Field(None, description="Sale start date")
    sale_end_date: Optional[datetime] = Field(None, description="Sale end date")
    sale_type: Optional[str] = Field(None, description="Sale type")
    data_source: str = Field("checkjebon", description="Data source")
    confidence_score: int = Field(100, ge=0, le=100, description="Data confidence score")
    checkjebon_link: Optional[str] = Field(None, description="CheckjeBon link")
    last_updated: datetime = Field(..., description="Last updated timestamp")
    created_at: datetime = Field(..., description="Created timestamp")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "product_id": "123e4567-e89b-12d3-a456-426614174001",
                "supermarket_id": "123e4567-e89b-12d3-a456-426614174002",
                "price": 2.95,
                "original_price": 3.50,
                "price_per_unit": 2.95,
                "discount_percentage": 15.7,
                "currency": "EUR",
                "is_available": True,
                "is_on_sale": True,
                "sale_start_date": "2025-01-09T00:00:00Z",
                "sale_end_date": "2025-01-15T23:59:59Z",
                "sale_type": "percentage",
                "data_source": "checkjebon",
                "confidence_score": 95,
                "checkjebon_link": "https://checkjebon.nl/product/123",
                "last_updated": "2025-01-09T10:00:00Z",
                "created_at": "2025-01-09T09:00:00Z"
            }
        }

class Product(BaseModel):
    """Product model"""
    id: UUID4
    name: str = Field(..., description="Product name")
    normalized_name: Optional[str] = Field(None, description="Normalized product name")
    brand: Optional[str] = Field(None, description="Brand name")
    checkjebon_link: Optional[str] = Field(None, description="CheckjeBon link")
    source_supermarket_id: Optional[UUID4] = Field(None, description="Source supermarket ID")
    category_id: Optional[UUID4] = Field(None, description="Category ID")
    auto_category: Optional[str] = Field(None, description="Auto-inferred category")
    barcode: Optional[str] = Field(None, description="Product barcode")
    sku: Optional[str] = Field(None, description="Product SKU")
    description: Optional[str] = Field(None, description="Product description")
    size_text: Optional[str] = Field(None, description="Size description")
    unit_type: str = Field("piece", description="Unit type")
    package_size: Optional[float] = Field(None, ge=0, description="Package size")
    package_unit: Optional[str] = Field(None, description="Package unit")
    brand_extracted: Optional[str] = Field(None, description="Extracted brand")
    is_organic: bool = Field(False, description="Whether product is organic")
    is_bio: bool = Field(False, description="Whether product is bio")
    is_private_label: bool = Field(False, description="Whether product is private label")
    ingredients: Optional[str] = Field(None, description="Ingredients list")
    allergens: Optional[List[str]] = Field(None, description="Allergens list")
    nutritional_info: Optional[Dict[str, Any]] = Field(None, description="Nutritional information")
    image_url: Optional[str] = Field(None, description="Product image URL")
    image_urls: Optional[List[str]] = Field(None, description="Product image URLs")
    is_active: bool = Field(True, description="Whether product is active")
    quality_score: int = Field(100, ge=0, le=100, description="Data quality score")
    last_verified: Optional[datetime] = Field(None, description="Last verified timestamp")
    created_at: datetime = Field(..., description="Created timestamp")
    updated_at: datetime = Field(..., description="Updated timestamp")
    
    # Related objects
    supermarkets: Optional[Supermarket] = Field(None, description="Source supermarket")
    categories: Optional[Category] = Field(None, description="Product category")
    current_price: Optional[ProductPrice] = Field(None, description="Current price information")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "AH Melk halfvol 1L",
                "normalized_name": "ah melk halfvol 1l",
                "brand": "AH",
                "checkjebon_link": "https://checkjebon.nl/product/123",
                "source_supermarket_id": "123e4567-e89b-12d3-a456-426614174001",
                "category_id": "123e4567-e89b-12d3-a456-426614174002",
                "auto_category": "Zuivel & eieren",
                "barcode": "8710398123456",
                "sku": "AH-MILK-1L",
                "description": "Halfvolle melk van Nederlandse koeien",
                "size_text": "1 liter",
                "unit_type": "liter",
                "package_size": 1.0,
                "package_unit": "liter",
                "brand_extracted": "AH",
                "is_organic": False,
                "is_bio": False,
                "is_private_label": True,
                "ingredients": "Melk",
                "allergens": ["melk"],
                "nutritional_info": {
                    "energy_kj": 195,
                    "energy_kcal": 47,
                    "fat": 1.5,
                    "saturated_fat": 1.0,
                    "carbohydrates": 4.8,
                    "sugars": 4.8,
                    "protein": 3.4,
                    "salt": 0.1
                },
                "image_url": "https://example.com/product.jpg",
                "image_urls": ["https://example.com/product1.jpg", "https://example.com/product2.jpg"],
                "is_active": True,
                "quality_score": 95,
                "last_verified": "2025-01-09T10:00:00Z",
                "created_at": "2025-01-09T09:00:00Z",
                "updated_at": "2025-01-09T10:00:00Z"
            }
        }

class PriceHistory(BaseModel):
    """Price history model"""
    id: UUID4
    product_id: UUID4
    supermarket_id: UUID4
    price: float = Field(..., ge=0, description="Historical price")
    original_price: Optional[float] = Field(None, ge=0, description="Historical original price")
    price_per_unit: Optional[float] = Field(None, ge=0, description="Historical price per unit")
    price_change: Optional[float] = Field(None, description="Price change from previous")
    price_change_percentage: Optional[float] = Field(None, description="Price change percentage")
    change_reason: Optional[str] = Field(None, description="Reason for price change")
    data_source: str = Field("checkjebon", description="Data source")
    recorded_at: datetime = Field(..., description="When price was recorded")
    effective_from: datetime = Field(..., description="When price was effective from")
    effective_until: Optional[datetime] = Field(None, description="When price was effective until")
    
    # Related objects
    supermarkets: Optional[Supermarket] = Field(None, description="Supermarket information")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "product_id": "123e4567-e89b-12d3-a456-426614174001",
                "supermarket_id": "123e4567-e89b-12d3-a456-426614174002",
                "price": 2.95,
                "original_price": 3.50,
                "price_per_unit": 2.95,
                "price_change": -0.20,
                "price_change_percentage": -6.35,
                "change_reason": "sale_start",
                "data_source": "checkjebon",
                "recorded_at": "2025-01-09T10:00:00Z",
                "effective_from": "2025-01-09T00:00:00Z",
                "effective_until": None
            }
        }

# Response models
class ProductSearchResponse(BaseModel):
    """Product search response model"""
    query: str = Field(..., description="Search query")
    results: List[Product] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    page: int = Field(..., description="Current page")
    limit: int = Field(..., description="Results per page")
    filters: Dict[str, Any] = Field({}, description="Applied filters")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "melk",
                "results": [],
                "total_results": 25,
                "page": 1,
                "limit": 20,
                "filters": {
                    "supermarket_id": None,
                    "category_id": "123e4567-e89b-12d3-a456-426614174000",
                    "min_price": 1.0,
                    "max_price": 10.0
                }
            }
        }

class PriceComparisonResponse(BaseModel):
    """Price comparison response model"""
    query: str = Field(..., description="Product query")
    supermarkets: List[Dict[str, Any]] = Field(..., description="Supermarket comparison data")
    best_price: Optional[Dict[str, Any]] = Field(None, description="Best price information")
    price_range: Dict[str, Optional[float]] = Field({}, description="Price range statistics")
    total_results: int = Field(..., description="Total number of results")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "melk 1L",
                "supermarkets": [],
                "best_price": {
                    "supermarket": {},
                    "product": {},
                    "price": 1.85
                },
                "price_range": {
                    "min": 1.85,
                    "max": 2.95,
                    "average": 2.40
                },
                "total_results": 8
            }
        }

class PriceHistoryResponse(BaseModel):
    """Price history response model"""
    product: Product = Field(..., description="Product information")
    history: List[PriceHistory] = Field(..., description="Price history records")
    period_days: int = Field(..., description="Period in days")
    statistics: Dict[str, Any] = Field({}, description="Price statistics")
    total_records: int = Field(..., description="Total number of records")
    
    class Config:
        schema_extra = {
            "example": {
                "product": {},
                "history": [],
                "period_days": 30,
                "statistics": {
                    "min_price": 1.85,
                    "max_price": 2.95,
                    "avg_price": 2.40,
                    "current_price": 2.20,
                    "price_change": -0.15,
                    "price_change_percentage": -6.38
                },
                "total_records": 15
            }
        }

class APIResponse(BaseModel):
    """Generic API response model"""
    success: bool = Field(..., description="Whether request was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    pagination: Optional[Dict[str, Any]] = Field(None, description="Pagination information")
    errors: Optional[List[str]] = Field(None, description="Error messages")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Request completed successfully",
                "data": {},
                "pagination": {
                    "page": 1,
                    "limit": 20,
                    "total": 100,
                    "has_more": True
                },
                "errors": None,
                "timestamp": "2025-01-09T10:00:00Z"
            }
        }

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(False, description="Always false for errors")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "Product not found",
                "error_code": "PRODUCT_NOT_FOUND",
                "details": {
                    "product_id": "123e4567-e89b-12d3-a456-426614174000"
                },
                "timestamp": "2025-01-09T10:00:00Z"
            }
        }