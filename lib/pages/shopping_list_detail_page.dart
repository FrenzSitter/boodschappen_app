import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/shopping_list.dart';
import '../services/shopping_list_service.dart';
import '../widgets/shopping_list_item_card.dart';

class ShoppingListDetailPage extends StatefulWidget {
  final ShoppingList shoppingList;

  const ShoppingListDetailPage({
    super.key,
    required this.shoppingList,
  });

  @override
  State<ShoppingListDetailPage> createState() => _ShoppingListDetailPageState();
}

class _ShoppingListDetailPageState extends State<ShoppingListDetailPage> {
  late ShoppingList _shoppingList;
  bool _isLoading = false;
  bool _showCheckedItems = true;

  @override
  void initState() {
    super.initState();
    _shoppingList = widget.shoppingList;
    _refreshList();
  }

  Future<void> _refreshList() async {
    setState(() => _isLoading = true);
    try {
      final updatedList = await ShoppingListService.getShoppingListById(_shoppingList.id);
      if (updatedList != null) {
        setState(() => _shoppingList = updatedList);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fout bij verversen: $e')),
        );
      }
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _addItem() async {
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => const AddItemDialog(),
    );

    if (result != null) {
      final newItem = await ShoppingListService.addItemToList(
        listId: _shoppingList.id,
        name: result['name'],
        quantity: result['quantity'] ?? 1,
        notes: result['notes'],
      );

      if (newItem != null) {
        setState(() {
          _shoppingList = _shoppingList.copyWith(
            items: [..._shoppingList.items, newItem],
          );
        });
      }
    }
  }

  Future<void> _toggleItemChecked(ShoppingListItem item) async {
    final success = await ShoppingListService.toggleItemChecked(
      item.id,
      !item.isChecked,
    );

    if (success) {
      setState(() {
        final items = _shoppingList.items.map((i) {
          if (i.id == item.id) {
            return i.copyWith(isChecked: !i.isChecked);
          }
          return i;
        }).toList();
        _shoppingList = _shoppingList.copyWith(items: items);
      });
    }
  }

  Future<void> _deleteItem(ShoppingListItem item) async {
    final success = await ShoppingListService.deleteListItem(item.id);
    
    if (success) {
      setState(() {
        final items = _shoppingList.items.where((i) => i.id != item.id).toList();
        _shoppingList = _shoppingList.copyWith(items: items);
      });
    }
  }

