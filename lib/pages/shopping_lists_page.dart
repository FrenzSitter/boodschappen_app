import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/shopping_list.dart';
import '../services/shopping_list_service.dart';
import '../widgets/shopping_list_card.dart';
import 'shopping_list_detail_page.dart';

class ShoppingListsPage extends StatefulWidget {
  const ShoppingListsPage({super.key});

  @override
  State<ShoppingListsPage> createState() => _ShoppingListsPageState();
}

class _ShoppingListsPageState extends State<ShoppingListsPage> {
  List<ShoppingList> _shoppingLists = [];
  bool _isLoading = true;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _loadShoppingLists();
  }

  Future<void> _loadShoppingLists() async {
    setState(() => _isLoading = true);
    try {
      final lists = await ShoppingListService.getShoppingLists();
      setState(() {
        _shoppingLists = lists;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fout bij laden van lijsten: $e')),
        );
      }
    }
  }

  List<ShoppingList> get _filteredLists {
    if (_searchQuery.isEmpty) return _shoppingLists;
    return _shoppingLists
        .where((list) => list.name.toLowerCase().contains(_searchQuery.toLowerCase()))
        .toList();
  }

  Future<void> _createNewList() async {
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => const CreateListDialog(),
    );

    if (result != null) {
      final newList = await ShoppingListService.createShoppingList(
        name: result['name'],
        description: result['description'],
        isShared: result['isShared'] ?? false,
      );

      if (newList != null) {
        setState(() {
          _shoppingLists.insert(0, newList);
        });
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Lijst succesvol aangemaakt!')),
          );
        }
      }
    }
  }

  Future<void> _joinSharedList() async {
    final code = await showDialog<String>(
      context: context,
      builder: (context) => const JoinListDialog(),
    );

    if (code != null && code.isNotEmpty) {
      final sharedList = await ShoppingListService.getShoppingListBySharedCode(code);
      
      if (sharedList != null) {
        setState(() {
          // Check if list already exists
          final existingIndex = _shoppingLists.indexWhere((list) => list.id == sharedList.id);
          if (existingIndex >= 0) {
            _shoppingLists[existingIndex] = sharedList;
          } else {
            _shoppingLists.insert(0, sharedList);
          }
        });
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Aangesloten bij lijst "${sharedList.name}"')),
          );
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Lijst niet gevonden. Controleer de code.')),
          );
        }
      }
    }
  }

  Future<void> _deleteList(ShoppingList list) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Lijst verwijderen'),
        content: Text('Weet je zeker dat je "${list.name}" wilt verwijderen?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Annuleren'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Verwijderen'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      final success = await ShoppingListService.deleteShoppingList(list.id);
      if (success) {
        setState(() {
          _shoppingLists.removeWhere((l) => l.id == list.id);
        });
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Lijst verwijderd')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: CustomScrollView(
        slivers: [
          // App Bar
          SliverAppBar(
            expandedHeight: 120,
            floating: true,
            pinned: true,
            backgroundColor: Theme.of(context).colorScheme.primaryContainer,
            flexibleSpace: FlexibleSpaceBar(
              title: const Text(
                'Mijn Lijsten',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              background: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      Theme.of(context).colorScheme.primaryContainer,
                      Theme.of(context).colorScheme.primaryContainer.withOpacity(0.8),
                    ],
                  ),
                ),
                child: SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Spacer(),
                        Row(
                          children: [
                            Text(
                              '${_shoppingLists.length} ${_shoppingLists.length == 1 ? 'lijst' : 'lijsten'}',
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors.grey[600],
                              ),
                            ),
                            const Spacer(),
                            IconButton(
                              onPressed: _joinSharedList,
                              icon: const Icon(Icons.group_add),
                              tooltip: 'Aansluiten bij gedeelde lijst',
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),

          // Search Bar
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: TextField(
                decoration: InputDecoration(
                  hintText: 'Zoek in lijsten...',
                  prefixIcon: const Icon(Icons.search),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  filled: true,
                  fillColor: Colors.grey[50],
                ),
                onChanged: (value) => setState(() => _searchQuery = value),
              ),
            ),
          ),

          // Content
          if (_isLoading)
            const SliverFillRemaining(
              child: Center(child: CircularProgressIndicator()),
            )
          else if (_filteredLists.isEmpty)
            SliverFillRemaining(
              child: _buildEmptyState(),
            )
          else
            SliverPadding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              sliver: SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, index) {
                    final list = _filteredLists[index];
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: ShoppingListCard(
                        shoppingList: list,
                        onTap: () => _navigateToListDetail(list),
                        onDelete: () => _deleteList(list),
                      ),
                    );
                  },
                  childCount: _filteredLists.length,
                ),
              ),
            ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _createNewList,
        icon: const Icon(Icons.add),
        label: const Text('Nieuwe Lijst'),
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
              Icons.shopping_basket_outlined,
              size: 80,
              color: Colors.grey[300],
            ),
            const SizedBox(height: 16),
            Text(
              _searchQuery.isEmpty 
                  ? 'Geen boodschappenlijsten'
                  : 'Geen lijsten gevonden',
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              _searchQuery.isEmpty
                  ? 'Maak je eerste boodschappenlijst aan!'
                  : 'Probeer een andere zoekterm',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[500],
              ),
            ),
            if (_searchQuery.isEmpty) ...[
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: _createNewList,
                icon: const Icon(Icons.add),
                label: const Text('Nieuwe Lijst'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _navigateToListDetail(ShoppingList list) async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ShoppingListDetailPage(shoppingList: list),
      ),
    );

    if (result == true) {
      _loadShoppingLists(); // Refresh the list
    }
  }
}

