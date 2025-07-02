import 'package:flutter/material.dart';
import 'config/supabase_config.dart';
import 'models/product.dart';
import 'services/product_service.dart';
import 'widgets/product_card.dart';
import 'widgets/barcode_scanner.dart';
import 'pages/product_comparison_page.dart';
import 'pages/modern_search_page.dart';
import 'pages/shopping_lists_page.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SupabaseConfig.initialize();
  runApp(const BoodschappenApp());
}

class BoodschappenApp extends StatelessWidget {
  const BoodschappenApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Boodschappen App',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFFF6B35),
          brightness: Brightness.light,
        ).copyWith(
          primary: const Color(0xFFFF6B35),
          secondary: const Color(0xFF004D40),
          tertiary: const Color(0xFFFFA726),
          surface: Colors.white,
          background: const Color(0xFFF5F5F5),
        ),
      ),
      home: const MainNavigationPage(),
    );
  }
}

class MainNavigationPage extends StatefulWidget {
  const MainNavigationPage({super.key});

  @override
  State<MainNavigationPage> createState() => _MainNavigationPageState();
}

class _MainNavigationPageState extends State<MainNavigationPage> {
  int _currentIndex = 0;
  String? _searchQuery;
  String? _searchCategoryId;

  late List<Widget> _pages;
  
  @override
  void initState() {
    super.initState();
    _updatePages();
  }
  
  void _updatePages() {
    _pages = [
      HomePage(onSearch: _handleSearch),
      ModernSearchPage(
        key: ValueKey('$_searchQuery-$_searchCategoryId'), 
        initialQuery: _searchQuery,
        initialCategoryId: _searchCategoryId,
      ),
      const ScannerPage(),
      const ShoppingListsPage(),
    ];
  }
  
  void _handleSearch(String query, {String? categoryId}) {
    print('_handleSearch called with query: $query, categoryId: $categoryId');
    setState(() {
      _searchQuery = query;
      _searchCategoryId = categoryId;
      _currentIndex = 1; // Switch to search tab
      _updatePages(); // Rebuild pages with new search query
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _pages,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() {
            _currentIndex = index;
            // Clear search query when navigating away from search page
            if (index != 1) {
              _searchQuery = null;
              _searchCategoryId = null;
              _updatePages();
            }
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.search_outlined),
            selectedIcon: Icon(Icons.search),
            label: 'Zoeken',
          ),
          NavigationDestination(
            icon: Icon(Icons.qr_code_scanner_outlined),
            selectedIcon: Icon(Icons.qr_code_scanner),
            label: 'Scanner',
          ),
          NavigationDestination(
            icon: Icon(Icons.list_outlined),
            selectedIcon: Icon(Icons.list),
            label: 'Lijsten',
          ),
        ],
      ),
    );
  }
}

class HomePage extends StatefulWidget {
  final Function(String, {String? categoryId}) onSearch;
  
