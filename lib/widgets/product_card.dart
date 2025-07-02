import 'package:flutter/material.dart';
import '../models/product.dart';
import '../models/shopping_list.dart';
import '../services/shopping_list_service.dart';
import '../pages/product_comparison_page.dart';

class ProductCard extends StatelessWidget {
  final ProductWithPrices productWithPrices;
  final VoidCallback? onTap;

  const ProductCard({
    super.key,
    required this.productWithPrices,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final product = productWithPrices.product;
    final prices = productWithPrices.availablePrices;
    final cheapestPrice = productWithPrices.cheapestPrice;
    final lowestPrice = productWithPrices.lowestPrice;
    final highestPrice = productWithPrices.highestPrice;

    return Card(
      elevation: 2,
      margin: const EdgeInsets.all(8),
      child: InkWell(
        onTap: onTap ?? () {
          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (context) => ProductComparisonPage(
                productWithPrices: productWithPrices,
              ),
            ),
          );
        },
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Product image placeholder
              Container(
                height: 120,
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.grey[200],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: product.imageUrl != null
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: Image.network(
                          product.imageUrl!,
                          fit: BoxFit.cover,
                          errorBuilder: (context, error, stackTrace) {
                            return const Icon(
                              Icons.shopping_basket,
                              size: 48,
                              color: Colors.grey,
                            );
                          },
                        ),
                      )
                    : const Icon(
                        Icons.shopping_basket,
                        size: 48,
                        color: Colors.grey,
                      ),
              ),
              const SizedBox(height: 8),
              
              // Product name
              Text(
                product.name,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              
              // Brand
              if (product.brand != null) ...[
                const SizedBox(height: 4),
                Text(
                  product.brand!,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                  ),
                ),
              ],
              
              // Category
              if (product.categoryName != null) ...[
                const SizedBox(height: 4),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.primaryContainer,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    product.categoryName!,
                    style: TextStyle(
                      fontSize: 10,
                      color: Theme.of(context).colorScheme.onPrimaryContainer,
                    ),
                  ),
                ),
              ],
              
              const SizedBox(height: 8),
              
              // Price information
              if (prices.isNotEmpty) ...[
                // Price range
                if (lowestPrice != null && highestPrice != null && lowestPrice != highestPrice) ...[
                  Text(
                    '€${lowestPrice!.toStringAsFixed(2)} - €${highestPrice!.toStringAsFixed(2)}',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Colors.green,
                    ),
                  ),
                ] else if (lowestPrice != null) ...[
                  Text(
                    '€${lowestPrice!.toStringAsFixed(2)}',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Colors.green,
                    ),
                  ),
                ],
                
                const SizedBox(height: 4),
                
                // Cheapest store
                if (cheapestPrice != null) ...[
                  Text(
                    'Goedkoopst bij ${cheapestPrice!.supermarketName}',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[600],
                    ),
                  ),
                ],
                
                const SizedBox(height: 8),
                
                // Store count
                Text(
                  '${prices.length} ${prices.length == 1 ? 'winkel' : 'winkels'}',
                  style: TextStyle(
                    fontSize: 12,
                    color: Theme.of(context).colorScheme.primary,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ] else ...[
                const Text(
                  'Geen prijzen beschikbaar',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey,
                  ),
                ),
              ],
              
              // Special indicators
              const SizedBox(height: 8),
              Wrap(
                spacing: 4,
                children: [
                  if (product.isOrganic)
                    _buildTag('Biologisch', Colors.green),
                  if (product.isBio)
                    _buildTag('Bio', Colors.green),
                  if (prices.any((p) => p.isOnSale))
                    _buildTag('Aanbieding', Colors.red),
                ],
              ),
              
              // Add to list button
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () => _showAddToListDialog(context),
                  icon: const Icon(Icons.add_shopping_cart, size: 16),
                  label: const Text('Toevoegen aan lijst'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTag(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 10,
          color: color,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  void _showAddToListDialog(BuildContext context) async {
    // Get available shopping lists
    final lists = await ShoppingListService.getShoppingLists();
    
    if (!context.mounted) return;
    
    if (lists.isEmpty) {
      // No lists available, prompt to create one
      final shouldCreate = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Geen lijsten gevonden'),
          content: const Text('Je hebt nog geen boodschappenlijsten. Wil je er een aanmaken?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Annuleren'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Lijst aanmaken'),
            ),
          ],
        ),
      );
      
      if (shouldCreate == true) {
        // Navigate to lists page (could implement direct creation here)
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Ga naar het Lijsten tabblad om een lijst aan te maken')),
        );
      }
      return;
    }
    
    // Show list selection dialog
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => AddToListDialog(
        productWithPrices: productWithPrices,
        availableLists: lists,
      ),
    );
    
    if (result != null) {
      final success = await ShoppingListService.addProductToList(
        listId: result['listId'],
        productWithPrices: productWithPrices,
        quantity: result['quantity'] ?? 1,
        notes: result['notes'],
      );
      
      if (success != null && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('${productWithPrices.product.name} toegevoegd aan lijst'),
            action: SnackBarAction(
              label: 'OK',
              onPressed: () {},
            ),
          ),
        );
      }
    }
  }
}

