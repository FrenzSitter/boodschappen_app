import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:supabase_flutter/supabase_flutter.dart';
import '../config/supabase_config.dart';
import '../models/product.dart';

class CompleteDataImportService {
  static final SupabaseClient _client = SupabaseConfig.client;
  static const String _dataUrl = 'https://raw.githubusercontent.com/supermarkt/checkjebon/refs/heads/main/data/supermarkets.json';
  
  /// Import the complete checkjebon dataset
  static Future<ImportResult> importCompleteDataset() async {
    try {
      print('🔄 Starting complete dataset import from checkjebon.nl...');
      
      // Clear existing data first
      await _clearExistingData();
      
      // Ensure supermarkets and categories exist
      await _ensureBaseDataExists();
      
      // Fetch the complete dataset
      final dataset = await _fetchCompleteDataset();
      print('📦 Fetched ${dataset.length} product groups from checkjebon.nl');
      
      // Process and import data
      final result = await _processAndImportData(dataset);
      
      print('🎉 Complete dataset import finished!');
      return result;
      
    } catch (e) {
      print('❌ Error during complete dataset import: $e');
      rethrow;
    }
  }
  
  /// Fetch the complete dataset from GitHub
  static Future<List<dynamic>> _fetchCompleteDataset() async {
    try {
      print('📡 Fetching complete dataset from GitHub...');
      
      final response = await http.get(
        Uri.parse(_dataUrl),
        headers: {'Accept': 'application/json'},
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> jsonData = json.decode(response.body);
        return jsonData;
      } else {
        throw Exception('Failed to fetch dataset: ${response.statusCode}');
      }
    } catch (e) {
      print('❌ Error fetching dataset: $e');
      rethrow;
    }
  }
  
  /// Process and import the dataset into Supabase
  static Future<ImportResult> _processAndImportData(List<dynamic> dataset) async {
    int totalProducts = 0;
    int totalPrices = 0;
    int processedGroups = 0;
    
    // Get Albert Heijn supermarket ID
    final albertHeijn = await _getOrCreateSupermarket('Albert Heijn', 'albert-heijn');
    final categories = await _getCategories();
    
    const batchSize = 50; // Process in smaller batches for better performance
    
    for (int i = 0; i < dataset.length; i += batchSize) {
      final batch = dataset.skip(i).take(batchSize).toList();
      
      final List<Map<String, dynamic>> productsToInsert = [];
      final List<Map<String, dynamic>> pricesToInsert = [];
      
      for (final productGroup in batch) {
        try {
          final products = await _processProductGroup(productGroup, albertHeijn.id, categories);
          
          for (final productData in products) {
            // Check if product already exists
            final existingProduct = await _getProductByName(productData['product']['name']);
            
            String productId;
            if (existingProduct == null) {
              productsToInsert.add(productData['product']);
              productId = productData['product']['id'];
              totalProducts++;
            } else {
              productId = existingProduct['id'];
            }
            
            // Add price data
            final priceData = productData['price'];
            priceData['product_id'] = productId;
            pricesToInsert.add(priceData);
            totalPrices++;
          }
          
          processedGroups++;
        } catch (e) {
          print('❌ Error processing product group: $e');
          continue;
        }
      }
      
      // Bulk insert products
      if (productsToInsert.isNotEmpty) {
        try {
          await _client.from('products').insert(productsToInsert);
          print('✅ Inserted ${productsToInsert.length} products (batch ${(i ~/ batchSize) + 1})');
        } catch (e) {
          print('❌ Error inserting products batch: $e');
        }
      }
      
      // Bulk insert prices
      if (pricesToInsert.isNotEmpty) {
        try {
          await _client.from('product_prices').insert(pricesToInsert);
          print('✅ Inserted ${pricesToInsert.length} prices (batch ${(i ~/ batchSize) + 1})');
        } catch (e) {
          print('❌ Error inserting prices batch: $e');
        }
      }
      
      print('📊 Progress: ${processedGroups}/${dataset.length} groups processed');
    }
    
    return ImportResult(
      totalProducts: totalProducts,
      totalPrices: totalPrices,
      processedGroups: processedGroups,
    );
  }
  
