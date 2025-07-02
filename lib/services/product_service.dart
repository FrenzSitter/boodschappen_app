import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/product.dart';
import '../config/supabase_config.dart';

class ProductService {
  static final SupabaseClient _client = SupabaseConfig.client;

  static Future<List<ProductWithPrices>> searchProducts({
    required SearchFilters filters,
    int limit = 20,
    int offset = 0,
  }) async {
    try {
      // Build the query - eerst basis query
      var query = _client
          .from('products')
          .select('''
            *,
            prices!inner(
              id,
              price,
              original_price,
              price_per_unit,
              currency,
              is_available,
              is_on_sale,
              last_updated,
              supermarkets!inner(
                id,
                name,
                slug,
                color_primary
              )
            ),
            categories(
              id,
              name,
              slug
            )
          ''');

      // Apply category filter first (most specific)
      if (filters.categoryId != null) {
        query = query.eq('category_id', filters.categoryId!);
        print('🔍 Searching by category: ${filters.categoryId}');
      }

      // Apply search query filter (only if no specific category is set, or as additional filter)
      if (filters.query != null && filters.query!.isNotEmpty) {
        final searchQuery = filters.query!.trim();
        query = query.or('name.ilike.%$searchQuery%,brand.ilike.%$searchQuery%');
        print('🔍 Searching by query: $searchQuery');
      }
      
      // Apply organic filter
      if (filters.isOrganic == true) {
        query = query.eq('is_organic', true);
      }
      
      // Apply bio filter
      if (filters.isBio == true) {
        query = query.eq('is_bio', true);
      }
      
      // Apply limit and offset
      final finalQuery = query.range(offset, offset + limit - 1);
      
      final response = await finalQuery;
      
      print('🔵 DATABASE QUERY SUCCESS: Retrieved ${response.length} products from Supabase');
      
      // Convert response to ProductWithPrices objects
      final results = <ProductWithPrices>[];
      
      for (final item in response) {
        final product = Product.fromJson(item);
        final pricesData = item['prices'] as List? ?? [];
        
        final prices = pricesData.map((priceData) {
          final supermarketData = priceData['supermarkets'];
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
            lastUpdated: DateTime.parse(priceData['last_updated']),
          );
        }).toList();
        
        // Apply price range and supermarket filters on the client side
        var filteredPrices = prices;
        
        // Apply supermarket filter
        if (filters.supermarketIds != null && filters.supermarketIds!.isNotEmpty) {
          filteredPrices = filteredPrices.where((price) {
            return filters.supermarketIds!.contains(price.supermarketSlug);
          }).toList();
        }
        
        // Apply price range filters
        if (filters.minPrice != null || filters.maxPrice != null) {
          filteredPrices = filteredPrices.where((price) {
            if (filters.minPrice != null && price.price < filters.minPrice!) {
              return false;
            }
            if (filters.maxPrice != null && price.price > filters.maxPrice!) {
              return false;
            }
            return true;
          }).toList();
        }
        
        // Apply sale filter
        if (filters.isOnSale == true) {
          filteredPrices = filteredPrices.where((price) => price.isOnSale).toList();
        }
        
        if (filteredPrices.isNotEmpty) {
          results.add(ProductWithPrices(product: product, prices: filteredPrices));
        }
      }
      
      return results;
    } catch (e) {
      print('🔴 DATABASE ERROR: $e');
      print('🟡 FALLING BACK TO MOCK DATA');
      // Fallback to mock data if database fails
      return _getMockProducts().where((p) {
        if (filters.query != null && filters.query!.isNotEmpty) {
          final query = filters.query!.toLowerCase();
          return p.product.name.toLowerCase().contains(query) ||
                 (p.product.brand?.toLowerCase().contains(query) ?? false);
        }
        return true;
      }).take(limit).toList();
    }
  }

  static Future<List<Supermarket>> getSupermarkets() async {
    try {
      final response = await _client
          .from('supermarkets')
          .select('*')
          .eq('is_active', true)
          .order('name');
      
      return response.map<Supermarket>((item) => Supermarket.fromJson(item)).toList();
    } catch (e) {
      print('Error fetching supermarkets: $e');
      // Fallback to mock data
      return _getMockSupermarkets();
    }
  }

  static Future<List<Category>> getCategories() async {
    try {
      final response = await _client
          .from('categories')
          .select('*')
          .order('display_order');
      
      return response.map<Category>((item) => Category.fromJson(item)).toList();
    } catch (e) {
      print('Error fetching categories: $e');
      // Fallback to mock data
      return _getMockCategories();
    }
  }

  static Future<ProductWithPrices?> getProductById(String productId) async {
    try {
      final response = await _client
          .from('products')
          .select('''
            *,
            prices(
              id,
              price,
              original_price,
              price_per_unit,
              currency,
              is_available,
              is_on_sale,
              last_updated,
              supermarket:supermarkets(
                id,
                name,
                slug,
                color_primary
              )
            ),
            category:categories(
              id,
              name,
              slug
            )
          ''')
          .eq('id', productId)
          .single();
      
      final product = Product.fromJson(response);
      final pricesData = response['prices'] as List? ?? [];
      
      final prices = pricesData.map((priceData) {
        final supermarketData = priceData['supermarket'];
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
          lastUpdated: DateTime.parse(priceData['last_updated']),
        );
      }).toList();
      
      return ProductWithPrices(product: product, prices: prices);
    } catch (e) {
      print('Error fetching product: $e');
      return null;
    }
  }

  static Future<ProductWithPrices?> searchProductByBarcode(String barcode) async {
    try {
      final response = await _client
          .from('products')
          .select('''
            *,
            prices(
              id,
              price,
              original_price,
              price_per_unit,
              currency,
              is_available,
              is_on_sale,
              last_updated,
              supermarket:supermarkets(
                id,
                name,
                slug,
                color_primary
              )
            ),
            category:categories(
              id,
              name,
              slug
            )
          ''')
          .eq('barcode', barcode)
          .limit(1);
      
      if (response.isEmpty) return null;
      
      final item = response.first;
      final product = Product.fromJson(item);
      final pricesData = item['prices'] as List? ?? [];
      
      final prices = pricesData.map((priceData) {
        final supermarketData = priceData['supermarket'];
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
          lastUpdated: DateTime.parse(priceData['last_updated']),
        );
      }).toList();
      
      return ProductWithPrices(product: product, prices: prices);
    } catch (e) {
      print('Error searching product by barcode: $e');
      return null;
    }
  }

  static Future<List<ProductWithPrices>> getPopularProducts({int limit = 10}) async {
    try {
      final response = await _client
          .from('products')
          .select('''
            *,
            prices(
              id,
              price,
              original_price,
              price_per_unit,
              currency,
              is_available,
              is_on_sale,
              last_updated,
              supermarket:supermarkets(
                id,
                name,
                slug,
                color_primary
              )
            ),
            category:categories(
              id,
              name,
              slug
            )
          ''')
          .limit(limit);
      
      final results = <ProductWithPrices>[];
      
      for (final item in response) {
        final product = Product.fromJson(item);
        final pricesData = item['prices'] as List? ?? [];
        
        final prices = pricesData.map((priceData) {
          final supermarketData = priceData['supermarket'];
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
            lastUpdated: DateTime.parse(priceData['last_updated']),
          );
        }).toList();
        
        if (prices.isNotEmpty) {
          results.add(ProductWithPrices(product: product, prices: prices));
        }
      }
      
      return results;
    } catch (e) {
      print('Error fetching popular products: $e');
      // Fallback to mock data
      return _getMockProducts().take(limit).toList();
    }
  }

  // Mock data methods
  static List<ProductWithPrices> _getMockProducts() {
    return [
      // Zuivel & eieren
      ProductWithPrices(
        product: Product(
          id: '1',
          name: 'Melk halfvol 1 liter',
          brand: 'AH Basic',
          categoryName: 'Zuivel & eieren',
          barcode: '8718906115892',
          unitType: 'liter',
          isOrganic: false,
          isBio: false,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
        prices: [
          ProductPrice(
            id: '1',
            productId: '1',
            supermarketId: 'albert-heijn',
            supermarketName: 'Albert Heijn',
            supermarketSlug: 'albert-heijn',
            price: 1.19,
            pricePerUnit: 1.19,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '2',
            productId: '1',
            supermarketId: 'jumbo',
            supermarketName: 'Jumbo',
            supermarketSlug: 'jumbo',
            price: 1.15,
            pricePerUnit: 1.15,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '3',
            productId: '1',
            supermarketId: 'lidl',
            supermarketName: 'Lidl',
            supermarketSlug: 'lidl',
            price: 0.89,
            pricePerUnit: 0.89,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: true,
            lastUpdated: DateTime.now(),
          ),
        ],
      ),
      
      ProductWithPrices(
        product: Product(
          id: '4',
          name: 'Eieren vrije uitloop 12 stuks',
          brand: 'AH',
          categoryName: 'Zuivel & eieren',
          barcode: '8718906142465',
          unitType: 'piece',
          isOrganic: false,
          isBio: false,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
        prices: [
          ProductPrice(
            id: '8',
            productId: '4',
            supermarketId: 'albert-heijn',
            supermarketName: 'Albert Heijn',
            supermarketSlug: 'albert-heijn',
            price: 2.89,
            pricePerUnit: 0.24,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '9',
            productId: '4',
            supermarketId: 'jumbo',
            supermarketName: 'Jumbo',
            supermarketSlug: 'jumbo',
            price: 2.79,
            pricePerUnit: 0.23,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
        ],
      ),
      
      ProductWithPrices(
        product: Product(
          id: '5',
          name: 'Yoghurt naturel 500ml',
          brand: 'Campina',
          categoryName: 'Zuivel & eieren',
          barcode: '8712566447640',
          unitType: 'piece',
          isOrganic: false,
          isBio: false,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
        prices: [
          ProductPrice(
            id: '10',
            productId: '5',
            supermarketId: 'albert-heijn',
            supermarketName: 'Albert Heijn',
            supermarketSlug: 'albert-heijn',
            price: 1.49,
            pricePerUnit: 2.98,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '11',
            productId: '5',
            supermarketId: 'lidl',
            supermarketName: 'Lidl',
            supermarketSlug: 'lidl',
            price: 1.29,
            pricePerUnit: 2.58,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: true,
            lastUpdated: DateTime.now(),
          ),
        ],
      ),
      
      // Groente & fruit
      ProductWithPrices(
        product: Product(
          id: '2',
          name: 'Bananen',
          brand: 'Chiquita',
          categoryName: 'Groente & fruit',
          barcode: null,
          unitType: 'kg',
          isOrganic: false,
          isBio: false,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
        prices: [
          ProductPrice(
            id: '4',
            productId: '2',
            supermarketId: 'albert-heijn',
            supermarketName: 'Albert Heijn',
            supermarketSlug: 'albert-heijn',
            price: 1.99,
            pricePerUnit: 1.99,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '5',
            productId: '2',
            supermarketId: 'jumbo',
            supermarketName: 'Jumbo',
            supermarketSlug: 'jumbo',
            price: 1.89,
            pricePerUnit: 1.89,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '12',
            productId: '2',
            supermarketId: 'lidl',
            supermarketName: 'Lidl',
            supermarketSlug: 'lidl',
            price: 1.49,
            pricePerUnit: 1.49,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: true,
            lastUpdated: DateTime.now(),
          ),
        ],
      ),
      
      ProductWithPrices(
        product: Product(
          id: '6',
          name: 'Tomaten cherry 250g',
          brand: 'AH',
          categoryName: 'Groente & fruit',
          barcode: '8718906521087',
          unitType: 'piece',
          isOrganic: false,
          isBio: false,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
        prices: [
          ProductPrice(
            id: '13',
            productId: '6',
            supermarketId: 'albert-heijn',
            supermarketName: 'Albert Heijn',
            supermarketSlug: 'albert-heijn',
            price: 1.79,
            pricePerUnit: 7.16,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '14',
            productId: '6',
            supermarketId: 'jumbo',
            supermarketName: 'Jumbo',
            supermarketSlug: 'jumbo',
            price: 1.69,
            pricePerUnit: 6.76,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
        ],
      ),
      
      // Dranken
      ProductWithPrices(
        product: Product(
          id: '3',
          name: 'Coca Cola 1.5L',
          brand: 'Coca-Cola',
          categoryName: 'Dranken',
          barcode: '5449000000996',
          unitType: 'liter',
          isOrganic: false,
          isBio: false,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
        prices: [
          ProductPrice(
            id: '6',
            productId: '3',
            supermarketId: 'albert-heijn',
            supermarketName: 'Albert Heijn',
            supermarketSlug: 'albert-heijn',
            price: 2.19,
            originalPrice: 2.49,
            pricePerUnit: 1.46,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: true,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '7',
            productId: '3',
            supermarketId: 'lidl',
            supermarketName: 'Lidl',
            supermarketSlug: 'lidl',
            price: 1.79,
            pricePerUnit: 1.19,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '15',
            productId: '3',
            supermarketId: 'jumbo',
            supermarketName: 'Jumbo',
            supermarketSlug: 'jumbo',
            price: 1.99,
            pricePerUnit: 1.33,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
        ],
      ),
      
      ProductWithPrices(
        product: Product(
          id: '7',
          name: 'Koffie gemalen 500g',
          brand: 'Douwe Egberts',
          categoryName: 'Dranken',
          barcode: '8711000536636',
          unitType: 'piece',
          isOrganic: false,
          isBio: false,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
        prices: [
          ProductPrice(
            id: '16',
            productId: '7',
            supermarketId: 'albert-heijn',
            supermarketName: 'Albert Heijn',
            supermarketSlug: 'albert-heijn',
            price: 4.49,
            pricePerUnit: 8.98,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '17',
            productId: '7',
            supermarketId: 'jumbo',
            supermarketName: 'Jumbo',
            supermarketSlug: 'jumbo',
            price: 4.29,
            pricePerUnit: 8.58,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: true,
            lastUpdated: DateTime.now(),
          ),
        ],
      ),
      
      // Brood & gebak
      ProductWithPrices(
        product: Product(
          id: '8',
          name: 'Brood wit heel 800g',
          brand: 'AH Basic',
          categoryName: 'Brood & gebak',
          barcode: '8718906176447',
          unitType: 'piece',
          isOrganic: false,
          isBio: false,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
        prices: [
          ProductPrice(
            id: '18',
            productId: '8',
            supermarketId: 'albert-heijn',
            supermarketName: 'Albert Heijn',
            supermarketSlug: 'albert-heijn',
            price: 1.09,
            pricePerUnit: 1.36,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '19',
            productId: '8',
            supermarketId: 'jumbo',
            supermarketName: 'Jumbo',
            supermarketSlug: 'jumbo',
            price: 0.99,
            pricePerUnit: 1.24,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
        ],
      ),
      
      ProductWithPrices(
        product: Product(
          id: '11',
          name: 'Bruin brood volkoren 800g',
          brand: 'AH',
          categoryName: 'Brood & gebak',
          barcode: '8718906234567',
          unitType: 'piece',
          isOrganic: false,
          isBio: false,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
        prices: [
          ProductPrice(
            id: '24',
            productId: '11',
            supermarketId: 'albert-heijn',
            supermarketName: 'Albert Heijn',
            supermarketSlug: 'albert-heijn',
            price: 1.29,
            pricePerUnit: 1.61,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '25',
            productId: '11',
            supermarketId: 'jumbo',
            supermarketName: 'Jumbo',
            supermarketSlug: 'jumbo',
            price: 1.19,
            pricePerUnit: 1.49,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '26',
            productId: '11',
            supermarketId: 'lidl',
            supermarketName: 'Lidl',
            supermarketSlug: 'lidl',
            price: 1.09,
            pricePerUnit: 1.36,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: true,
            lastUpdated: DateTime.now(),
          ),
        ],
      ),
      
      ProductWithPrices(
        product: Product(
          id: '12',
          name: 'Volkoren brood 800g',
          brand: 'Hovis',
          categoryName: 'Brood & gebak',
          barcode: '8712345678901',
          unitType: 'piece',
          isOrganic: true,
          isBio: true,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
        prices: [
          ProductPrice(
            id: '27',
            productId: '12',
            supermarketId: 'albert-heijn',
            supermarketName: 'Albert Heijn',
            supermarketSlug: 'albert-heijn',
            price: 2.19,
            pricePerUnit: 2.74,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '28',
            productId: '12',
            supermarketId: 'jumbo',
            supermarketName: 'Jumbo',
            supermarketSlug: 'jumbo',
            price: 1.99,
            pricePerUnit: 2.49,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: true,
            lastUpdated: DateTime.now(),
          ),
        ],
      ),
      
      ProductWithPrices(
        product: Product(
          id: '9',
          name: 'Croissants 6 stuks',
          brand: 'AH',
          categoryName: 'Brood & gebak',
          barcode: '8718906332447',
          unitType: 'piece',
          isOrganic: false,
          isBio: false,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
        prices: [
          ProductPrice(
            id: '20',
            productId: '9',
            supermarketId: 'albert-heijn',
            supermarketName: 'Albert Heijn',
            supermarketSlug: 'albert-heijn',
            price: 1.89,
            pricePerUnit: 0.32,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '21',
            productId: '9',
            supermarketId: 'lidl',
            supermarketName: 'Lidl',
            supermarketSlug: 'lidl',
            price: 1.49,
            pricePerUnit: 0.25,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: true,
            lastUpdated: DateTime.now(),
          ),
        ],
      ),
      
      // Biologische producten
      ProductWithPrices(
        product: Product(
          id: '10',
          name: 'Biologische melk 1L',
          brand: 'AH Biologisch',
          categoryName: 'Zuivel & eieren',
          barcode: '8718906998877',
          unitType: 'liter',
          isOrganic: true,
          isBio: true,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
        prices: [
          ProductPrice(
            id: '22',
            productId: '10',
            supermarketId: 'albert-heijn',
            supermarketName: 'Albert Heijn',
            supermarketSlug: 'albert-heijn',
            price: 1.89,
            pricePerUnit: 1.89,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '23',
            productId: '10',
            supermarketId: 'jumbo',
            supermarketName: 'Jumbo',
            supermarketSlug: 'jumbo',
            price: 1.79,
            pricePerUnit: 1.79,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: true,
            lastUpdated: DateTime.now(),
          ),
        ],
      ),
      
      // Extra producten voor betere zoekresultaten
      ProductWithPrices(
        product: Product(
          id: '13',
          name: 'Appels Elstar 1kg',
          brand: null,
          categoryName: 'Groente & fruit',
          barcode: null,
          unitType: 'kg',
          isOrganic: false,
          isBio: false,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
        prices: [
          ProductPrice(
            id: '29',
            productId: '13',
            supermarketId: 'albert-heijn',
            supermarketName: 'Albert Heijn',
            supermarketSlug: 'albert-heijn',
            price: 2.49,
            pricePerUnit: 2.49,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '30',
            productId: '13',
            supermarketId: 'jumbo',
            supermarketName: 'Jumbo',
            supermarketSlug: 'jumbo',
            price: 2.29,
            pricePerUnit: 2.29,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: true,
            lastUpdated: DateTime.now(),
          ),
        ],
      ),
      
      ProductWithPrices(
        product: Product(
          id: '14',
          name: 'Kaas jong belegen plakken 150g',
          brand: 'AH',
          categoryName: 'Zuivel & eieren',
          barcode: '8718906445567',
          unitType: 'piece',
          isOrganic: false,
          isBio: false,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
        prices: [
          ProductPrice(
            id: '31',
            productId: '14',
            supermarketId: 'albert-heijn',
            supermarketName: 'Albert Heijn',
            supermarketSlug: 'albert-heijn',
            price: 2.99,
            pricePerUnit: 19.93,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: false,
            lastUpdated: DateTime.now(),
          ),
          ProductPrice(
            id: '32',
            productId: '14',
            supermarketId: 'lidl',
            supermarketName: 'Lidl',
            supermarketSlug: 'lidl',
            price: 2.49,
            pricePerUnit: 16.60,
            currency: 'EUR',
            isAvailable: true,
            isOnSale: true,
            lastUpdated: DateTime.now(),
          ),
        ],
      ),
    ];
  }

  static List<Supermarket> _getMockSupermarkets() {
    return [
      Supermarket(
        id: '1',
        name: 'Albert Heijn',
        slug: 'albert-heijn',
        colorPrimary: '#0051A5',
        isActive: true,
      ),
      Supermarket(
        id: '2',
        name: 'Jumbo',
        slug: 'jumbo',
        colorPrimary: '#FFD800',
        isActive: true,
      ),
      Supermarket(
        id: '3',
        name: 'Lidl',
        slug: 'lidl',
        colorPrimary: '#0050AA',
        isActive: true,
      ),
      Supermarket(
        id: '4',
        name: 'Aldi',
        slug: 'aldi',
        colorPrimary: '#009CDA',
        isActive: true,
      ),
      Supermarket(
        id: '5',
        name: 'Plus',
        slug: 'plus',
        colorPrimary: '#E30613',
        isActive: true,
      ),
      Supermarket(
        id: '6',
        name: 'COOP',
        slug: 'coop',
        colorPrimary: '#E30613',
        isActive: true,
      ),
    ];
  }

  static List<Category> _getMockCategories() {
    return [
      Category(
        id: '1',
        name: 'Verse producten',
        slug: 'fresh-products',
        iconName: 'local_florist',
        displayOrder: 1,
      ),
      Category(
        id: '2',
        name: 'Vlees, vis & vegetarisch',
        slug: 'meat-fish-vegetarian',
        iconName: 'set_meal',
        displayOrder: 2,
      ),
      Category(
        id: '3',
        name: 'Zuivel & eieren',
        slug: 'dairy-eggs',
        iconName: 'egg',
        displayOrder: 3,
      ),
      Category(
        id: '4',
        name: 'Brood & gebak',
        slug: 'bread-bakery',
        iconName: 'bakery_dining',
        displayOrder: 4,
      ),
      Category(
        id: '5',
        name: 'Groente & fruit',
        slug: 'vegetables-fruit',
        iconName: 'eco',
        displayOrder: 5,
      ),
      Category(
        id: '6',
        name: 'Dranken',
        slug: 'drinks',
        iconName: 'local_drink',
        displayOrder: 8,
      ),
      Category(
        id: '7',
        name: 'Diepvries',
        slug: 'frozen',
        iconName: 'ac_unit',
        displayOrder: 6,
      ),
      Category(
        id: '8',
        name: 'Houdbaar',
        slug: 'shelf-stable',
        iconName: 'inventory_2',
        displayOrder: 7,
      ),
    ];
  }
}