class CreateListDialog extends StatefulWidget {
  const CreateListDialog({super.key});

  @override
  State<CreateListDialog> createState() => _CreateListDialogState();
}

class _CreateListDialogState extends State<CreateListDialog> {
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  bool _isShared = false;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Nieuwe Boodschappenlijst'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: _nameController,
            decoration: const InputDecoration(
              labelText: 'Naam *',
              hintText: 'Bijv. Weekend boodschappen',
            ),
            autofocus: true,
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _descriptionController,
            decoration: const InputDecoration(
              labelText: 'Beschrijving (optioneel)',
              hintText: 'Extra notities over deze lijst',
            ),
            maxLines: 2,
          ),
          const SizedBox(height: 16),
          CheckboxListTile(
            title: const Text('Lijst delen'),
            subtitle: const Text('Anderen kunnen aansluiten met een code'),
            value: _isShared,
            onChanged: (value) => setState(() => _isShared = value ?? false),
            controlAffinity: ListTileControlAffinity.leading,
            contentPadding: EdgeInsets.zero,
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
                    'description': _descriptionController.text.trim().isNotEmpty
                        ? _descriptionController.text.trim()
                        : null,
                    'isShared': _isShared,
                  });
                },
          child: const Text('Aanmaken'),
        ),
      ],
    );
  }

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }
}

class JoinListDialog extends StatefulWidget {
  const JoinListDialog({super.key});

  @override
  State<JoinListDialog> createState() => _JoinListDialogState();
}

class _JoinListDialogState extends State<JoinListDialog> {
  final _codeController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Aansluiten bij Lijst'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text(
            'Voer de 6-cijferige code in die je van iemand anders hebt gekregen:',
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _codeController,
            decoration: const InputDecoration(
              labelText: 'Lijst Code',
              hintText: 'ABC123',
            ),
            textCapitalization: TextCapitalization.characters,
            inputFormatters: [
              LengthLimitingTextInputFormatter(6),
              FilteringTextInputFormatter.allow(RegExp(r'[A-Za-z0-9]')),
            ],
            autofocus: true,
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Annuleren'),
        ),
        ElevatedButton(
          onPressed: _codeController.text.trim().length < 6
              ? null
              : () => Navigator.pop(context, _codeController.text.trim().toUpperCase()),
          child: const Text('Aansluiten'),
        ),
      ],
    );
  }

  @override
  void dispose() {
    _codeController.dispose();
    super.dispose();
  }
}