  Future<void> _clearCheckedItems() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Afgevinkte items wissen'),
        content: const Text('Weet je zeker dat je alle afgevinkte items wilt verwijderen?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Annuleren'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Wissen'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      final success = await ShoppingListService.clearCheckedItems(_shoppingList.id);
      if (success) {
        setState(() {
          final items = _shoppingList.items.where((item) => !item.isChecked).toList();
          _shoppingList = _shoppingList.copyWith(items: items);
        });
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Afgevinkte items gewist')),
          );
        }
      }
    }
  }

  List<ShoppingListItem> get _displayedItems {
    if (_showCheckedItems) {
      return _shoppingList.items;
    }
    return _shoppingList.items.where((item) => !item.isChecked).toList();
  }

  List<ShoppingListItem> get _uncheckedItems {
    return _shoppingList.items.where((item) => !item.isChecked).toList();
  }

  List<ShoppingListItem> get _checkedItems {
    return _shoppingList.items.where((item) => item.isChecked).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_shoppingList.name),
        actions: [
          if (_shoppingList.isShared)
            IconButton(
              onPressed: _shareList,
              icon: const Icon(Icons.share),
              tooltip: 'Lijst delen',
            ),
          if (_checkedItems.isNotEmpty)
            IconButton(
              onPressed: _clearCheckedItems,
              icon: const Icon(Icons.clear_all),
              tooltip: 'Afgevinkte items wissen',
            ),
          PopupMenuButton<String>(
            onSelected: _handleMenuAction,
            itemBuilder: (context) => [
              PopupMenuItem(
                value: 'toggle_checked',
                child: ListTile(
                  leading: Icon(_showCheckedItems ? Icons.visibility_off : Icons.visibility),
                  title: Text(_showCheckedItems ? 'Verberg afgevinkt' : 'Toon afgevinkt'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const PopupMenuItem(
                value: 'refresh',
                child: ListTile(
                  leading: Icon(Icons.refresh),
                  title: Text('Verversen'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
            ],
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refreshList,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _buildContent(),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _addItem,
        child: const Icon(Icons.add),
        tooltip: 'Item toevoegen',
      ),
    );
  }

  Widget _buildContent() {
    if (_shoppingList.items.isEmpty) {
      return _buildEmptyState();
    }

    return CustomScrollView(
      slivers: [
        // List info header
        SliverToBoxAdapter(
          child: _buildListHeader(),
        ),

        // Unchecked items
        if (_uncheckedItems.isNotEmpty) ...[
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
              child: Text(
                'Te doen (${_uncheckedItems.length})',
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            sliver: SliverList(
              delegate: SliverChildBuilderDelegate(
                (context, index) {
                  final item = _uncheckedItems[index];
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: ShoppingListItemCard(
                      item: item,
                      onToggleChecked: () => _toggleItemChecked(item),
                      onDelete: () => _deleteItem(item),
                    ),
                  );
                },
                childCount: _uncheckedItems.length,
              ),
            ),
          ),
        ],

        // Checked items (if showing)
        if (_showCheckedItems && _checkedItems.isNotEmpty) ...[
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 24, 16, 8),
              child: Text(
                'Afgevinkt (${_checkedItems.length})',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.grey[600],
                ),
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            sliver: SliverList(
              delegate: SliverChildBuilderDelegate(
                (context, index) {
                  final item = _checkedItems[index];
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: ShoppingListItemCard(
                      item: item,
                      onToggleChecked: () => _toggleItemChecked(item),
                      onDelete: () => _deleteItem(item),
                    ),
                  );
                },
                childCount: _checkedItems.length,
              ),
            ),
          ),
        ],

        // Bottom spacing
        const SliverToBoxAdapter(
          child: SizedBox(height: 80),
        ),
      ],
    );
  }

  Widget _buildListHeader() {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primaryContainer.withOpacity(0.3),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (_shoppingList.description != null) ...[
            Text(
              _shoppingList.description!,
              style: const TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 12),
          ],
          
          // Progress
          if (_shoppingList.totalItems > 0) ...[
            Row(
              children: [
                Expanded(
                  child: LinearProgressIndicator(
                    value: _shoppingList.completionPercentage / 100,
                    backgroundColor: Colors.grey[300],
                    valueColor: AlwaysStoppedAnimation<Color>(
                      _shoppingList.completionPercentage == 100
                          ? Colors.green
                          : Theme.of(context).colorScheme.primary,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Text(
                  '${_shoppingList.completionPercentage.round()}%',
                  style: const TextStyle(fontWeight: FontWeight.w500),
                ),
              ],
            ),
            const SizedBox(height: 12),
          ],

          // Stats
          Row(
            children: [
              _buildStatChip(
                icon: Icons.list,
                label: '${_shoppingList.totalItems} items',
                color: Colors.blue,
              ),
              if (_shoppingList.checkedItems > 0) ...[
                const SizedBox(width: 8),
                _buildStatChip(
                  icon: Icons.check_circle,
                  label: '${_shoppingList.checkedItems} klaar',
                  color: Colors.green,
                ),
              ],
              const Spacer(),
              if (_shoppingList.estimatedTotal > 0)
                Text(
                  '~€${_shoppingList.estimatedTotal.toStringAsFixed(2)}',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                ),
            ],
          ),

          if (_shoppingList.isShared && _shoppingList.sharedCode != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.green.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.green.withOpacity(0.3)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.share, color: Colors.green, size: 16),
                  const SizedBox(width: 8),
                  Text(
                    'Gedeelde lijst - Code: ${_shoppingList.sharedCode}',
                    style: const TextStyle(
                      color: Colors.green,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const Spacer(),
                  IconButton(
                    onPressed: _shareList,
                    icon: const Icon(Icons.copy, size: 16),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
            ),
          ],
        ],
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

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.shopping_cart_outlined,
              size: 80,
              color: Colors.grey[300],
            ),
            const SizedBox(height: 16),
            const Text(
              'Lijst is nog leeg',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Voeg je eerste item toe!',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _addItem,
              icon: const Icon(Icons.add),
              label: const Text('Item toevoegen'),
            ),
          ],
        ),
      ),
    );
  }

  void _handleMenuAction(String action) {
    switch (action) {
      case 'toggle_checked':
        setState(() => _showCheckedItems = !_showCheckedItems);
        break;
      case 'refresh':
        _refreshList();
        break;
    }
  }

  void _shareList() {
    if (_shoppingList.sharedCode != null) {
      Clipboard.setData(ClipboardData(text: _shoppingList.sharedCode!));
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Code ${_shoppingList.sharedCode!} gekopieerd naar klembord'),
        ),
      );
    }
  }
}

class AddItemDialog extends StatefulWidget {
  const AddItemDialog({super.key});

  @override
  State<AddItemDialog> createState() => _AddItemDialogState();
}

class _AddItemDialogState extends State<AddItemDialog> {
  final _nameController = TextEditingController();
  final _notesController = TextEditingController();
  int _quantity = 1;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Item toevoegen'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: _nameController,
            decoration: const InputDecoration(
              labelText: 'Item naam *',
              hintText: 'Bijv. Melk, Brood, etc.',
            ),
            autofocus: true,
          ),
          const SizedBox(height: 16),
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
          TextField(
            controller: _notesController,
            decoration: const InputDecoration(
              labelText: 'Notities (optioneel)',
              hintText: 'Extra informatie',
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
          onPressed: _nameController.text.trim().isEmpty
              ? null
              : () {
                  Navigator.pop(context, {
                    'name': _nameController.text.trim(),
                    'quantity': _quantity,
                    'notes': _notesController.text.trim().isNotEmpty
                        ? _notesController.text.trim()
                        : null,
                  });
                },
          child: const Text('Toevoegen'),
        ),
      ],
    );
  }

  @override
  void dispose() {
    _nameController.dispose();
    _notesController.dispose();
    super.dispose();
  }
}