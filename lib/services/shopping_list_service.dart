import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/shopping_list.dart';
import '../models/product.dart';
import '../config/supabase_config.dart';

class ShoppingListService {
  static final SupabaseClient _client = SupabaseConfig.client;

  // Get all shopping lists
  static Future<List<ShoppingList>> getShoppingLists() async {
    try {
      final response = await _client
          .from('shopping_lists')
          .select('''
            *,
            shopping_list_items:shopping_list_items(
              *,
              product:products(
                *,
                prices:prices(
                  *,
                  supermarket:supermarkets(*)
                ),
                category:categories(*)
              )
            )
          ''')
          .order('created_at', ascending: false);

      return response.map<ShoppingList>((item) => ShoppingList.fromJson(item)).toList();
    } catch (e) {
      print('Error fetching shopping lists: $e');
      return [];
    }
  }

  // Get shopping list by ID
  static Future<ShoppingList?> getShoppingListById(String id) async {
    try {
      final response = await _client
          .from('shopping_lists')
          .select('''
            *,
            shopping_list_items:shopping_list_items(
              *,
              product:products(
                *,
                prices:prices(
                  *,
                  supermarket:supermarkets(*)
                ),
                category:categories(*)
              )
            )
          ''')
          .eq('id', id)
          .single();

      return ShoppingList.fromJson(response);
    } catch (e) {
      print('Error fetching shopping list: $e');
      return null;
    }
  }

  // Create shopping list
  static Future<ShoppingList?> createShoppingList({
    required String name,
    String? description,
    bool isShared = false,
  }) async {
    try {
      final now = DateTime.now();
      String? sharedCode;
      
      if (isShared) {
        sharedCode = await _generateUniqueSharedCode();
      }

      final listData = {
        'name': name,
        'description': description,
        'is_shared': isShared,
        'shared_code': sharedCode,
        'created_at': now.toIso8601String(),
        'updated_at': now.toIso8601String(),
      };

      final response = await _client
          .from('shopping_lists')
          .insert(listData)
          .select()
          .single();

      return ShoppingList.fromJson(response);
    } catch (e) {
      print('Error creating shopping list: $e');
      return null;
    }
  }

  // Update shopping list
  static Future<ShoppingList?> updateShoppingList(
    String id, {
    String? name,
    String? description,
    bool? isShared,
  }) async {
    try {
      final updateData = <String, dynamic>{
        'updated_at': DateTime.now().toIso8601String(),
      };

      if (name != null) updateData['name'] = name;
      if (description != null) updateData['description'] = description;
      if (isShared != null) {
        updateData['is_shared'] = isShared;
        if (isShared && updateData['shared_code'] == null) {
          updateData['shared_code'] = await _generateUniqueSharedCode();
        } else if (!isShared) {
          updateData['shared_code'] = null;
        }
      }

      final response = await _client
          .from('shopping_lists')
          .update(updateData)
          .eq('id', id)
          .select()
          .single();

      return ShoppingList.fromJson(response);
    } catch (e) {
      print('Error updating shopping list: $e');
      return null;
    }
  }

  // Delete shopping list
  static Future<bool> deleteShoppingList(String id) async {
    try {
      await _client
          .from('shopping_lists')
          .delete()
          .eq('id', id);
      return true;
    } catch (e) {
      print('Error deleting shopping list: $e');
      return false;
    }
  }

  // Add item to shopping list
  static Future<ShoppingListItem?> addItemToList({
    required String listId,
    String? productId,
    required String name,
    int quantity = 1,
    String? notes,
  }) async {
    try {
      final now = DateTime.now();
      final itemData = {
        'list_id': listId,
        'product_id': productId,
        'name': name,
        'quantity': quantity,
        'notes': notes,
        'is_checked': false,
        'created_at': now.toIso8601String(),
        'updated_at': now.toIso8601String(),
      };

      final response = await _client
          .from('shopping_list_items')
          .insert(itemData)
          .select('''
            *,
            product:products(
              *,
              prices:prices(
                *,
                supermarket:supermarkets(*)
              ),
              category:categories(*)
            )
          ''')
          .single();

      // Update list's updated_at
      await _client
          .from('shopping_lists')
          .update({'updated_at': now.toIso8601String()})
          .eq('id', listId);

      return ShoppingListItem.fromJson(response);
    } catch (e) {
      print('Error adding item to list: $e');
      return null;
    }
  }

