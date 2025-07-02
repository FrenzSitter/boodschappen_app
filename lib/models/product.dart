class Product {
  final String id;
  final String name;
  final String? brand;
  final String? categoryId;
  final String? categoryName;
  final String? barcode;
  final String? imageUrl;
  final String unitType;
  final double? packageSize;
  final String? packageUnit;
  final String? description;
  final bool isOrganic;
  final bool isBio;
  final DateTime createdAt;
  final DateTime updatedAt;

  Product({
    required this.id,
    required this.name,
    this.brand,
    this.categoryId,
    this.categoryName,
    this.barcode,
    this.imageUrl,
    required this.unitType,
    this.packageSize,
    this.packageUnit,
    this.description,
    required this.isOrganic,
    required this.isBio,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    // Handle category data from joined response
    String? categoryName;
    String? categoryId;
    
    if (json['category'] != null && json['category'] is Map) {
      final categoryData = json['category'] as Map<String, dynamic>;
      categoryName = categoryData['name'] as String?;
      categoryId = categoryData['id'] as String?;
    } else {
      categoryName = json['category_name'] as String?;
      categoryId = json['category_id'] as String?;
    }
    
    return Product(
      id: json['id'].toString(),
      name: json['name'] as String,
      brand: json['brand'] as String?,
      categoryId: categoryId,
      categoryName: categoryName,
      barcode: json['barcode'] as String?,
      imageUrl: json['image_url'] as String?,
      unitType: json['unit_type'] as String? ?? 'piece',
      packageSize: (json['package_size'] as num?)?.toDouble(),
      packageUnit: json['package_unit'] as String?,
      description: json['description'] as String?,
      isOrganic: json['is_organic'] as bool? ?? false,
      isBio: json['is_bio'] as bool? ?? false,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'brand': brand,
      'category_id': categoryId,
      'category_name': categoryName,
      'barcode': barcode,
      'image_url': imageUrl,
      'unit_type': unitType,
      'package_size': packageSize,
      'package_unit': packageUnit,
      'description': description,
      'is_organic': isOrganic,
      'is_bio': isBio,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}

class ProductPrice {
  final String id;
  final String productId;
  final String supermarketId;
  final String supermarketName;
  final String supermarketSlug;
  final double price;
  final double? originalPrice;
  final double? discountPercentage;
  final double? pricePerUnit;
  final String currency;
  final bool isAvailable;
  final bool isOnSale;
  final DateTime? saleStartDate;
  final DateTime? saleEndDate;
  final DateTime lastUpdated;

  ProductPrice({
    required this.id,
    required this.productId,
    required this.supermarketId,
    required this.supermarketName,
    required this.supermarketSlug,
    required this.price,
    this.originalPrice,
    this.discountPercentage,
    this.pricePerUnit,
    required this.currency,
    required this.isAvailable,
    required this.isOnSale,
    this.saleStartDate,
    this.saleEndDate,
    required this.lastUpdated,
  });

  factory ProductPrice.fromJson(Map<String, dynamic> json) {
    return ProductPrice(
      id: json['id'] as String,
      productId: json['product_id'] as String,
      supermarketId: json['supermarket_id'] as String,
      supermarketName: json['supermarket_name'] as String,
      supermarketSlug: json['supermarket_slug'] as String,
      price: (json['price'] as num).toDouble(),
      originalPrice: (json['original_price'] as num?)?.toDouble(),
      discountPercentage: (json['discount_percentage'] as num?)?.toDouble(),
      pricePerUnit: (json['price_per_unit'] as num?)?.toDouble(),
      currency: json['currency'] as String? ?? 'EUR',
      isAvailable: json['is_available'] as bool? ?? true,
      isOnSale: json['is_on_sale'] as bool? ?? false,
      saleStartDate: json['sale_start_date'] != null 
          ? DateTime.parse(json['sale_start_date'] as String)
          : null,
      saleEndDate: json['sale_end_date'] != null 
          ? DateTime.parse(json['sale_end_date'] as String)
          : null,
      lastUpdated: DateTime.parse(json['last_updated'] as String),
    );
  }
}

class ProductWithPrices {
  final Product product;
  final List<ProductPrice> prices;

  ProductWithPrices({
    required this.product,
    required this.prices,
  });

  double? get lowestPrice {
    if (prices.isEmpty) return null;
    return prices.map((p) => p.price).reduce((a, b) => a < b ? a : b);
  }

  double? get highestPrice {
    if (prices.isEmpty) return null;
    return prices.map((p) => p.price).reduce((a, b) => a > b ? a : b);
  }

  ProductPrice? get cheapestPrice {
    if (prices.isEmpty) return null;
    return prices.reduce((a, b) => a.price < b.price ? a : b);
  }

  List<ProductPrice> get availablePrices {
    return prices.where((p) => p.isAvailable).toList();
  }
}

class Supermarket {
  final String id;
  final String name;
  final String slug;
  final String? logoUrl;
  final String? websiteUrl;
  final String? colorPrimary;
  final String? colorSecondary;
  final bool isActive;

  Supermarket({
    required this.id,
    required this.name,
    required this.slug,
    this.logoUrl,
    this.websiteUrl,
    this.colorPrimary,
    this.colorSecondary,
    required this.isActive,
  });

  factory Supermarket.fromJson(Map<String, dynamic> json) {
    return Supermarket(
      id: json['id'] as String,
      name: json['name'] as String,
      slug: json['slug'] as String,
      logoUrl: json['logo_url'] as String?,
      websiteUrl: json['website_url'] as String?,
      colorPrimary: json['color_primary'] as String?,
      colorSecondary: json['color_secondary'] as String?,
      isActive: json['is_active'] as bool? ?? true,
    );
  }
}

class Category {
  final String id;
  final String name;
  final String slug;
  final String? parentId;
  final String? iconName;
  final int displayOrder;

  Category({
    required this.id,
    required this.name,
    required this.slug,
    this.parentId,
    this.iconName,
    required this.displayOrder,
  });

  factory Category.fromJson(Map<String, dynamic> json) {
    return Category(
      id: json['id'] as String,
      name: json['name'] as String,
      slug: json['slug'] as String,
      parentId: json['parent_id'] as String?,
      iconName: json['icon_name'] as String?,
      displayOrder: json['display_order'] as int? ?? 0,
    );
  }
}

class SearchFilters {
  final String? query;
  final List<String>? supermarketIds;
  final String? categoryId;
  final double? minPrice;
  final double? maxPrice;
  final bool? isOrganic;
  final bool? isBio;
  final bool? isOnSale;

  SearchFilters({
    this.query,
    this.supermarketIds,
    this.categoryId,
    this.minPrice,
    this.maxPrice,
    this.isOrganic,
    this.isBio,
    this.isOnSale,
  });

  SearchFilters copyWith({
    String? query,
    List<String>? supermarketIds,
    String? categoryId,
    double? minPrice,
    double? maxPrice,
    bool? isOrganic,
    bool? isBio,
    bool? isOnSale,
  }) {
    return SearchFilters(
      query: query ?? this.query,
      supermarketIds: supermarketIds ?? this.supermarketIds,
      categoryId: categoryId ?? this.categoryId,
      minPrice: minPrice ?? this.minPrice,
      maxPrice: maxPrice ?? this.maxPrice,
      isOrganic: isOrganic ?? this.isOrganic,
      isBio: isBio ?? this.isBio,
      isOnSale: isOnSale ?? this.isOnSale,
    );
  }
}