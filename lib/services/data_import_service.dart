import 'package:supabase_flutter/supabase_flutter.dart';
import '../config/supabase_config.dart';
import '../models/product.dart';
import 'checkjebon_service.dart';

class DataImportService {
  static final SupabaseClient _client = SupabaseConfig.client;
  
  /// Import products from checkjebon.nl into Supabase
  static Future<int> importProductsFromCheckjebon() async {
    try {
      print('🔄 Starting import from checkjebon.nl...');
      
      // Fetch products from checkjebon.nl
      final checkjebonProducts = await CheckjebonService.fetchProducts();
      print('📦 Fetched ${checkjebonProducts.length} products from checkjebon.nl');
      
      // Get categories and supermarkets from database
      final categories = await _getCategories();
      final supermarkets = await _getSupermarkets();
      
      // Find Albert Heijn supermarket (since checkjebon.nl data appears to be from AH)
      final albertHeijn = supermarkets.firstWhere(
        (s) => s.slug == 'albert-heijn',
        orElse: () => throw Exception('Albert Heijn not found in database'),
      );
      
      int importedCount = 0;
      final batchSize = 100; // Process in batches to avoid memory issues
      
      // Process products in batches
      for (int i = 0; i < checkjebonProducts.length; i += batchSize) {
        final batch = checkjebonProducts.skip(i).take(batchSize).toList();
        
        final List<Map<String, dynamic>> productsToInsert = [];
        final List<Map<String, dynamic>> pricesToInsert = [];
        
        for (final checkjebonProduct in batch) {
          try {
            // Determine category for this product
            final categoryName = _inferCategory(checkjebonProduct.name);
            final category = categories.firstWhere(
              (c) => c.name == categoryName,
              orElse: () => categories.firstWhere((c) => c.name == 'Houdbaar'),
            );
            
            // Convert to our Product model
            final product = CheckjebonService.convertToProduct(checkjebonProduct, category.id);
            
            // Check if product already exists
            final existingProduct = await _getProductByName(product.name);
            
            String productId;
            if (existingProduct == null) {
              // Prepare product for insertion
              final productData = {
                'id': product.id,
                'name': product.name,
                'brand': product.brand,
                'category_id': product.categoryId,
                'barcode': product.barcode,
                'image_url': product.imageUrl,
                'unit_type': product.unitType,
                'package_size': product.packageSize,
                'package_unit': product.packageUnit,
                'description': product.description,
                'is_organic': product.isOrganic,
                'is_bio': product.isBio,
                'created_at': DateTime.now().toIso8601String(),
                'updated_at': DateTime.now().toIso8601String(),
              };
              
              productsToInsert.add(productData);
              productId = product.id;
            } else {
              productId = existingProduct['id'];
            }
            
            // Convert to ProductPrice for Albert Heijn
            final productPrice = CheckjebonService.convertToProductPrice(checkjebonProduct, productId);
            
            // Check if price already exists
            final existingPrice = await _getProductPrice(productId, albertHeijn.id);
            
            if (existingPrice == null) {
              // Prepare price for insertion
              final priceData = {
                'id': productPrice.id,
                'product_id': productPrice.productId,
                'supermarket_id': albertHeijn.id,
                'price': productPrice.price,
                'original_price': productPrice.originalPrice,
                'price_per_unit': productPrice.pricePerUnit,
                'currency': productPrice.currency,
                'is_available': productPrice.isAvailable,
                'is_on_sale': productPrice.isOnSale,
                'last_updated': DateTime.now().toIso8601String(),
                'created_at': DateTime.now().toIso8601String(),
              };
              
              pricesToInsert.add(priceData);
            } else {
              // Update existing price
              await _client
                  .from('product_prices')
                  .update({
                    'price': productPrice.price,
                    'last_updated': DateTime.now().toIso8601String(),
                  })
                  .eq('id', existingPrice['id']);
            }
            
          } catch (e) {
            print('❌ Error processing product ${checkjebonProduct.name}: $e');
            continue;
          }
        }
        
        // Insert products batch
        if (productsToInsert.isNotEmpty) {
          try {
            await _client
                .from('products')
                .insert(productsToInsert);
            print('✅ Inserted ${productsToInsert.length} products');
          } catch (e) {
            print('❌ Error inserting products batch: $e');
          }
        }
        
        // Insert prices batch
        if (pricesToInsert.isNotEmpty) {
          try {
            await _client
                .from('product_prices')
                .insert(pricesToInsert);
            print('✅ Inserted ${pricesToInsert.length} prices');
          } catch (e) {
            print('❌ Error inserting prices batch: $e');
          }
        }
        
        importedCount += batch.length;
        print('📊 Processed ${importedCount}/${checkjebonProducts.length} products');
      }
      
      print('🎉 Import completed! Processed $importedCount products');
      return importedCount;
      
    } catch (e) {
      print('❌ Error during import: $e');
      rethrow;
    }
  }
  
  /// Initialize database with supermarkets and categories
  static Future<void> initializeDatabase() async {
    try {
      print('🔄 Initializing database...');
      
      // Check if supermarkets exist
      final supermarkets = await _client
          .from('supermarkets')
          .select('count');
      
      if (supermarkets.isEmpty) {
        print('📦 Seeding supermarkets...');
        await _seedSupermarkets();
      }
      
      // Check if categories exist
      final categories = await _client
          .from('categories')
          .select('count');
      
      if (categories.isEmpty) {
        print('📦 Seeding categories...');
        await _seedCategories();
      }
      
      print('✅ Database initialized successfully');
    } catch (e) {
      print('❌ Error initializing database: $e');
      rethrow;
    }
  }
  