  // Update shopping list item
  static Future<ShoppingListItem?> updateListItem(
    String itemId, {
    String? name,
    int? quantity,
    String? notes,
    bool? isChecked,
  }) async {
    try {
      final updateData = <String, dynamic>{
        'updated_at': DateTime.now().toIso8601String(),
      };

      if (name != null) updateData['name'] = name;
      if (quantity != null) updateData['quantity'] = quantity;
      if (notes != null) updateData['notes'] = notes;
      if (isChecked != null) updateData['is_checked'] = isChecked;

      final response = await _client
          .from('shopping_list_items')
          .update(updateData)
          .eq('id', itemId)
          .select('''
            *,
            product:products(
              *,
              prices:prices(
                *,
                supermarket:supermarkets(*)
              ),
              category:categories(*)
            )
          ''')
          .single();

      // Update parent list's updated_at
      await _client
          .from('shopping_lists')
          .update({'updated_at': DateTime.now().toIso8601String()})
          .eq('id', response['list_id']);

      return ShoppingListItem.fromJson(response);
    } catch (e) {
      print('Error updating list item: $e');
      return null;
    }
  }

  // Delete shopping list item
  static Future<bool> deleteListItem(String itemId) async {
    try {
      // Get list_id before deleting for updating parent list
      final item = await _client
          .from('shopping_list_items')
          .select('list_id')
          .eq('id', itemId)
          .single();

      await _client
          .from('shopping_list_items')
          .delete()
          .eq('id', itemId);

      // Update parent list's updated_at
      await _client
          .from('shopping_lists')
          .update({'updated_at': DateTime.now().toIso8601String()})
          .eq('id', item['list_id']);

      return true;
    } catch (e) {
      print('Error deleting list item: $e');
      return false;
    }
  }

  // Toggle item checked status
  static Future<bool> toggleItemChecked(String itemId, bool isChecked) async {
    try {
      await updateListItem(itemId, isChecked: isChecked);
      return true;
    } catch (e) {
      print('Error toggling item checked: $e');
      return false;
    }
  }

  // Clear checked items from list
  static Future<bool> clearCheckedItems(String listId) async {
    try {
      await _client
          .from('shopping_list_items')
          .delete()
          .eq('list_id', listId)
          .eq('is_checked', true);

      // Update parent list's updated_at
      await _client
          .from('shopping_lists')
          .update({'updated_at': DateTime.now().toIso8601String()})
          .eq('id', listId);

      return true;
    } catch (e) {
      print('Error clearing checked items: $e');
      return false;
    }
  }

  // Get shopping list by shared code
  static Future<ShoppingList?> getShoppingListBySharedCode(String sharedCode) async {
    try {
      final response = await _client
          .from('shopping_lists')
          .select('''
            *,
            shopping_list_items:shopping_list_items(
              *,
              product:products(
                *,
                prices:prices(
                  *,
                  supermarket:supermarkets(*)
                ),
                category:categories(*)
              )
            )
          ''')
          .eq('shared_code', sharedCode.toUpperCase())
          .eq('is_shared', true)
          .single();

      return ShoppingList.fromJson(response);
    } catch (e) {
      print('Error fetching shared shopping list: $e');
      return null;
    }
  }

  // Generate unique shared code
  static Future<String> _generateUniqueSharedCode() async {
    String code;
    bool isUnique = false;
    int attempts = 0;
    const maxAttempts = 10;

    do {
      code = _generateRandomCode();
      attempts++;
      
      try {
        final existing = await _client
            .from('shopping_lists')
            .select('id')
            .eq('shared_code', code)
            .limit(1);
        
        isUnique = existing.isEmpty;
      } catch (e) {
        // If error checking, assume unique and break
        isUnique = true;
      }
    } while (!isUnique && attempts < maxAttempts);

    return code;
  }

  static String _generateRandomCode() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    var result = '';
    for (int i = 0; i < 6; i++) {
      result += chars[(DateTime.now().millisecondsSinceEpoch + i) % chars.length];
    }
    return result;
  }

  // Add product from search to shopping list
  static Future<ShoppingListItem?> addProductToList({
    required String listId,
    required ProductWithPrices productWithPrices,
    int quantity = 1,
    String? notes,
  }) async {
    return await addItemToList(
      listId: listId,
      productId: productWithPrices.product.id,
      name: productWithPrices.product.name,
      quantity: quantity,
      notes: notes,
    );
  }
}