  const HomePage({super.key, required this.onSearch});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final TextEditingController _searchController = TextEditingController();
  List<ProductWithPrices> _featuredDeals = [];
  List<ProductWithPrices> _popularProducts = [];
  List<Supermarket> _supermarkets = [];
  List<Category> _categories = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadHomeData();
  }

  Future<void> _loadHomeData() async {
    try {
      final deals = await ProductService.getPopularProducts(limit: 6);
      final popular = await ProductService.getPopularProducts(limit: 8);
      final supermarkets = await ProductService.getSupermarkets();
      final categories = await ProductService.getCategories();
      
      setState(() {
        _featuredDeals = deals;
        _popularProducts = popular;
        _supermarkets = supermarkets.take(6).toList();
        _categories = categories.where((c) => c.parentId == null).take(8).toList();
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      print('Error loading home data: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: RefreshIndicator(
        onRefresh: _loadHomeData,
        child: CustomScrollView(
          slivers: [
            // App Bar with gradient
            SliverAppBar(
              expandedHeight: 120,
              floating: false,
              pinned: true,
              elevation: 0,
              flexibleSpace: FlexibleSpaceBar(
                background: Container(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [
                        Theme.of(context).colorScheme.primary,
                        Theme.of(context).colorScheme.primaryContainer,
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
                          Text(
                            'Boodschappen Vergelijker',
                            style: TextStyle(
                              fontSize: 24,
                              fontWeight: FontWeight.bold,
                              color: Theme.of(context).colorScheme.onPrimary,
                            ),
                          ),
                          Text(
                            'Vind de beste prijzen in Nederland',
                            style: TextStyle(
                              fontSize: 14,
                              color: Theme.of(context).colorScheme.onPrimary.withOpacity(0.8),
                            ),
                          ),
                          const SizedBox(height: 8),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
            
            // Search and Scanner Section
            SliverToBoxAdapter(
              child: _buildSearchSection(),
            ),
            
            // Stats Section
            SliverToBoxAdapter(
              child: _buildStatsSection(),
            ),
            
            // Quick Categories
            SliverToBoxAdapter(
              child: _buildCategoriesSection(),
            ),
            
            // Featured Deals
            SliverToBoxAdapter(
              child: _buildFeaturedDealsSection(),
            ),
            
            // Supermarket Shortcuts
            SliverToBoxAdapter(
              child: _buildSupermarketsSection(),
            ),
            
            // Popular Products
            SliverToBoxAdapter(
              child: _buildPopularProductsSection(),
            ),
            
            // Bottom padding
            const SliverToBoxAdapter(
              child: SizedBox(height: 20),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSearchSection() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          // Search bar with scanner button
          Row(
            children: [
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.1),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: TextField(
                    controller: _searchController,
                    decoration: const InputDecoration(
                      hintText: 'Zoek naar producten...',
                      prefixIcon: Icon(Icons.search),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.all(Radius.circular(12)),
                        borderSide: BorderSide.none,
                      ),
                      filled: true,
                      fillColor: Colors.white,
                    ),
                    onSubmitted: _performSearch,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              
              // Scanner button
              Container(
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.secondary,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.1),
                      blurRadius: 8,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: IconButton(
                  onPressed: _openScanner,
                  icon: Icon(
                    Icons.qr_code_scanner,
                    color: Theme.of(context).colorScheme.onSecondary,
                    size: 28,
                  ),
                  tooltip: 'Scan barcode',
                ),
              ),
            ],
          ),
          
          // Quick category buttons
          const SizedBox(height: 12),
          if (_categories.isNotEmpty) ...[
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _categories.take(6).map((category) => 
                  _buildCategoryChip(category)
                ).toList(),
              ),
            ),
          ] else ...[
            // Fallback categories while loading
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  _buildQuickSearchChip('Zuivel & eieren'),
                  _buildQuickSearchChip('Brood & gebak'),
                  _buildQuickSearchChip('Groente & fruit'),
                  _buildQuickSearchChip('Dranken'),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildCategoryChip(Category category) {
    return Container(
      margin: const EdgeInsets.only(right: 8),
      child: ActionChip(
        avatar: Icon(
          _getCategoryIcon(category.iconName),
          size: 16,
          color: Theme.of(context).colorScheme.onPrimaryContainer,
        ),
        label: Text(category.name),
        onPressed: () => _searchByCategory(category),
        backgroundColor: Theme.of(context).colorScheme.primaryContainer,
        labelStyle: TextStyle(
          color: Theme.of(context).colorScheme.onPrimaryContainer,
          fontSize: 12,
        ),
      ),
    );
  }

  Widget _buildQuickSearchChip(String query) {
    return Container(
      margin: const EdgeInsets.only(right: 8),
      child: ActionChip(
        label: Text(query),
        onPressed: () => _performSearch(query),
        backgroundColor: Theme.of(context).colorScheme.primaryContainer,
        labelStyle: TextStyle(
          color: Theme.of(context).colorScheme.onPrimaryContainer,
        ),
      ),
    );
  }

  Widget _buildStatsSection() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
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
      child: Row(
        children: [
          Expanded(
            child: _buildStatItem(
              '95k+',
              'Producten',
              Icons.inventory,
              Colors.blue,
            ),
          ),
          Container(
            width: 1,
            height: 40,
            color: Colors.grey[300],
          ),
          Expanded(
            child: _buildStatItem(
              '10',
              'Supermarkten',
              Icons.store,
              Colors.green,
            ),
          ),
          Container(
            width: 1,
            height: 40,
            color: Colors.grey[300],
          ),
          Expanded(
            child: _buildStatItem(
              '€50+',
              'Gem. besparing',
              Icons.savings,
              Colors.orange,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem(String value, String label, IconData icon, Color color) {
    return Column(
      children: [
        Icon(icon, color: color, size: 24),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildCategoriesSection() {
    if (_isLoading || _categories.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.fromLTRB(16, 24, 16, 12),
          child: Text(
            'Categorieën',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 4,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              childAspectRatio: 1,
            ),
            itemCount: _categories.length,
            itemBuilder: (context, index) {
              final category = _categories[index];
              return _buildCategoryCard(category);
            },
          ),
        ),
      ],
    );
  }

  Widget _buildCategoryCard(Category category) {
    return GestureDetector(
      onTap: () => _searchByCategory(category),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              _getCategoryIcon(category.iconName),
              size: 28,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(height: 8),
            Text(
              category.name,
              style: const TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w500,
              ),
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeaturedDealsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 24, 16, 12),
          child: Row(
            children: [
              const Icon(Icons.local_fire_department, color: Colors.red, size: 24),
              const SizedBox(width: 8),
              const Text(
                'Aanbiedingen',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const Spacer(),
              TextButton(
                onPressed: _viewAllDeals,
                child: const Text('Alles bekijken'),
              ),
            ],
          ),
        ),
        
        if (_isLoading) ...[
          const Center(child: CircularProgressIndicator()),
        ] else if (_featuredDeals.isEmpty) ...[
          const Padding(
            padding: EdgeInsets.all(32),
            child: Center(
              child: Text(
                'Geen aanbiedingen beschikbaar',
                style: TextStyle(color: Colors.grey),
              ),
            ),
          ),
        ] else ...[
          SizedBox(
            height: 280,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: _featuredDeals.length,
              itemBuilder: (context, index) {
                return SizedBox(
                  width: 160,
                  child: ProductCard(productWithPrices: _featuredDeals[index]),
                );
              },
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildSupermarketsSection() {
    if (_isLoading || _supermarkets.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.fromLTRB(16, 24, 16, 12),
          child: Text(
            'Supermarkten',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        
        SizedBox(
          height: 80,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            itemCount: _supermarkets.length,
            itemBuilder: (context, index) {
              final supermarket = _supermarkets[index];
              return _buildSupermarketCard(supermarket);
            },
          ),
        ),
      ],
    );
  }

  Widget _buildSupermarketCard(Supermarket supermarket) {
    return Container(
      width: 70,
      margin: const EdgeInsets.symmetric(horizontal: 4),
      child: GestureDetector(
        onTap: () => _searchBySupermarket(supermarket),
        child: Column(
          children: [
            Container(
              width: 50,
              height: 50,
              decoration: BoxDecoration(
                color: _getSupermarketColor(supermarket.slug),
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.1),
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Center(
                child: Text(
                  _getSupermarketInitials(supermarket.name),
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 6),
            Text(
              supermarket.name,
              style: const TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w500,
              ),
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPopularProductsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 24, 16, 12),
          child: Row(
            children: [
              const Icon(Icons.trending_up, color: Colors.blue, size: 24),
              const SizedBox(width: 8),
              const Text(
                'Populaire producten',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const Spacer(),
              TextButton(
                onPressed: _viewPopularProducts,
                child: const Text('Alles bekijken'),
              ),
            ],
          ),
        ),
        
        if (_isLoading) ...[
          const Center(child: CircularProgressIndicator()),
        ] else if (_popularProducts.isEmpty) ...[
          const Padding(
            padding: EdgeInsets.all(32),
            child: Center(
              child: Text(
                'Geen populaire producten beschikbaar',
                style: TextStyle(color: Colors.grey),
              ),
            ),
          ),
        ] else ...[
          SizedBox(
            height: 280,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: _popularProducts.length,
              itemBuilder: (context, index) {
                return SizedBox(
                  width: 160,
                  child: ProductCard(productWithPrices: _popularProducts[index]),
                );
              },
            ),
          ),
        ],
      ],
    );
  }

  IconData _getCategoryIcon(String? iconName) {
    switch (iconName) {
      case 'local_florist':
        return Icons.local_florist;
      case 'set_meal':
        return Icons.set_meal;
      case 'egg':
        return Icons.egg;
      case 'bakery_dining':
        return Icons.bakery_dining;
      case 'eco':
        return Icons.eco;
      case 'ac_unit':
        return Icons.ac_unit;
      case 'inventory_2':
        return Icons.inventory_2;
      case 'local_drink':
        return Icons.local_drink;
      case 'child_care':
        return Icons.child_care;
      case 'health_and_safety':
        return Icons.health_and_safety;
      case 'cleaning_services':
        return Icons.cleaning_services;
      case 'pets':
        return Icons.pets;
      default:
        return Icons.category;
    }
  }

  Color _getSupermarketColor(String slug) {
    switch (slug.toLowerCase()) {
      case 'albert-heijn':
        return const Color(0xFF0051A5);
      case 'jumbo':
        return const Color(0xFFFFD800);
      case 'lidl':
        return const Color(0xFF0050AA);
      case 'aldi':
        return const Color(0xFF009CDA);
      case 'plus':
        return const Color(0xFFE30613);
      case 'coop':
        return const Color(0xFFE30613);
      case 'spar':
        return const Color(0xFF009639);
      case 'vomar':
        return const Color(0xFFE30613);
      case 'hoogvliet':
        return const Color(0xFFE30613);
      case 'jan-linders':
        return const Color(0xFF0066CC);
      default:
        return Colors.grey;
    }
  }

  String _getSupermarketInitials(String name) {
    final words = name.split(' ');
    if (words.length >= 2) {
      return '${words[0][0]}${words[1][0]}'.toUpperCase();
    }
    return name.length >= 2 ? name.substring(0, 2).toUpperCase() : name.toUpperCase();
  }

  void _performSearch(String query) {
    print('_performSearch called with query: $query');
    if (query.trim().isEmpty) return;
    
    // Use the callback to perform search
    widget.onSearch(query.trim());
    
    // Clear the search field
    _searchController.clear();
  }

  void _openScanner() {
    // Navigate to scanner tab
    if (context.findAncestorStateOfType<_MainNavigationPageState>() != null) {
      final navState = context.findAncestorStateOfType<_MainNavigationPageState>()!;
      navState.setState(() {
        navState._currentIndex = 2; // Switch to scanner tab
      });
    }
  }

  void _searchByCategory(Category category) {
    // Navigate to search with category filter - use empty query for category searches
    widget.onSearch('', categoryId: category.id);
  }

  void _searchBySupermarket(Supermarket supermarket) {
    // Navigate to search with supermarket filter
    widget.onSearch(supermarket.name);
  }

  void _viewAllDeals() {
    widget.onSearch('aanbiedingen');
  }

  void _viewPopularProducts() {
    widget.onSearch('populair');
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }
}

class ScannerPage extends StatefulWidget {
  const ScannerPage({super.key});

  @override
  State<ScannerPage> createState() => _ScannerPageState();
}

class _ScannerPageState extends State<ScannerPage> {
  bool _isCameraActive = false;
  bool _isSearching = false;
  ProductWithPrices? _scannedProduct;
  String? _lastScannedBarcode;
  String? _errorMessage;

  @override
  Widget build(BuildContext context) {
    if (_isCameraActive) {
      return Scaffold(
        body: BarcodeScanner(
          onBarcodeDetected: _onBarcodeDetected,
          overlayText: 'Richt de camera op een productbarcode',
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Scanner'),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // Scanner intro
            if (_scannedProduct == null && _errorMessage == null) ...[
              const SizedBox(height: 40),
              Container(
                padding: const EdgeInsets.all(32),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(24),
                ),
                child: const Column(
                  children: [
                    Icon(
                      Icons.qr_code_scanner,
                      size: 80,
                      color: Colors.orange,
                    ),
                    SizedBox(height: 16),
                    Text(
                      'Scan een barcode',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    SizedBox(height: 8),
                    Text(
                      'Scan de barcode van een product om prijzen te vergelijken tussen Nederlandse supermarkten',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 16,
                        color: Colors.grey,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),
              
              // Start scanning button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _startScanning,
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('Camera openen'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.all(16),
                    textStyle: const TextStyle(fontSize: 18),
                  ),
                ),
              ),
              
              const SizedBox(height: 16),
              
              // Manual input option
              OutlinedButton.icon(
                onPressed: _showManualBarcodeDialog,
                icon: const Icon(Icons.keyboard),
                label: const Text('Barcode handmatig invoeren'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.all(16),
                ),
              ),
            ],
            
            // Loading state
            if (_isSearching) ...[
              const SizedBox(height: 40),
              const CircularProgressIndicator(),
              const SizedBox(height: 16),
              Text(
                'Zoeken naar product...',
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.grey[600],
                ),
              ),
              if (_lastScannedBarcode != null) ...[
                const SizedBox(height: 8),
                Text(
                  'Barcode: $_lastScannedBarcode',
                  style: const TextStyle(
                    fontSize: 12,
                    fontFamily: 'monospace',
                  ),
                ),
              ],
            ],
            
            // Error state
            if (_errorMessage != null) ...[
              const SizedBox(height: 20),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.red.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.red.withOpacity(0.3)),
                ),
                child: Column(
                  children: [
                    const Icon(
                      Icons.error_outline,
                      color: Colors.red,
                      size: 48,
                    ),
                    const SizedBox(height: 12),
                    Text(
                      _errorMessage!,
                      style: const TextStyle(
                        fontSize: 16,
                        color: Colors.red,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    if (_lastScannedBarcode != null) ...[
                      const SizedBox(height: 8),
                      Text(
                        'Barcode: $_lastScannedBarcode',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[600],
                          fontFamily: 'monospace',
                        ),
                      ),
                    ],
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        ElevatedButton(
                          onPressed: _startScanning,
                          child: const Text('Opnieuw scannen'),
                        ),
                        const SizedBox(width: 12),
                        OutlinedButton(
                          onPressed: _clearResults,
                          child: const Text('Wissen'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
            
            // Product result
            if (_scannedProduct != null) ...[
              const SizedBox(height: 20),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.green.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.green.withOpacity(0.3)),
                ),
                child: Column(
                  children: [
                    const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.check_circle,
                          color: Colors.green,
                          size: 24,
                        ),
                        SizedBox(width: 8),
                        Text(
                          'Product gevonden!',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Colors.green,
                          ),
                        ),
                      ],
                    ),
                    if (_lastScannedBarcode != null) ...[
                      const SizedBox(height: 8),
                      Text(
                        'Barcode: $_lastScannedBarcode',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[600],
                          fontFamily: 'monospace',
                        ),
                      ),
                    ],
                    const SizedBox(height: 16),
                    
                    // Product details
                    ProductDetailCard(productWithPrices: _scannedProduct!),
                    
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: ElevatedButton(
                            onPressed: _startScanning,
                            child: const Text('Nieuwe scan'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () {
                              // Navigate to search page with this product
                              Navigator.of(context).pushReplacement(
                                MaterialPageRoute(
                                  builder: (context) => const MainNavigationPage(),
                                ),
                              );
                              // Switch to search tab
                              if (context.findAncestorStateOfType<_MainNavigationPageState>() != null) {
                                context.findAncestorStateOfType<_MainNavigationPageState>()!.setState(() {
                                  context.findAncestorStateOfType<_MainNavigationPageState>()!._currentIndex = 1;
                                });
                              }
                            },
                            child: const Text('Naar zoeken'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
            
            // How it works section
            if (_scannedProduct == null && _errorMessage == null && !_isSearching) ...[
              const SizedBox(height: 40),
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.grey.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Hoe werkt het?',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),
                    _buildHowItWorksStep(
                      1,
                      'Scan de barcode',
                      'Richt je camera op de barcode van het product',
                      Icons.qr_code_scanner,
                    ),
                    const SizedBox(height: 12),
                    _buildHowItWorksStep(
                      2,
                      'Automatische herkenning',
                      'De app herkent het product automatisch',
                      Icons.auto_awesome,
                    ),
                    const SizedBox(height: 12),
                    _buildHowItWorksStep(
                      3,
                      'Prijsvergelijking',
                      'Zie direct de prijzen bij alle supermarkten',
                      Icons.compare_arrows,
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildHowItWorksStep(int step, String title, String description, IconData icon) {
    return Row(
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.primary,
            shape: BoxShape.circle,
          ),
          child: Center(
            child: Text(
              step.toString(),
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
        const SizedBox(width: 16),
        Icon(
          icon,
          color: Theme.of(context).colorScheme.primary,
          size: 24,
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
              Text(
                description,
                style: TextStyle(
                  color: Colors.grey[600],
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _startScanning() {
    setState(() {
      _isCameraActive = true;
      _errorMessage = null;
      _scannedProduct = null;
    });
  }

  void _onBarcodeDetected(String barcode) {
    setState(() {
      _isCameraActive = false;
      _isSearching = true;
      _lastScannedBarcode = barcode;
      _errorMessage = null;
      _scannedProduct = null;
    });

    _searchProductByBarcode(barcode);
  }

  Future<void> _searchProductByBarcode(String barcode) async {
    try {
      final product = await ProductService.searchProductByBarcode(barcode);
      
      setState(() {
        _isSearching = false;
        if (product != null) {
          _scannedProduct = product;
          _errorMessage = null;
        } else {
          _errorMessage = 'Product niet gevonden in onze database.\nProbeer een ander product of zoek handmatig.';
          _scannedProduct = null;
        }
      });
    } catch (e) {
      setState(() {
        _isSearching = false;
        _errorMessage = 'Fout bij zoeken naar product.\nControleer je internetverbinding en probeer opnieuw.';
        _scannedProduct = null;
      });
      
      print('Error searching for product: $e');
    }
  }

  void _showManualBarcodeDialog() {
    final TextEditingController barcodeController = TextEditingController();
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Barcode invoeren'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Voer de barcode van het product handmatig in:'),
            const SizedBox(height: 16),
            TextField(
              controller: barcodeController,
              decoration: const InputDecoration(
                labelText: 'Barcode',
                hintText: 'bijv. 8718906115892',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.number,
              autofocus: true,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Annuleren'),
          ),
          ElevatedButton(
            onPressed: () {
              final barcode = barcodeController.text.trim();
              if (barcode.isNotEmpty) {
                Navigator.of(context).pop();
                _onBarcodeDetected(barcode);
              }
            },
            child: const Text('Zoeken'),
          ),
        ],
      ),
    );
  }

  void _clearResults() {
    setState(() {
      _scannedProduct = null;
      _errorMessage = null;
      _lastScannedBarcode = null;
      _isSearching = false;
      _isCameraActive = false;
    });
  }
}

class ListsPage extends StatelessWidget {
  const ListsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Boodschappenlijsten'),
        centerTitle: true,
      ),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.list_alt,
              size: 80,
            ),
            SizedBox(height: 16),
            Text(
              'Geen lijsten gevonden',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Maak je eerste boodschappenlijst aan',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey,
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {},
        tooltip: 'Nieuwe lijst',
        child: const Icon(Icons.add),
      ),
    );
  }
}
