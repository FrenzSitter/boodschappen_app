import 'package:flutter/material.dart';
import 'package:animations/animations.dart';
import 'dart:async';
import '../models/product.dart';
import '../services/product_service.dart';
import '../widgets/product_card.dart';
import '../pages/product_comparison_page.dart';

class ModernSearchPage extends StatefulWidget {
  final String? initialQuery;
  final String? initialCategoryId;
  
  const ModernSearchPage({super.key, this.initialQuery, this.initialCategoryId});

  @override
  State<ModernSearchPage> createState() => _ModernSearchPageState();
}

class _ModernSearchPageState extends State<ModernSearchPage>
    with TickerProviderStateMixin {
  final TextEditingController _searchController = TextEditingController();
  final FocusNode _searchFocusNode = FocusNode();
  
  List<ProductWithPrices> _searchResults = [];
  List<Supermarket> _supermarkets = [];
  List<Category> _categories = [];
  List<String> _searchHistory = [];
  List<String> _searchSuggestions = [];
  
  SearchFilters _filters = SearchFilters();
  bool _isLoading = false;
  bool _showFilters = false;
  bool _showSuggestions = false;
  String _searchQuery = '';
  
  Timer? _debounceTimer;
  late AnimationController _filterAnimationController;
  late Animation<double> _filterAnimation;
  
  // Popular searches
  final List<String> _popularSearches = [
    'Melk', 'Brood', 'Eieren', 'Bananen', 'Coca Cola', 'Yoghurt', 
    'Kaas', 'Boter', 'Koffie', 'Thee', 'Suiker', 'Rijst'
  ];

  @override
  void initState() {
    super.initState();
    _loadInitialData();
    _setupAnimations();
    _searchController.addListener(_onSearchChanged);
    _searchFocusNode.addListener(_onFocusChanged);
    
    // Set initial query and category if provided
    if (widget.initialQuery != null && widget.initialQuery!.isNotEmpty) {
      _searchController.text = widget.initialQuery!;
      _searchQuery = widget.initialQuery!;
    }
    
    if (widget.initialCategoryId != null) {
      _filters = _filters.copyWith(categoryId: widget.initialCategoryId);
    }
    
    // Delay the search to let the page load first
    if ((widget.initialQuery != null && widget.initialQuery!.isNotEmpty) || 
        widget.initialCategoryId != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (widget.initialCategoryId != null) {
          // Voor categorie zoeken, voer direct een lege query uit met categorie filter
          _performSearch('');
        } else {
          _performSearch(widget.initialQuery ?? '');
        }
      });
    }
  }

  void _setupAnimations() {
    _filterAnimationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _filterAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _filterAnimationController,
      curve: Curves.easeInOut,
    ));
  }

  Future<void> _loadInitialData() async {
    try {
      final supermarkets = await ProductService.getSupermarkets();
      final categories = await ProductService.getCategories();
      
      setState(() {
        _supermarkets = supermarkets;
        _categories = categories;
      });
    } catch (e) {
      print('Error loading initial data: $e');
    }
  }

  void _onSearchChanged() {
    final query = _searchController.text;
    setState(() {
      _searchQuery = query;
      _showSuggestions = query.isNotEmpty;
    });
    
    if (query.isEmpty) {
      // Als er een categorie filter is, laat de resultaten staan
      if (_filters.categoryId == null) {
        setState(() {
          _searchResults.clear();
          _isLoading = false;
        });
      }
      return;
    }

    // Generate suggestions
    _generateSuggestions(query);
    
    // Debounce search
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 500), () {
      _performSearch(query);
    });
  }

  void _onFocusChanged() {
    setState(() {
      _showSuggestions = _searchFocusNode.hasFocus && _searchQuery.isNotEmpty;
    });
  }

  void _generateSuggestions(String query) {
    final suggestions = <String>[];
    
    // Add exact matches from popular searches
    for (final search in _popularSearches) {
      if (search.toLowerCase().contains(query.toLowerCase())) {
        suggestions.add(search);
      }
    }
    
    // Add category suggestions
    for (final category in _categories) {
      if (category.name.toLowerCase().contains(query.toLowerCase())) {
        suggestions.add('in ${category.name}');
      }
    }
    
    // Add supermarket suggestions
    for (final supermarket in _supermarkets) {
      if (supermarket.name.toLowerCase().contains(query.toLowerCase())) {
        suggestions.add('bij ${supermarket.name}');
      }
    }
    
    setState(() {
      _searchSuggestions = suggestions.take(5).toList();
    });
  }

  Future<void> _performSearch(String query) async {
    print('ModernSearchPage _performSearch called with query: "$query", categoryId: ${_filters.categoryId}');
    
    // Voor categorie zoeken, laten we doorgaan zelfs als query leeg is
    if (query.trim().isEmpty && _filters.categoryId == null) return;
    
    setState(() {
      _isLoading = true;
      _showSuggestions = false;
    });

    try {
      final results = await ProductService.searchProducts(
        filters: _filters.copyWith(query: query.trim()),
        limit: 50,
      );
      
      print('Search results: ${results.length} products found');
      setState(() {
        _searchResults = results;
        _isLoading = false;
      });
      
      // Add to search history
      _addToSearchHistory(query.trim());
    } catch (e) {
      print('Search error: $e');
      setState(() {
        _isLoading = false;
      });
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fout bij zoeken: $e')),
        );
      }
    }
  }

  void _addToSearchHistory(String query) {
    setState(() {
      _searchHistory.remove(query); // Remove if exists
      _searchHistory.insert(0, query); // Add to top
      if (_searchHistory.length > 10) {
        _searchHistory.removeLast(); // Keep only 10 items
      }
    });
  }

  void _selectSuggestion(String suggestion) {
    _searchController.text = suggestion.startsWith('in ') || suggestion.startsWith('bij ') 
        ? suggestion.substring(3)
        : suggestion;
    _searchFocusNode.unfocus();
    _performSearch(_searchController.text);
  }

  void _toggleFilters() {
    setState(() {
      _showFilters = !_showFilters;
    });
    
    if (_showFilters) {
      _filterAnimationController.forward();
    } else {
      _filterAnimationController.reverse();
    }
  }

  void _clearSearch() {
    _searchController.clear();
    setState(() {
      _searchResults.clear();
      _searchQuery = '';
      _showSuggestions = false;
      _isLoading = false;
    });
  }

  void _clearFilters() {
    setState(() {
      _filters = SearchFilters();
      // Clear search results when filters are cleared
      _searchResults.clear();
    });
    if (_searchQuery.isNotEmpty) {
      _performSearch(_searchQuery);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: CustomScrollView(
        slivers: [
          // Modern search app bar
          SliverAppBar(
            expandedHeight: 120,
            floating: true,
            pinned: true,
            elevation: 0,
            backgroundColor: Theme.of(context).colorScheme.surface,
            flexibleSpace: FlexibleSpaceBar(
              background: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      Theme.of(context).colorScheme.primaryContainer,
                      Theme.of(context).colorScheme.primaryContainer.withOpacity(0.7),
                    ],
                  ),
                ),
                child: SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Spacer(),
                        Row(
                          children: [
                            const Text(
                              'Zoeken',
                              style: TextStyle(
                                fontSize: 28,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const Spacer(),
                            if (_searchResults.isNotEmpty) ...[
                              Text(
                                '${_searchResults.length} resultaten',
                                style: TextStyle(
                                  fontSize: 14,
                                  color: Colors.grey[600],
                                ),
                              ),
                            ],
                          ],
                        ),
                        const SizedBox(height: 8),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            bottom: PreferredSize(
              preferredSize: const Size.fromHeight(70),
              child: Container(
                padding: const EdgeInsets.all(16),
                child: _buildSearchBar(),
              ),
            ),
          ),
          
          // Search content
          SliverToBoxAdapter(
            child: _buildSearchContent(),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchBar() {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.1),
                      blurRadius: 10,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: TextField(
                  controller: _searchController,
                  focusNode: _searchFocusNode,
                  decoration: InputDecoration(
                    hintText: 'Zoek naar producten, merken of categorieën...',
                    prefixIcon: const Icon(Icons.search, size: 24),
                    suffixIcon: _searchQuery.isNotEmpty
                        ? Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              if (_isLoading)
                                const Padding(
                                  padding: EdgeInsets.all(12),
                                  child: SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  ),
                                ),
                              IconButton(
                                icon: const Icon(Icons.clear, size: 20),
                                onPressed: _clearSearch,
                              ),
                            ],
                          )
                        : null,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: BorderSide.none,
                    ),
                    filled: true,
                    fillColor: Colors.white,
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 16,
                    ),
                  ),
                  onSubmitted: _performSearch,
                ),
              ),
            ),
            const SizedBox(width: 12),
            
            // Filter button
            Container(
              decoration: BoxDecoration(
                color: _showFilters 
                    ? Theme.of(context).colorScheme.primary
                    : Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.1),
                    blurRadius: 10,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: IconButton(
                onPressed: _toggleFilters,
                icon: Icon(
                  Icons.tune,
                  color: _showFilters 
                      ? Theme.of(context).colorScheme.onPrimary
                      : Theme.of(context).colorScheme.primary,
                ),
                tooltip: 'Filters',
              ),
            ),
          ],
        ),
        
        // Active filters display
        if (_hasActiveFilters()) ...[
          const SizedBox(height: 12),
          _buildActiveFiltersRow(),
        ],
      ],
    );
  }

  Widget _buildActiveFiltersRow() {
    final activeFilters = <Widget>[];
    
    if (_filters.supermarketIds?.isNotEmpty == true) {
      for (final id in _filters.supermarketIds!) {
        final supermarket = _supermarkets.firstWhere((s) => s.slug == id);
        activeFilters.add(_buildFilterChip(supermarket.name, () {
          setState(() {
            _filters = _filters.copyWith(
              supermarketIds: _filters.supermarketIds!..remove(id),
            );
          });
        }));
      }
    }
    
    if (_filters.categoryId != null) {
      try {
        final category = _categories.firstWhere((c) => c.id == _filters.categoryId);
        activeFilters.add(_buildFilterChip(category.name, () {
          setState(() {
            _filters = _filters.copyWith(categoryId: null);
            _searchResults.clear();
          });
          // Voer opnieuw een zoekopdracht uit zonder categorie filter
          if (_searchQuery.isNotEmpty) {
            _performSearch(_searchQuery);
          }
        }));
      } catch (e) {
        // Category not found in list, show placeholder
        activeFilters.add(_buildFilterChip('Categorie geselecteerd', () {
          setState(() {
            _filters = _filters.copyWith(categoryId: null);
            _searchResults.clear();
          });
          // Voer opnieuw een zoekopdracht uit zonder categorie filter
          if (_searchQuery.isNotEmpty) {
            _performSearch(_searchQuery);
          }
        }));
      }
    }
    
    if (_filters.minPrice != null || _filters.maxPrice != null) {
      final priceText = _filters.minPrice != null && _filters.maxPrice != null
          ? '€${_filters.minPrice!.toStringAsFixed(0)} - €${_filters.maxPrice!.toStringAsFixed(0)}'
          : _filters.minPrice != null
              ? '> €${_filters.minPrice!.toStringAsFixed(0)}'
              : '< €${_filters.maxPrice!.toStringAsFixed(0)}';
      activeFilters.add(_buildFilterChip(priceText, () {
        setState(() {
          _filters = _filters.copyWith(minPrice: null, maxPrice: null);
        });
      }));
    }
    
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          ...activeFilters,
          if (activeFilters.isNotEmpty) ...[
            const SizedBox(width: 8),
            TextButton.icon(
              onPressed: _clearFilters,
              icon: const Icon(Icons.clear_all, size: 16),
              label: const Text('Alles wissen'),
              style: TextButton.styleFrom(
                foregroundColor: Colors.grey[600],
                padding: const EdgeInsets.symmetric(horizontal: 8),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildFilterChip(String label, VoidCallback onRemove) {
    return Container(
      margin: const EdgeInsets.only(right: 8),
      child: Chip(
        label: Text(label),
        deleteIcon: const Icon(Icons.close, size: 16),
        onDeleted: onRemove,
        backgroundColor: Theme.of(context).colorScheme.primaryContainer,
        labelStyle: TextStyle(
          color: Theme.of(context).colorScheme.onPrimaryContainer,
          fontSize: 12,
        ),
      ),
    );
  }

  Widget _buildSearchContent() {
    return Column(
      children: [
        // Suggestions overlay
        if (_showSuggestions) _buildSuggestionsOverlay(),
        
        // Filters panel
        if (_showFilters) _buildFiltersPanel(),
        
        // Search results or empty state
        if (!_showSuggestions) _buildMainContent(),
      ],
    );
  }

  Widget _buildSuggestionsOverlay() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Search suggestions
          if (_searchSuggestions.isNotEmpty) ...[
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'Suggesties',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: Colors.grey,
                ),
              ),
            ),
            ...(_searchSuggestions.map((suggestion) => ListTile(
              leading: Icon(
                suggestion.startsWith('in ') 
                    ? Icons.category
                    : suggestion.startsWith('bij ')
                        ? Icons.store
                        : Icons.search,
                size: 20,
                color: Colors.grey[600],
              ),
              title: RichText(
                text: TextSpan(
                  children: _highlightMatches(suggestion, _searchQuery),
                  style: const TextStyle(
                    fontSize: 16,
                    color: Colors.black,
                  ),
                ),
              ),
              onTap: () => _selectSuggestion(suggestion),
              dense: true,
            ))),
          ],
          
          // Recent searches
          if (_searchHistory.isNotEmpty && _searchQuery.isEmpty) ...[
            const Divider(height: 1),
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'Recente zoekopdrachten',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: Colors.grey,
                ),
              ),
            ),
            ...(_searchHistory.take(5).map((search) => ListTile(
              leading: Icon(
                Icons.history,
                size: 20,
                color: Colors.grey[600],
              ),
              title: Text(search),
              trailing: IconButton(
                icon: const Icon(Icons.close, size: 16),
                onPressed: () {
                  setState(() {
                    _searchHistory.remove(search);
                  });
                },
              ),
              onTap: () => _selectSuggestion(search),
              dense: true,
            ))),
          ],
          
          // Popular searches
          if (_searchQuery.isEmpty) ...[
            const Divider(height: 1),
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'Populaire zoekopdrachten',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: Colors.grey,
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _popularSearches.take(8).map((search) => ActionChip(
                  label: Text(search),
                  onPressed: () => _selectSuggestion(search),
                  backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                  labelStyle: TextStyle(
                    color: Theme.of(context).colorScheme.onPrimaryContainer,
                    fontSize: 12,
                  ),
                )).toList(),
              ),
            ),
            const SizedBox(height: 16),
          ],
        ],
      ),
    );
  }

  List<TextSpan> _highlightMatches(String text, String query) {
    if (query.isEmpty) return [TextSpan(text: text)];
    
    final spans = <TextSpan>[];
    final lowerText = text.toLowerCase();
    final lowerQuery = query.toLowerCase();
    
    int start = 0;
    int index = lowerText.indexOf(lowerQuery);
    
    while (index != -1) {
      if (index > start) {
        spans.add(TextSpan(text: text.substring(start, index)));
      }
      spans.add(TextSpan(
        text: text.substring(index, index + query.length),
        style: TextStyle(
          fontWeight: FontWeight.bold,
          color: Theme.of(context).colorScheme.primary,
        ),
      ));
      start = index + query.length;
      index = lowerText.indexOf(lowerQuery, start);
    }
    
    if (start < text.length) {
      spans.add(TextSpan(text: text.substring(start)));
    }
    
    return spans;
  }

  Widget _buildFiltersPanel() {
    return FadeTransition(
      opacity: _filterAnimation,
      child: SizeTransition(
        sizeFactor: _filterAnimation,
        child: Container(
          margin: const EdgeInsets.all(16),
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 10,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Text(
                    'Filters',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Spacer(),
                  TextButton(
                    onPressed: _clearFilters,
                    child: const Text('Wissen'),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              
              // Supermarket filter
              if (_supermarkets.isNotEmpty) ...[
                const Text(
                  'Supermarkten',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: _supermarkets.map((supermarket) {
                    final isSelected = _filters.supermarketIds?.contains(supermarket.slug) ?? false;
                    return FilterChip(
                      label: Text(supermarket.name),
                      selected: isSelected,
                      onSelected: (selected) {
                        setState(() {
                          if (selected) {
                            final currentIds = _filters.supermarketIds ?? [];
                            _filters = _filters.copyWith(
                              supermarketIds: [...currentIds, supermarket.slug],
                            );
                          } else {
                            final currentIds = _filters.supermarketIds ?? [];
                            _filters = _filters.copyWith(
                              supermarketIds: currentIds.where((id) => id != supermarket.slug).toList(),
                            );
                          }
                        });
                      },
                      backgroundColor: Colors.grey[100],
                      selectedColor: Theme.of(context).colorScheme.primaryContainer,
                    );
                  }).toList(),
                ),
                const SizedBox(height: 20),
              ],
              
              // Category filter
              if (_categories.isNotEmpty) ...[
                const Text(
                  'Categorie',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  value: _filters.categoryId,
                  decoration: InputDecoration(
                    hintText: 'Selecteer categorie',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    filled: true,
                    fillColor: Colors.grey[50],
                  ),
                  items: [
                    const DropdownMenuItem<String>(
                      value: null,
                      child: Text('Alle categorieën'),
                    ),
                    ..._categories.map((category) => DropdownMenuItem<String>(
                      value: category.id,
                      child: Text(category.name),
                    )),
                  ],
                  onChanged: (value) {
                    setState(() {
                      _filters = _filters.copyWith(categoryId: value);
                    });
                  },
                ),
                const SizedBox(height: 20),
              ],
              
              // Price range filter
              const Text(
                'Prijsbereik',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      decoration: InputDecoration(
                        hintText: 'Min prijs',
                        prefixText: '€ ',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        filled: true,
                        fillColor: Colors.grey[50],
                      ),
                      keyboardType: TextInputType.number,
                      onChanged: (value) {
                        final price = double.tryParse(value);
                        setState(() {
                          _filters = _filters.copyWith(minPrice: price);
                        });
                      },
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: TextFormField(
                      decoration: InputDecoration(
                        hintText: 'Max prijs',
                        prefixText: '€ ',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        filled: true,
                        fillColor: Colors.grey[50],
                      ),
                      keyboardType: TextInputType.number,
                      onChanged: (value) {
                        final price = double.tryParse(value);
                        setState(() {
                          _filters = _filters.copyWith(maxPrice: price);
                        });
                      },
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              
              // Special filters
              const Text(
                'Speciale filters',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  FilterChip(
                    label: const Text('Alleen aanbiedingen'),
                    selected: _filters.isOnSale ?? false,
                    onSelected: (selected) {
                      setState(() {
                        _filters = _filters.copyWith(isOnSale: selected ? true : null);
                      });
                    },
                    backgroundColor: Colors.grey[100],
                    selectedColor: Colors.orange.withOpacity(0.3),
                  ),
                  FilterChip(
                    label: const Text('Biologisch'),
                    selected: _filters.isOrganic ?? false,
                    onSelected: (selected) {
                      setState(() {
                        _filters = _filters.copyWith(isOrganic: selected ? true : null);
                      });
                    },
                    backgroundColor: Colors.grey[100],
                    selectedColor: Colors.green.withOpacity(0.3),
                  ),
                ],
              ),
              
              const SizedBox(height: 20),
              
              // Apply filters button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    if (_searchQuery.isNotEmpty) {
                      _performSearch(_searchQuery);
                    }
                    _toggleFilters();
                  },
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.all(16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: const Text('Filters toepassen'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMainContent() {
    if (_isLoading) {
      return const Padding(
        padding: EdgeInsets.all(32),
        child: Center(child: CircularProgressIndicator()),
      );
    }
    
    // Show empty search state only if no query AND no category filter
    if (_searchQuery.isEmpty && _filters.categoryId == null) {
      return _buildEmptySearchState();
    }
    
    if (_searchResults.isEmpty) {
      return _buildNoResultsState();
    }
    
    return _buildSearchResults();
  }

  Widget _buildEmptySearchState() {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        children: [
          Icon(
            Icons.search,
            size: 80,
            color: Colors.grey[300],
          ),
          const SizedBox(height: 16),
          Text(
            'Begin met typen om te zoeken',
            style: TextStyle(
              fontSize: 18,
              color: Colors.grey[600],
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Zoek naar producten, merken of categorieën\nom de beste prijzen te vinden',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[500],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNoResultsState() {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        children: [
          Icon(
            Icons.search_off,
            size: 80,
            color: Colors.grey[300],
          ),
          const SizedBox(height: 16),
          Text(
            'Geen resultaten gevonden',
            style: TextStyle(
              fontSize: 18,
              color: Colors.grey[600],
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Probeer andere zoektermen of\npas je filters aan',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[500],
            ),
          ),
          const SizedBox(height: 24),
          OutlinedButton.icon(
            onPressed: _clearFilters,
            icon: const Icon(Icons.clear_all),
            label: const Text('Filters wissen'),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchResults() {
    return Column(
      children: [
        // Results header
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: [
              Text(
                '${_searchResults.length} ${_searchResults.length == 1 ? 'product' : 'producten'} gevonden',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const Spacer(),
              // Sort options could go here
            ],
          ),
        ),
        
        // Results grid
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          padding: const EdgeInsets.symmetric(horizontal: 8),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            childAspectRatio: 0.7,
            crossAxisSpacing: 8,
            mainAxisSpacing: 8,
          ),
          itemCount: _searchResults.length,
          itemBuilder: (context, index) {
            return ProductCard(
              productWithPrices: _searchResults[index],
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (context) => ProductComparisonPage(
                      productWithPrices: _searchResults[index],
                    ),
                  ),
                );
              },
            );
          },
        ),
        
        const SizedBox(height: 20),
      ],
    );
  }

  bool _hasActiveFilters() {
    return (_filters.supermarketIds?.isNotEmpty == true) ||
           _filters.categoryId != null ||
           _filters.minPrice != null ||
           _filters.maxPrice != null ||
           (_filters.isOnSale == true) ||
           (_filters.isOrganic == true);
  }

  @override
  void dispose() {
    _searchController.dispose();
    _searchFocusNode.dispose();
    _debounceTimer?.cancel();
    _filterAnimationController.dispose();
    super.dispose();
  }
}