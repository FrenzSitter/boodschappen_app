import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

// Data import script for Checkjebon GitHub repository data
// This script fetches product data from the Checkjebon repository and formats it for our database

class CheckjebonDataImporter {
  static const String baseUrl = 'https://raw.githubusercontent.com/supermarkt/checkjebon/main/data';
  
  // Known supermarket data files from Checkjebon
  static const Map<String, String> supermarketFiles = {
    'albert-heijn': 'supermarkets.json', // This appears to be Albert Heijn data
    // Add more when discovered
  };

  static Future<void> importAllData() async {
    print('Starting Checkjebon data import...');
    
    for (final entry in supermarketFiles.entries) {
      final supermarketSlug = entry.key;
      final fileName = entry.value;
      
      try {
        print('Importing data for $supermarketSlug from $fileName...');
        await importSupermarketData(supermarketSlug, fileName);
        print('Successfully imported $supermarketSlug data');
      } catch (e) {
        print('Error importing $supermarketSlug data: $e');
      }
    }
    
    print('Data import completed!');
  }

  static Future<void> importSupermarketData(String supermarketSlug, String fileName) async {
    final url = '$baseUrl/$fileName';
    
    try {
      final response = await http.get(Uri.parse(url));
      
      if (response.statusCode != 200) {
        throw Exception('Failed to fetch data: ${response.statusCode}');
      }
      
      final jsonData = jsonDecode(response.body) as List<dynamic>;
      
      // Convert to our database format
      final products = await convertToProductFormat(jsonData, supermarketSlug);
      
      // Generate SQL insert statements
      final sqlStatements = generateInsertStatements(products, supermarketSlug);
      
      // Save to file for manual execution in Supabase
      await saveToSqlFile(sqlStatements, supermarketSlug);
      
    } catch (e) {
      print('Error processing $fileName: $e');
      rethrow;
    }
  }

  static Future<List<ProductData>> convertToProductFormat(
    List<dynamic> jsonData, 
    String supermarketSlug
  ) async {
    final products = <ProductData>[];
    
    for (final item in jsonData) {
      final productName = item['n'] as String;
      final variants = item['d'] as List<dynamic>;
      
      for (final variant in variants) {
        final variantName = variant['n'] as String;
        final productId = variant['l'] as String;
        final price = (variant['p'] as num).toDouble();
        final size = variant['s'] as String?;
        
        // Create a combined product name
        final fullName = productName == variantName 
            ? productName 
            : '$productName - $variantName';
        
        products.add(ProductData(
          name: fullName,
          productId: productId,
          price: price,
          size: size ?? '',
          supermarketSlug: supermarketSlug,
        ));
      }
    }
    
    print('Converted ${products.length} products for $supermarketSlug');
    return products;
  }

  static List<String> generateInsertStatements(
    List<ProductData> products, 
    String supermarketSlug
  ) {
    final statements = <String>[];
    
    // Group products by batches for performance
    const batchSize = 100;
    
    for (int i = 0; i < products.length; i += batchSize) {
      final batch = products.skip(i).take(batchSize).toList();
      
      // Insert products
      final productValues = batch.map((p) => 
        "(uuid_generate_v4(), ${_escapeString(p.name)}, NULL, NULL, ${_escapeString(p.productId)}, NULL, 'piece', NULL, NULL, ${_escapeString(p.size)}, NULL, NULL, NULL, false, false, NOW(), NOW())"
      ).join(',\n  ');
      
      statements.add('''
-- Insert products batch ${(i ~/ batchSize) + 1}
INSERT INTO products (id, name, brand, category_id, barcode, image_url, unit_type, package_size, package_unit, description, ingredients, nutritional_info, allergens, is_organic, is_bio, created_at, updated_at)
VALUES
  $productValues
ON CONFLICT (barcode) DO NOTHING;
''');

      // Insert prices
      final priceValues = batch.map((p) => 
        "((SELECT id FROM products WHERE barcode = ${_escapeString(p.productId)} LIMIT 1), (SELECT id FROM supermarkets WHERE slug = '$supermarketSlug' LIMIT 1), ${p.price}, ${p.price}, 'EUR', true, false, NULL, NULL, NOW(), NOW())"
      ).join(',\n  ');
      
      statements.add('''
-- Insert prices batch ${(i ~/ batchSize) + 1}
INSERT INTO product_prices (product_id, supermarket_id, price, price_per_unit, currency, is_available, is_on_sale, sale_start_date, sale_end_date, last_updated, created_at)
VALUES
  $priceValues
ON CONFLICT (product_id, supermarket_id) DO UPDATE SET
  price = EXCLUDED.price,
  price_per_unit = EXCLUDED.price_per_unit,
  last_updated = NOW();
''');
    }
    
    return statements;
  }

  static String _escapeString(String? value) {
    if (value == null) return 'NULL';
    // Basic SQL string escaping
    final escaped = value.replaceAll("'", "''");
    return "'$escaped'";
  }

  static Future<void> saveToSqlFile(List<String> statements, String supermarketSlug) async {
    final file = File('database/import_${supermarketSlug}_data.sql');
    
    // Create directory if it doesn't exist
    await file.parent.create(recursive: true);
    
    final content = '''
-- Generated import script for $supermarketSlug from Checkjebon data
-- Execute this in your Supabase SQL editor
-- Generated on: ${DateTime.now().toIso8601String()}

${statements.join('\n\n')}
''';
    
    await file.writeAsString(content);
    print('SQL import file saved: ${file.path}');
  }
}

class ProductData {
  final String name;
  final String productId;
  final double price;
  final String size;
  final String supermarketSlug;

  ProductData({
    required this.name,
    required this.productId,
    required this.price,
    required this.size,
    required this.supermarketSlug,
  });
}

// Main function to run the import
void main() async {
  try {
    await CheckjebonDataImporter.importAllData();
  } catch (e) {
    print('Import failed: $e');
    exit(1);
  }
}