  /// Process a single product group from the dataset
  static Future<List<Map<String, dynamic>>> _processProductGroup(
    Map<String, dynamic> productGroup,
    String supermarketId,
    List<Category> categories,
  ) async {
    final List<Map<String, dynamic>> results = [];
    
    final mainProductName = productGroup['n'] as String? ?? '';
    final variants = productGroup['d'] as List<dynamic>? ?? [];
    
    // Process each variant as a separate product
    for (final variant in variants) {
      try {
        final variantName = variant['n'] as String? ?? '';
        final link = variant['l'] as String? ?? '';
        final price = (variant['p'] as num?)?.toDouble() ?? 0.0;
        final size = variant['s'] as String? ?? '';
        
        // Create full product name combining main name and variant
        final fullProductName = _createFullProductName(mainProductName, variantName);
        
        // Determine category
        final categoryName = _inferCategory(fullProductName);
        final category = categories.firstWhere(
          (c) => c.name == categoryName,
          orElse: () => categories.firstWhere((c) => c.name == 'Houdbaar'),
        );
        
        // Extract brand
        final brand = _extractBrand(fullProductName);
        
        // Generate unique product ID
        final productId = _generateProductId(link, fullProductName);
        
        // Create product data
        final productData = {
          'id': productId,
          'name': fullProductName,
          'brand': brand,
          'category_id': category.id,
          'barcode': null, // checkjebon doesn't provide barcodes
          'image_url': null, // checkjebon doesn't provide images
          'unit_type': _extractUnitType(size),
          'package_size': _extractPackageSize(size),
          'package_unit': _extractPackageUnit(size),
          'description': size,
          'is_organic': _isOrganic(fullProductName),
          'is_bio': _isBio(fullProductName),
          'created_at': DateTime.now().toIso8601String(),
          'updated_at': DateTime.now().toIso8601String(),
        };
        
        // Create price data
        final priceData = {
          'id': '${productId}_ah',
          'supermarket_id': supermarketId,
          'price': price,
          'original_price': null,
          'price_per_unit': _calculatePricePerUnit(price, size),
          'currency': 'EUR',
          'is_available': true,
          'is_on_sale': false,
          'last_updated': DateTime.now().toIso8601String(),
          'created_at': DateTime.now().toIso8601String(),
        };
        
        results.add({
          'product': productData,
          'price': priceData,
        });
        
      } catch (e) {
        print('❌ Error processing variant: $e');
        continue;
      }
    }
    
    return results;
  }
  
  /// Create full product name from main name and variant
  static String _createFullProductName(String mainName, String variantName) {
    if (variantName.isEmpty) return mainName;
    if (mainName.isEmpty) return variantName;
    
    // Check if variant name already contains the main name
    if (variantName.toLowerCase().contains(mainName.toLowerCase())) {
      return variantName;
    }
    
    return '$mainName - $variantName';
  }
  
  /// Generate unique product ID
  static String _generateProductId(String link, String productName) {
    if (link.isNotEmpty) {
      return link;
    }
    
    // Generate ID from product name hash
    return 'product_${productName.hashCode.abs()}';
  }
  
  /// Calculate price per unit
  static double? _calculatePricePerUnit(double price, String size) {
    // Try to extract numeric value from size
    final regex = RegExp(r'(\d+(?:\.\d+)?)');
    final match = regex.firstMatch(size);
    
    if (match != null) {
      final sizeValue = double.tryParse(match.group(1)!);
      if (sizeValue != null && sizeValue > 0) {
        return price / sizeValue;
      }
    }
    
    return price; // Default to product price if can't calculate per unit
  }
  
  /// Clear all product data (public method)
  static Future<void> clearProductData() async {
    await _clearExistingData();
  }
  
  /// Clear existing product and price data
  static Future<void> _clearExistingData() async {
    try {
      print('🗑️ Clearing existing product data...');
      
      // Check if tables exist first
      try {
        // Delete all product prices first (due to foreign key constraints)
        await _client.from('product_prices').delete().neq('id', '00000000-0000-0000-0000-000000000000');
        
        // Delete all products
        await _client.from('products').delete().neq('id', '00000000-0000-0000-0000-000000000000');
        
        print('✅ Existing data cleared');
      } catch (e) {
        // If tables don't exist, that's fine - we'll create them later
        print('ℹ️ Tables may not exist yet, skipping data clearing');
      }
    } catch (e) {
      print('❌ Error clearing existing data: $e');
      // Don't rethrow - we can continue even if clearing fails
    }
  }
  
  /// Ensure base data (supermarkets and categories) exists
  static Future<void> _ensureBaseDataExists() async {
    try {
      print('🔧 Ensuring base data exists...');
      
      // Check if categories exist
      final categories = await _client.from('categories').select('id').limit(1);
      if (categories.isEmpty) {
        await _seedCategories();
      }
      
      // Check if supermarkets exist
      final supermarkets = await _client.from('supermarkets').select('id').limit(1);
      if (supermarkets.isEmpty) {
        await _seedSupermarkets();
      }
      
      print('✅ Base data ready');
    } catch (e) {
      print('❌ Error ensuring base data: $e');
      rethrow;
    }
  }
  
