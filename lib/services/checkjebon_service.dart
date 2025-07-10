import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/product.dart';

class CheckjebonService {
  static const String _baseUrl = 'https://raw.githubusercontent.com/supermarkt/checkjebon/refs/heads/main/data';
  
  /// Fetch products from checkjebon.nl supermarkets data
  static Future<List<CheckjebonProduct>> fetchProducts() async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/supermarkets.json'),
        headers: {'Accept': 'application/json'},
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> jsonData = json.decode(response.body);
        return jsonData.map((item) => CheckjebonProduct.fromJson(item)).toList();
      } else {
        throw Exception('Failed to load products: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching checkjebon.nl products: $e');
      rethrow;
    }
  }
  
  /// Search products by name
  static Future<List<CheckjebonProduct>> searchProducts(String query) async {
    try {
      final allProducts = await fetchProducts();
      
      if (query.isEmpty) {
        return allProducts;
      }
      
      final searchQuery = query.toLowerCase();
      
      // Filter products that match the search query
      return allProducts.where((product) {
        return product.name.toLowerCase().contains(searchQuery);
      }).toList();
    } catch (e) {
      print('Error searching products: $e');
      return [];
    }
  }
  
  /// Get product by exact name match
  static Future<CheckjebonProduct?> getProductByName(String name) async {
    try {
      final allProducts = await fetchProducts();
      
      return allProducts.firstWhere(
        (product) => product.name.toLowerCase() == name.toLowerCase(),
        orElse: () => throw StateError('Product not found'),
      );
    } catch (e) {
      print('Error getting product by name: $e');
      return null;
    }
  }
  
  /// Get products by category (simple text matching)
  static Future<List<CheckjebonProduct>> getProductsByCategory(String category) async {
    try {
      final allProducts = await fetchProducts();
      
      final categoryQuery = category.toLowerCase();
      
      // Simple category matching based on product names
      return allProducts.where((product) {
        final productName = product.name.toLowerCase();
        
        // Define category keywords
        switch (categoryQuery) {
          case 'zuivel':
          case 'melk':
            return productName.contains('melk') || 
                   productName.contains('yoghurt') || 
                   productName.contains('kaas') || 
                   productName.contains('boter');
          case 'groente':
          case 'fruit':
            return productName.contains('appel') || 
                   productName.contains('banaan') || 
                   productName.contains('tomaat') || 
                   productName.contains('ui') ||
                   productName.contains('wortel');
          case 'brood':
            return productName.contains('brood') || 
                   productName.contains('stokbrood') || 
                   productName.contains('croissant');
          case 'dranken':
            return productName.contains('cola') || 
                   productName.contains('sap') || 
                   productName.contains('water') || 
                   productName.contains('bier') ||
                   productName.contains('koffie');
          default:
            return productName.contains(categoryQuery);
        }
      }).toList();
    } catch (e) {
      print('Error getting products by category: $e');
      return [];
    }
  }
  
  /// Get products with price range filtering
  static Future<List<CheckjebonProduct>> getProductsByPriceRange({
    double? minPrice,
    double? maxPrice,
  }) async {
    try {
      final allProducts = await fetchProducts();
      
      return allProducts.where((product) {
        if (minPrice != null && product.price < minPrice) {
          return false;
        }
        if (maxPrice != null && product.price > maxPrice) {
          return false;
        }
        return true;
      }).toList();
    } catch (e) {
      print('Error filtering products by price: $e');
      return [];
    }
  }
  
  /// Get top products by lowest price
  static Future<List<CheckjebonProduct>> getCheapestProducts({int limit = 20}) async {
    try {
      final allProducts = await fetchProducts();
      
      // Sort by price (ascending) and take the cheapest ones
      allProducts.sort((a, b) => a.price.compareTo(b.price));
      
      return allProducts.take(limit).toList();
    } catch (e) {
      print('Error getting cheapest products: $e');
      return [];
    }
  }
  
  /// Convert CheckjebonProduct to our app's Product model
  static Product convertToProduct(CheckjebonProduct checkjebonProduct, String categoryId) {
    return Product(
      id: checkjebonProduct.link, // Use link as unique identifier
      name: checkjebonProduct.name,
      brand: _extractBrand(checkjebonProduct.name),
      categoryId: categoryId,
      categoryName: _inferCategory(checkjebonProduct.name),
      barcode: null, // checkjebon.nl doesn't provide barcodes
      imageUrl: null, // checkjebon.nl doesn't provide images
      unitType: _extractUnitType(checkjebonProduct.size),
      packageSize: _extractPackageSize(checkjebonProduct.size),
      packageUnit: _extractPackageUnit(checkjebonProduct.size),
      description: checkjebonProduct.size,
      isOrganic: _isOrganic(checkjebonProduct.name),
      isBio: _isBio(checkjebonProduct.name),
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );
  }
  
  /// Convert CheckjebonProduct to ProductPrice for Albert Heijn
  static ProductPrice convertToProductPrice(CheckjebonProduct checkjebonProduct, String productId) {
    return ProductPrice(
      id: '${checkjebonProduct.link}_ah',
      productId: productId,
      supermarketId: 'albert-heijn', // checkjebon.nl data appears to be from Albert Heijn
      supermarketName: 'Albert Heijn',
      supermarketSlug: 'albert-heijn',
      price: checkjebonProduct.price,
      pricePerUnit: checkjebonProduct.price, // Would need more logic to calculate actual per-unit price
      currency: 'EUR',
      isAvailable: true,
      isOnSale: false,
      lastUpdated: DateTime.now(),
    );
  }
  
  // Helper methods
  static String? _extractBrand(String productName) {
    // Try to extract brand from product name
    final lowerName = productName.toLowerCase();
    
    // Common Dutch brands
    if (lowerName.contains('ah ')) return 'AH';
    if (lowerName.contains('jumbo')) return 'Jumbo';
    if (lowerName.contains('campina')) return 'Campina';
    if (lowerName.contains('douwe egberts')) return 'Douwe Egberts';
    if (lowerName.contains('coca cola') || lowerName.contains('coca-cola')) return 'Coca-Cola';
    if (lowerName.contains('heineken')) return 'Heineken';
    if (lowerName.contains('unilever')) return 'Unilever';
    if (lowerName.contains('nestlé') || lowerName.contains('nestle')) return 'Nestlé';
    
    return null;
  }
  
  static String _inferCategory(String productName) {
    final lowerName = productName.toLowerCase();
    
    if (lowerName.contains('melk') || lowerName.contains('yoghurt') || lowerName.contains('kaas')) {
      return 'Zuivel & eieren';
    } else if (lowerName.contains('brood') || lowerName.contains('stokbrood')) {
      return 'Brood & gebak';
    } else if (lowerName.contains('appel') || lowerName.contains('banaan') || lowerName.contains('tomaat')) {
      return 'Groente & fruit';
    } else if (lowerName.contains('cola') || lowerName.contains('sap') || lowerName.contains('water')) {
      return 'Dranken';
    } else if (lowerName.contains('vlees') || lowerName.contains('kip') || lowerName.contains('vis')) {
      return 'Vlees, vis & vegetarisch';
    } else if (lowerName.contains('diepvries') || lowerName.contains('frozen')) {
      return 'Diepvries';
    } else {
      return 'Houdbaar';
    }
  }
  
  static String _extractUnitType(String size) {
    final lowerSize = size.toLowerCase();
    
    if (lowerSize.contains('kg')) return 'kg';
    if (lowerSize.contains('gram') || lowerSize.contains('g ')) return 'gram';
    if (lowerSize.contains('liter') || lowerSize.contains('l ')) return 'liter';
    if (lowerSize.contains('ml')) return 'ml';
    if (lowerSize.contains('stuks') || lowerSize.contains('st ')) return 'piece';
    
    return 'piece';
  }
  
  static double? _extractPackageSize(String size) {
    // Extract numeric value from size string
    final regex = RegExp(r'(\d+(?:\.\d+)?)');
    final match = regex.firstMatch(size);
    
    if (match != null) {
      return double.tryParse(match.group(1)!);
    }
    
    return null;
  }
  
  static String _extractPackageUnit(String size) {
    final lowerSize = size.toLowerCase();
    
    if (lowerSize.contains('kg')) return 'kg';
    if (lowerSize.contains('gram') || lowerSize.contains('g')) return 'g';
    if (lowerSize.contains('liter') || lowerSize.contains('l')) return 'l';
    if (lowerSize.contains('ml')) return 'ml';
    if (lowerSize.contains('stuks') || lowerSize.contains('st')) return 'stuks';
    
    return 'stuks';
  }
  
  static bool _isOrganic(String productName) {
    final lowerName = productName.toLowerCase();
    return lowerName.contains('organic') || lowerName.contains('biologisch');
  }
  
  static bool _isBio(String productName) {
    final lowerName = productName.toLowerCase();
    return lowerName.contains('bio ') || lowerName.contains('biologisch');
  }
}

/// Model for checkjebon.nl product data
class CheckjebonProduct {
  final String name;
  final String link;
  final double price;
  final String size;
  
  CheckjebonProduct({
    required this.name,
    required this.link,
    required this.price,
    required this.size,
  });
  
  factory CheckjebonProduct.fromJson(Map<String, dynamic> json) {
    return CheckjebonProduct(
      name: json['n'] ?? '',
      link: json['l'] ?? '',
      price: (json['p'] as num?)?.toDouble() ?? 0.0,
      size: json['s'] ?? '',
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'n': name,
      'l': link,
      'p': price,
      's': size,
    };
  }
  
  @override
  String toString() {
    return 'CheckjebonProduct{name: $name, price: €$price, size: $size}';
  }
}