import 'package:flutter/material.dart';
import '../models/shopping_list.dart';

class ShoppingListItemCard extends StatelessWidget {
  final ShoppingListItem item;
  final VoidCallback onToggleChecked;
  final VoidCallback onDelete;

  const ShoppingListItemCard({
    super.key,
    required this.item,
    required this.onToggleChecked,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isChecked = item.isChecked;
    
    return Card(
      elevation: isChecked ? 1 : 2,
      color: isChecked ? Colors.grey[50] : null,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: InkWell(
        onTap: onToggleChecked,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              // Checkbox
              Checkbox(
                value: isChecked,
                onChanged: (_) => onToggleChecked(),
                activeColor: theme.colorScheme.primary,
              ),
              
              const SizedBox(width: 8),
              
              // Main content
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Item name and quantity
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            item.name,
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w500,
                              decoration: isChecked ? TextDecoration.lineThrough : null,
                              color: isChecked ? Colors.grey[600] : null,
                            ),
                          ),
                        ),
                        if (item.quantity > 1) ...[
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: theme.colorScheme.primaryContainer,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              '${item.quantity}x',
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w500,
                                color: theme.colorScheme.onPrimaryContainer,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                    
                    // Notes
                    if (item.notes != null && item.notes!.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        item.notes!,
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey[600],
                          decoration: isChecked ? TextDecoration.lineThrough : null,
                        ),
                      ),
                    ],
                    
                    // Product info and price
                    if (item.productWithPrices != null) ...[
                      const SizedBox(height: 8),
                      _buildProductInfo(theme),
                    ],
                  ],
                ),
              ),
              
              // Delete button
              IconButton(
                onPressed: onDelete,
                icon: Icon(
                  Icons.delete_outline,
                  color: Colors.grey[600],
                ),
                tooltip: 'Verwijderen',
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProductInfo(ThemeData theme) {
    final product = item.productWithPrices!.product;
    final prices = item.productWithPrices!.prices;
    
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceVariant.withOpacity(0.3),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Product name and brand
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      product.name,
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (product.brand != null)
                      Text(
                        product.brand!,
                        style: TextStyle(
                          fontSize: 10,
                          color: Colors.grey[600],
                        ),
                      ),
                  ],
                ),
              ),
              
              // Best price
              if (prices.isNotEmpty) ...[
                const SizedBox(width: 8),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      '€${_getBestPrice().toStringAsFixed(2)}',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: theme.colorScheme.primary,
                      ),
                    ),
                    Text(
                      _getBestPriceSupermarket(),
                      style: TextStyle(
                        fontSize: 10,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
          
          // Price comparison (if multiple prices)
          if (prices.length > 1) ...[
            const SizedBox(height: 4),
            Text(
              '${prices.length} winkels vergelijken',
              style: TextStyle(
                fontSize: 10,
                color: theme.colorScheme.primary,
                decoration: TextDecoration.underline,
              ),
            ),
          ],
        ],
      ),
    );
  }

  double _getBestPrice() {
    if (item.productWithPrices?.prices.isEmpty ?? true) return 0.0;
    return item.productWithPrices!.prices.map((p) => p.price).reduce((a, b) => a < b ? a : b);
  }

  String _getBestPriceSupermarket() {
    if (item.productWithPrices?.prices.isEmpty ?? true) return '';
    final bestPrice = _getBestPrice();
    final bestPriceItem = item.productWithPrices!.prices.firstWhere((p) => p.price == bestPrice);
    return bestPriceItem.supermarketName;
  }
}