  /// Get or create supermarket
  static Future<Supermarket> _getOrCreateSupermarket(String name, String slug) async {
    try {
      final existing = await _client
          .from('supermarkets')
          .select('*')
          .eq('slug', slug)
          .limit(1);
      
      if (existing.isNotEmpty) {
        return Supermarket.fromJson(existing.first);
      }
      
      // Create new supermarket
      final supermarketData = {
        'name': name,
        'slug': slug,
        'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Albert_Heijn_Logo.svg/1200px-Albert_Heijn_Logo.svg.png',
        'website_url': 'https://www.ah.nl',
        'color_primary': '#0051A5',
        'color_secondary': '#FFFFFF',
        'is_active': true,
      };
      
      final result = await _client
          .from('supermarkets')
          .insert(supermarketData)
          .select()
          .single();
      
      return Supermarket.fromJson(result);
    } catch (e) {
      print('❌ Error getting/creating supermarket: $e');
      rethrow;
    }
  }
  
  /// Get all categories
  static Future<List<Category>> _getCategories() async {
    try {
      final response = await _client
          .from('categories')
          .select('*')
          .order('display_order');
      
      return response.map<Category>((item) => Category.fromJson(item)).toList();
    } catch (e) {
      print('❌ Error fetching categories: $e');
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
  
  /// Extract brand from product name
  static String? _extractBrand(String productName) {
    final lowerName = productName.toLowerCase();
    
    // Common Dutch brands and store brands
    if (lowerName.contains('ah ') || lowerName.contains('albert heijn')) return 'AH';
    if (lowerName.contains('campina')) return 'Campina';
    if (lowerName.contains('douwe egberts')) return 'Douwe Egberts';
    if (lowerName.contains('coca cola') || lowerName.contains('coca-cola')) return 'Coca-Cola';
    if (lowerName.contains('heineken')) return 'Heineken';
    if (lowerName.contains('unilever')) return 'Unilever';
    if (lowerName.contains('nestlé') || lowerName.contains('nestle')) return 'Nestlé';
    if (lowerName.contains('danone')) return 'Danone';
    if (lowerName.contains('friesche vlag')) return 'Friesche Vlag';
    if (lowerName.contains('verkade')) return 'Verkade';
    if (lowerName.contains('liga')) return 'Liga';
    if (lowerName.contains('calvé')) return 'Calvé';
    if (lowerName.contains('knorr')) return 'Knorr';
    if (lowerName.contains('maggi')) return 'Maggi';
    if (lowerName.contains('hero')) return 'Hero';
    
    return null;
  }
  
  /// Infer category from product name
  static String _inferCategory(String productName) {
    final lowerName = productName.toLowerCase();
    
    // Dairy & Eggs
    if (lowerName.contains('melk') || lowerName.contains('yoghurt') || 
        lowerName.contains('kaas') || lowerName.contains('boter') ||
        lowerName.contains('ei') || lowerName.contains('eieren') ||
        lowerName.contains('kwark') || lowerName.contains('room')) {
      return 'Zuivel & eieren';
    }
    
    // Bread & Bakery
    if (lowerName.contains('brood') || lowerName.contains('stokbrood') ||
        lowerName.contains('croissant') || lowerName.contains('beschuit') ||
        lowerName.contains('cake') || lowerName.contains('koek')) {
      return 'Brood & gebak';
    }
    
    // Fruits & Vegetables
    if (lowerName.contains('appel') || lowerName.contains('banaan') || 
        lowerName.contains('tomaat') || lowerName.contains('ui') ||
        lowerName.contains('wortel') || lowerName.contains('sla') ||
        lowerName.contains('komkommer') || lowerName.contains('paprika') ||
        lowerName.contains('fruit') || lowerName.contains('groente')) {
      return 'Groente & fruit';
    }
    
    // Drinks
    if (lowerName.contains('cola') || lowerName.contains('sap') || 
        lowerName.contains('water') || lowerName.contains('bier') ||
        lowerName.contains('koffie') || lowerName.contains('thee') ||
        lowerName.contains('wijn') || lowerName.contains('frisdrank')) {
      return 'Dranken';
    }
    
    // Meat, Fish & Vegetarian
    if (lowerName.contains('vlees') || lowerName.contains('kip') || 
        lowerName.contains('vis') || lowerName.contains('gehakt') ||
        lowerName.contains('worst') || lowerName.contains('ham') ||
        lowerName.contains('vegetarisch') || lowerName.contains('vegan')) {
      return 'Vlees, vis & vegetarisch';
    }
    
    // Frozen
    if (lowerName.contains('diepvries') || lowerName.contains('frozen') ||
        lowerName.contains('ijs') || lowerName.contains('ijsje')) {
      return 'Diepvries';
    }
    
    // Baby & Child
    if (lowerName.contains('baby') || lowerName.contains('luier') ||
        lowerName.contains('flesvoeding') || lowerName.contains('kindje')) {
      return 'Baby & kind';
    }
    
    // Personal Care
    if (lowerName.contains('shampoo') || lowerName.contains('tandpasta') ||
        lowerName.contains('zeep') || lowerName.contains('deodorant') ||
        lowerName.contains('parfum') || lowerName.contains('creme')) {
      return 'Verzorging';
    }
    
    // Household
    if (lowerName.contains('wasmiddel') || lowerName.contains('afwasmiddel') ||
        lowerName.contains('toiletpapier') || lowerName.contains('keukenrol') ||
        lowerName.contains('schoonmaak')) {
      return 'Huishouden';
    }
    
    // Default category
    return 'Houdbaar';
  }
  
  /// Extract unit type from size string
  static String _extractUnitType(String size) {
    final lowerSize = size.toLowerCase();
    
    if (lowerSize.contains('kg')) return 'kg';
    if (lowerSize.contains('gram') || lowerSize.contains('g ')) return 'gram';
    if (lowerSize.contains('liter') || lowerSize.contains('l ')) return 'liter';
    if (lowerSize.contains('ml')) return 'ml';
    if (lowerSize.contains('cl')) return 'cl';
    if (lowerSize.contains('stuks') || lowerSize.contains('st ')) return 'piece';
    
    return 'piece';
  }
  
  /// Extract package size from size string
  static double? _extractPackageSize(String size) {
    final regex = RegExp(r'(\d+(?:\.\d+)?)');
    final match = regex.firstMatch(size);
    
    if (match != null) {
      return double.tryParse(match.group(1)!);
    }
    
    return null;
  }
  
  /// Extract package unit from size string
  static String _extractPackageUnit(String size) {
    final lowerSize = size.toLowerCase();
    
    if (lowerSize.contains('kg')) return 'kg';
    if (lowerSize.contains('gram') || lowerSize.contains('g')) return 'g';
    if (lowerSize.contains('liter') || lowerSize.contains('l')) return 'l';
    if (lowerSize.contains('ml')) return 'ml';
    if (lowerSize.contains('cl')) return 'cl';
    if (lowerSize.contains('stuks') || lowerSize.contains('st')) return 'stuks';
    
    return 'stuks';
  }
  
  /// Check if product is organic
  static bool _isOrganic(String productName) {
    final lowerName = productName.toLowerCase();
    return lowerName.contains('organic') || lowerName.contains('biologisch');
  }
  
  /// Check if product is bio
  static bool _isBio(String productName) {
    final lowerName = productName.toLowerCase();
    return lowerName.contains('bio ') || lowerName.contains('biologisch');
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
        'name': 'Diepvries',
        'slug': 'diepvries',
        'parent_id': null,
        'icon_name': 'ac_unit',
        'display_order': 6,
      },
      {
        'name': 'Houdbaar',
        'slug': 'houdbaar',
        'parent_id': null,
        'icon_name': 'inventory_2',
        'display_order': 7,
      },
      {
        'name': 'Dranken',
        'slug': 'dranken',
        'parent_id': null,
        'icon_name': 'local_drink',
        'display_order': 8,
      },
      {
        'name': 'Snacks & snoep',
        'slug': 'snacks-snoep',
        'parent_id': null,
        'icon_name': 'cookie',
        'display_order': 9,
      },
      {
        'name': 'Verzorging',
        'slug': 'verzorging',
        'parent_id': null,
        'icon_name': 'local_pharmacy',
        'display_order': 10,
      },
      {
        'name': 'Huishouden',
        'slug': 'huishouden',
        'parent_id': null,
        'icon_name': 'cleaning_services',
        'display_order': 11,
      },
      {
        'name': 'Baby & kind',
        'slug': 'baby-kind',
        'parent_id': null,
        'icon_name': 'child_care',
        'display_order': 12,
      },
    ];
    
    await _client.from('categories').insert(categories);
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
    ];
    
    await _client.from('supermarkets').insert(supermarkets);
  }
}

/// Result of import operation
class ImportResult {
  final int totalProducts;
  final int totalPrices;
  final int processedGroups;
  
  ImportResult({
    required this.totalProducts,
    required this.totalPrices,
    required this.processedGroups,
  });
  
  @override
  String toString() {
    return 'ImportResult{products: $totalProducts, prices: $totalPrices, groups: $processedGroups}';
  }
}