  /// Get all categories from database
  static Future<List<Category>> _getCategories() async {
    try {
      final response = await _client
          .from('categories')
          .select('*')
          .order('display_order');
      
      return response.map<Category>((item) => Category.fromJson(item)).toList();
    } catch (e) {
      print('Error fetching categories: $e');
      return [];
    }
  }
  
  /// Get all supermarkets from database
  static Future<List<Supermarket>> _getSupermarkets() async {
    try {
      final response = await _client
          .from('supermarkets')
          .select('*')
          .eq('is_active', true)
          .order('name');
      
      return response.map<Supermarket>((item) => Supermarket.fromJson(item)).toList();
    } catch (e) {
      print('Error fetching supermarkets: $e');
      return [];
    }
  }
  
  /// Check if product exists by name
  static Future<Map<String, dynamic>?> _getProductByName(String name) async {
    try {
      final response = await _client
          .from('products')
          .select('id, name')
          .eq('name', name)
          .limit(1);
      
      return response.isNotEmpty ? response.first : null;
    } catch (e) {
      return null;
    }
  }
  
  /// Check if product price exists
  static Future<Map<String, dynamic>?> _getProductPrice(String productId, String supermarketId) async {
    try {
      final response = await _client
          .from('product_prices')
          .select('id, price')
          .eq('product_id', productId)
          .eq('supermarket_id', supermarketId)
          .limit(1);
      
      return response.isNotEmpty ? response.first : null;
    } catch (e) {
      return null;
    }
  }
  
  /// Seed supermarkets data
  static Future<void> _seedSupermarkets() async {
    final supermarkets = [
      {
        'name': 'Albert Heijn',
        'slug': 'albert-heijn',
        'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Albert_Heijn_Logo.svg/1200px-Albert_Heijn_Logo.svg.png',
        'website_url': 'https://www.ah.nl',
        'color_primary': '#0051A5',
        'color_secondary': '#FFFFFF',
        'is_active': true,
      },
      {
        'name': 'Jumbo',
        'slug': 'jumbo',
        'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Jumbo_Logo.svg/1200px-Jumbo_Logo.svg.png',
        'website_url': 'https://www.jumbo.com',
        'color_primary': '#FFD800',
        'color_secondary': '#000000',
        'is_active': true,
      },
      {
        'name': 'Lidl',
        'slug': 'lidl',
        'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Lidl-Logo.svg/1200px-Lidl-Logo.svg.png',
        'website_url': 'https://www.lidl.nl',
        'color_primary': '#0050AA',
        'color_secondary': '#FFED00',
        'is_active': true,
      },
      {
        'name': 'Aldi',
        'slug': 'aldi',
        'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Aldi_Nord_Logo.svg/1200px-Aldi_Nord_Logo.svg.png',
        'website_url': 'https://www.aldi.nl',
        'color_primary': '#009CDA',
        'color_secondary': '#FFFFFF',
        'is_active': true,
      },
      {
        'name': 'Plus',
        'slug': 'plus',
        'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c6/Plus_logo.svg/1200px-Plus_logo.svg.png',
        'website_url': 'https://www.plus.nl',
        'color_primary': '#E30613',
        'color_secondary': '#FFFFFF',
        'is_active': true,
      },
    ];
    
    await _client.from('supermarkets').insert(supermarkets);
  }
  
  /// Seed categories data
  static Future<void> _seedCategories() async {
    final categories = [
      {
        'id': '33333333-3333-3333-3333-333333333333',
        'name': 'Alle producten',
        'slug': 'alle-producten',
        'parent_id': null,
        'icon_name': 'shopping_cart',
        'display_order': 0,
      },
      {
        'name': 'Verse producten',
        'slug': 'verse-producten',
        'parent_id': null,
        'icon_name': 'local_florist',
        'display_order': 1,
      },
      {
        'name': 'Vlees, vis & vegetarisch',
        'slug': 'vlees-vis-vegetarisch',
        'parent_id': null,
        'icon_name': 'set_meal',
        'display_order': 2,
      },
      {
        'name': 'Zuivel & eieren',
        'slug': 'zuivel-eieren',
        'parent_id': null,
        'icon_name': 'egg',
        'display_order': 3,
      },
      {
        'name': 'Brood & gebak',
        'slug': 'brood-gebak',
        'parent_id': null,
        'icon_name': 'bakery_dining',
        'display_order': 4,
      },
      {
        'name': 'Groente & fruit',
        'slug': 'groente-fruit',
        'parent_id': null,
        'icon_name': 'eco',
        'display_order': 5,
      },
      {
        'name': 'Dranken',
        'slug': 'dranken',
        'parent_id': null,
        'icon_name': 'local_drink',
        'display_order': 6,
      },
      {
        'name': 'Houdbaar',
        'slug': 'houdbaar',
        'parent_id': null,
        'icon_name': 'inventory_2',
        'display_order': 7,
      },
    ];
    
    await _client.from('categories').insert(categories);
  }
  
  /// Clear all product data (for testing purposes)
  static Future<void> clearProductData() async {
    try {
      print('🗑️ Clearing product data...');
      
      await _client.from('product_prices').delete().neq('id', '00000000-0000-0000-0000-000000000000');
      await _client.from('products').delete().neq('id', '00000000-0000-0000-0000-000000000000');
      
      print('✅ Product data cleared');
    } catch (e) {
      print('❌ Error clearing product data: $e');
      rethrow;
    }
  }
  
  /// Infer category from product name
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
}