class AddToListDialog extends StatefulWidget {
  final ProductWithPrices productWithPrices;
  final List<ShoppingList> availableLists;

  const AddToListDialog({
    super.key,
    required this.productWithPrices,
    required this.availableLists,
  });

  @override
  State<AddToListDialog> createState() => _AddToListDialogState();
}

class _AddToListDialogState extends State<AddToListDialog> {
  String? _selectedListId;
  int _quantity = 1;
  final _notesController = TextEditingController();

  @override
  void initState() {
    super.initState();
    if (widget.availableLists.isNotEmpty) {
      _selectedListId = widget.availableLists.first.id;
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('${widget.productWithPrices.product.name} toevoegen'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // List selection
          DropdownButtonFormField<String>(
            value: _selectedListId,
            decoration: const InputDecoration(
              labelText: 'Kies lijst',
              border: OutlineInputBorder(),
            ),
            items: widget.availableLists.map((list) {
              return DropdownMenuItem(
                value: list.id,
                child: Text(list.name),
              );
            }).toList(),
            onChanged: (value) => setState(() => _selectedListId = value),
          ),
          
          const SizedBox(height: 16),
          
          // Quantity selector
          Row(
            children: [
              const Text('Aantal:'),
              const SizedBox(width: 16),
              IconButton(
                onPressed: _quantity > 1 ? () => setState(() => _quantity--) : null,
                icon: const Icon(Icons.remove),
              ),
              Text(
                _quantity.toString(),
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              IconButton(
                onPressed: () => setState(() => _quantity++),
                icon: const Icon(Icons.add),
              ),
            ],
          ),
          
          const SizedBox(height: 16),
          
          // Notes
          TextField(
            controller: _notesController,
            decoration: const InputDecoration(
              labelText: 'Notities (optioneel)',
              hintText: 'Extra informatie',
              border: OutlineInputBorder(),
            ),
            maxLines: 2,
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Annuleren'),
        ),
        ElevatedButton(
          onPressed: _selectedListId != null
              ? () {
                  Navigator.pop(context, {
                    'listId': _selectedListId,
                    'quantity': _quantity,
                    'notes': _notesController.text.trim().isNotEmpty
                        ? _notesController.text.trim()
                        : null,
                  });
                }
              : null,
          child: const Text('Toevoegen'),
        ),
      ],
    );
  }

  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }
}

class ProductDetailCard extends StatelessWidget {
  final ProductWithPrices productWithPrices;

  const ProductDetailCard({
    super.key,
    required this.productWithPrices,
  });

  @override
  Widget build(BuildContext context) {
    final product = productWithPrices.product;
    final prices = productWithPrices.availablePrices;

    return Card(
      elevation: 4,
      margin: const EdgeInsets.all(16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Product header
            Row(
              children: [
                // Product image
                Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    color: Colors.grey[200],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: product.imageUrl != null
                      ? ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.network(
                            product.imageUrl!,
                            fit: BoxFit.cover,
                            errorBuilder: (context, error, stackTrace) {
                              return const Icon(
                                Icons.shopping_basket,
                                size: 32,
                                color: Colors.grey,
                              );
                            },
                          ),
                        )
                      : const Icon(
                          Icons.shopping_basket,
                          size: 32,
                          color: Colors.grey,
                        ),
                ),
                const SizedBox(width: 16),
                
                // Product info
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        product.name,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      if (product.brand != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          product.brand!,
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                      if (product.categoryName != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          product.categoryName!,
                          style: TextStyle(
                            fontSize: 12,
                            color: Theme.of(context).colorScheme.primary,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
            
            const SizedBox(height: 24),
            
            // Price comparison
            const Text(
              'Prijsvergelijking',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            
            // Prices list
            if (prices.isNotEmpty) ...[
              ...prices.map((price) => _buildPriceRow(context, price)),
            ] else ...[
              const Text(
                'Geen prijzen beschikbaar',
                style: TextStyle(color: Colors.grey),
              ),
            ],
            
            // Additional info
            if (product.description != null) ...[
              const SizedBox(height: 24),
              const Text(
                'Beschrijving',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Text(product.description!),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildPriceRow(BuildContext context, ProductPrice price) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey[300]!),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          // Supermarket name
          Expanded(
            child: Text(
              price.supermarketName,
              style: const TextStyle(
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          
          // Price
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '€${price.price.toStringAsFixed(2)}',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (price.originalPrice != null && price.originalPrice! > price.price) ...[
                Text(
                  '€${price.originalPrice!.toStringAsFixed(2)}',
                  style: const TextStyle(
                    fontSize: 12,
                    decoration: TextDecoration.lineThrough,
                    color: Colors.grey,
                  ),
                ),
              ],
              if (price.pricePerUnit != null) ...[
                Text(
                  '€${price.pricePerUnit!.toStringAsFixed(2)}/eenheid',
                  style: const TextStyle(
                    fontSize: 10,
                    color: Colors.grey,
                  ),
                ),
              ],
            ],
          ),
          
          // Sale indicator
          if (price.isOnSale) ...[
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: Colors.red.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Text(
                'SALE',
                style: TextStyle(
                  fontSize: 10,
                  color: Colors.red,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}