import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/shopping_list.dart';

class ShoppingListCard extends StatelessWidget {
  final ShoppingList shoppingList;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  const ShoppingListCard({
    super.key,
    required this.shoppingList,
    required this.onTap,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final completionPercentage = shoppingList.completionPercentage;
    
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header with title and actions
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                shoppingList.name,
                                style: const TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            if (shoppingList.isShared) ...[
                              const SizedBox(width: 8),
                              Icon(
                                Icons.share,
                                size: 16,
                                color: theme.colorScheme.primary,
                              ),
                            ],
                          ],
                        ),
                        if (shoppingList.description != null) ...[
                          const SizedBox(height: 4),
                          Text(
                            shoppingList.description!,
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey[600],
                            ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ],
                    ),
                  ),
                  PopupMenuButton<String>(
                    onSelected: (value) => _handleMenuAction(context, value),
                    itemBuilder: (context) => [
                      const PopupMenuItem(
                        value: 'edit',
                        child: ListTile(
                          leading: Icon(Icons.edit),
                          title: Text('Bewerken'),
                          contentPadding: EdgeInsets.zero,
                        ),
                      ),
                      if (shoppingList.isShared)
                        const PopupMenuItem(
                          value: 'share',
                          child: ListTile(
                            leading: Icon(Icons.share),
                            title: Text('Code delen'),
                            contentPadding: EdgeInsets.zero,
                          ),
                        ),
                      const PopupMenuItem(
                        value: 'delete',
                        child: ListTile(
                          leading: Icon(Icons.delete, color: Colors.red),
                          title: Text('Verwijderen'),
                          contentPadding: EdgeInsets.zero,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              
              const SizedBox(height: 16),
              
              // Progress section
              if (shoppingList.totalItems > 0) ...[
                Row(
                  children: [
                    Expanded(
                      child: LinearProgressIndicator(
                        value: completionPercentage / 100,
                        backgroundColor: Colors.grey[200],
                        valueColor: AlwaysStoppedAnimation<Color>(
                          completionPercentage == 100
                              ? Colors.green
                              : theme.colorScheme.primary,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      '${completionPercentage.round()}%',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
              ],
              
              // Stats row
              Row(
                children: [
                  _buildStatChip(
                    icon: Icons.shopping_cart,
                    label: '${shoppingList.totalItems}',
                    color: Colors.blue,
                  ),
                  if (shoppingList.checkedItems > 0) ...[
                    const SizedBox(width: 8),
                    _buildStatChip(
                      icon: Icons.check_circle,
                      label: '${shoppingList.checkedItems}',
                      color: Colors.green,
                    ),
                  ],
                  const Spacer(),
                  if (shoppingList.estimatedTotal > 0)
                    Text(
                      '~€${shoppingList.estimatedTotal.toStringAsFixed(2)}',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: theme.colorScheme.primary,
                      ),
                    ),
                ],
              ),
              
              const SizedBox(height: 8),
              
              // Last updated
              Text(
                'Bijgewerkt ${_getRelativeTime(shoppingList.updatedAt)}',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[500],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatChip({
    required IconData icon,
    required String label,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  String _getRelativeTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inDays > 0) {
      return '${difference.inDays} ${difference.inDays == 1 ? 'dag' : 'dagen'} geleden';
    } else if (difference.inHours > 0) {
      return '${difference.inHours} ${difference.inHours == 1 ? 'uur' : 'uur'} geleden';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes} ${difference.inMinutes == 1 ? 'minuut' : 'minuten'} geleden';
    } else {
      return 'Zojuist';
    }
  }

  void _handleMenuAction(BuildContext context, String action) {
    switch (action) {
      case 'edit':
        _showEditDialog(context);
        break;
      case 'share':
        _shareList(context);
        break;
      case 'delete':
        onDelete();
        break;
    }
  }

  void _showEditDialog(BuildContext context) {
    // TODO: Implement edit dialog
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Bewerken komt binnenkort beschikbaar')),
    );
  }

  void _shareList(BuildContext context) {
    if (shoppingList.sharedCode != null) {
      Clipboard.setData(ClipboardData(text: shoppingList.sharedCode!));
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Code ${shoppingList.sharedCode!} gekopieerd naar klembord'),
          action: SnackBarAction(
            label: 'OK',
            onPressed: () {},
          ),
        ),
      );
    }
  }
}