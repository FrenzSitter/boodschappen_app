import 'package:uuid/uuid.dart';
import 'product.dart';

class ShoppingList {
  final String id;
  final String name;
  final String? description;
  final DateTime createdAt;
  final DateTime updatedAt;
  final bool isShared;
  final String? sharedCode;
  final List<ShoppingListItem> items;

  ShoppingList({
    required this.id,
    required this.name,
    this.description,
    required this.createdAt,
    required this.updatedAt,
    this.isShared = false,
    this.sharedCode,
    this.items = const [],
  });

  factory ShoppingList.fromJson(Map<String, dynamic> json) {
    return ShoppingList(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      isShared: json['is_shared'] ?? false,
      sharedCode: json['shared_code'],
      items: (json['items'] as List? ?? [])
          .map((item) => ShoppingListItem.fromJson(item))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      'is_shared': isShared,
      'shared_code': sharedCode,
    };
  }

  ShoppingList copyWith({
    String? id,
    String? name,
    String? description,
    DateTime? createdAt,
    DateTime? updatedAt,
    bool? isShared,
    String? sharedCode,
    List<ShoppingListItem>? items,
  }) {
    return ShoppingList(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      isShared: isShared ?? this.isShared,
      sharedCode: sharedCode ?? this.sharedCode,
      items: items ?? this.items,
    );
  }

  // Helper methods
  int get totalItems => items.length;
  int get checkedItems => items.where((item) => item.isChecked).length;
  double get completionPercentage => 
      totalItems > 0 ? (checkedItems / totalItems) * 100 : 0;
  
  double get estimatedTotal => items.fold(0.0, (sum, item) {
    if (item.productWithPrices != null && item.productWithPrices!.prices.isNotEmpty) {
      final cheapestPrice = item.productWithPrices!.prices
          .map((p) => p.price)
          .reduce((a, b) => a < b ? a : b);
      return sum + (cheapestPrice * item.quantity);
    }
    return sum;
  });

  static String generateId() => const Uuid().v4();
}

class ShoppingListItem {
  final String id;
  final String listId;
  final String? productId;
  final ProductWithPrices? productWithPrices;
  final String name;
  final int quantity;
  final String? notes;
  final bool isChecked;
  final DateTime createdAt;
  final DateTime updatedAt;

  ShoppingListItem({
    required this.id,
    required this.listId,
    this.productId,
    this.productWithPrices,
    required this.name,
    this.quantity = 1,
    this.notes,
    this.isChecked = false,
    required this.createdAt,
    required this.updatedAt,
  });

  factory ShoppingListItem.fromJson(Map<String, dynamic> json) {
    ProductWithPrices? productWithPrices;
    if (json['product'] != null) {
      final product = Product.fromJson(json['product']);
      // Convert product prices to ProductPrice objects
      final pricesData = json['product']['prices'] as List? ?? [];
      final prices = pricesData.map((priceData) {
        final supermarketData = priceData['supermarket'] ?? priceData['supermarkets'];
        return ProductPrice(
          id: priceData['id'].toString(),
          productId: product.id,
          supermarketId: supermarketData['id'].toString(),
          supermarketName: supermarketData['name'],
          supermarketSlug: supermarketData['slug'],
          price: (priceData['price'] as num).toDouble(),
          originalPrice: priceData['original_price'] != null 
              ? (priceData['original_price'] as num).toDouble() 
              : null,
          pricePerUnit: priceData['price_per_unit'] != null 
              ? (priceData['price_per_unit'] as num).toDouble() 
              : null,
          currency: priceData['currency'] ?? 'EUR',
          isAvailable: priceData['is_available'] ?? true,
          isOnSale: priceData['is_on_sale'] ?? false,
          lastUpdated: DateTime.parse(priceData['last_updated'] ?? DateTime.now().toIso8601String()),
        );
      }).toList();
      productWithPrices = ProductWithPrices(product: product, prices: prices);
    }
    
    return ShoppingListItem(
      id: json['id'],
      listId: json['list_id'],
      productId: json['product_id'],
      productWithPrices: productWithPrices,
      name: json['name'],
      quantity: json['quantity'] ?? 1,
      notes: json['notes'],
      isChecked: json['is_checked'] ?? false,
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'list_id': listId,
      'product_id': productId,
      'name': name,
      'quantity': quantity,
      'notes': notes,
      'is_checked': isChecked,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  ShoppingListItem copyWith({
    String? id,
    String? listId,
    String? productId,
    ProductWithPrices? productWithPrices,
    String? name,
    int? quantity,
    String? notes,
    bool? isChecked,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return ShoppingListItem(
      id: id ?? this.id,
      listId: listId ?? this.listId,
      productId: productId ?? this.productId,
      productWithPrices: productWithPrices ?? this.productWithPrices,
      name: name ?? this.name,
      quantity: quantity ?? this.quantity,
      notes: notes ?? this.notes,
      isChecked: isChecked ?? this.isChecked,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  static String generateId() => const Uuid().v4();
}