import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:animations/animations.dart';
import '../models/product.dart';
import '../widgets/product_card.dart';
import '../widgets/price_comparison_chart.dart';

class ProductComparisonPage extends StatefulWidget {
  final ProductWithPrices productWithPrices;

  const ProductComparisonPage({
    super.key,
    required this.productWithPrices,
  });

  @override
  State<ProductComparisonPage> createState() => _ProductComparisonPageState();
}

class _ProductComparisonPageState extends State<ProductComparisonPage>
    with TickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  int _selectedViewIndex = 0; // 0: Chart, 1: List, 2: History

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));
    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final product = widget.productWithPrices.product;
    final prices = widget.productWithPrices.availablePrices;
    final cheapestPrice = widget.productWithPrices.cheapestPrice;
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('Prijsvergelijking'),
        centerTitle: true,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.share),
            onPressed: _shareProduct,
          ),
          IconButton(
            icon: const Icon(Icons.favorite_border),
            onPressed: _addToFavorites,
          ),
        ],
      ),
      body: FadeTransition(
        opacity: _fadeAnimation,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Product header
              _buildProductHeader(product, prices),
              
              // Price summary
              _buildPriceSummary(prices, cheapestPrice),
              
              // View toggle
              _buildViewToggle(),
              
              // Main content
              AnimatedSwitcher(
                duration: const Duration(milliseconds: 300),
                child: _buildSelectedView(prices),
              ),
              
              // Additional info
              _buildAdditionalInfo(product),
            ],
          ),
        ),
      ),
      bottomNavigationBar: _buildBottomActions(product),
    );
  }

  Widget _buildProductHeader(Product product, List<ProductPrice> prices) {
    return Container(
      padding: const EdgeInsets.all(20),
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
      child: Row(
        children: [
          // Product image
          Container(
            width: 80,
            height: 80,
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
            child: product.imageUrl != null
                ? ClipRRect(
                    borderRadius: BorderRadius.circular(12),
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
                    fontSize: 20,
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
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.secondary,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${prices.length} winkels',
                    style: TextStyle(
                      fontSize: 12,
                      color: Theme.of(context).colorScheme.onSecondary,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPriceSummary(List<ProductPrice> prices, ProductPrice? cheapestPrice) {
    if (prices.isEmpty) return const SizedBox.shrink();
    
    final lowestPrice = prices.map((p) => p.price).reduce((a, b) => a < b ? a : b);
    final highestPrice = prices.map((p) => p.price).reduce((a, b) => a > b ? a : b);
    final avgPrice = prices.map((p) => p.price).reduce((a, b) => a + b) / prices.length;
    final savings = highestPrice - lowestPrice;
    
    return Container(
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
        children: [
          // Price range
          Row(
            children: [
              Expanded(
                child: _buildPriceStat(
                  'Laagste prijs',
                  '€${lowestPrice.toStringAsFixed(2)}',
                  Colors.green,
                  Icons.trending_down,
                ),
              ),
              Container(
                width: 1,
                height: 40,
                color: Colors.grey[300],
              ),
              Expanded(
                child: _buildPriceStat(
                  'Hoogste prijs',
                  '€${highestPrice.toStringAsFixed(2)}',
                  Colors.red,
                  Icons.trending_up,
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 16),
          
          Row(
            children: [
              Expanded(
                child: _buildPriceStat(
                  'Gemiddelde',
                  '€${avgPrice.toStringAsFixed(2)}',
                  Colors.blue,
                  Icons.analytics,
                ),
              ),
              Container(
                width: 1,
                height: 40,
                color: Colors.grey[300],
              ),
              Expanded(
                child: _buildPriceStat(
                  'Mogelijk besparen',
                  '€${savings.toStringAsFixed(2)}',
                  Colors.orange,
                  Icons.savings,
                ),
              ),
            ],
          ),
          
          if (cheapestPrice != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.green.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.green.withOpacity(0.3)),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.star,
                    color: Colors.green,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Beste deal bij ${cheapestPrice.supermarketName}',
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        color: Colors.green,
                      ),
                    ),
                  ),
                  Text(
                    '€${cheapestPrice.price.toStringAsFixed(2)}',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Colors.green,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildPriceStat(String label, String value, Color color, IconData icon) {
    return Column(
      children: [
        Icon(icon, color: color, size: 20),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ],
    );
  }

  Widget _buildViewToggle() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          _buildToggleButton(0, 'Grafiek', Icons.bar_chart),
          _buildToggleButton(1, 'Lijst', Icons.list),
          _buildToggleButton(2, 'Geschiedenis', Icons.history),
        ],
      ),
    );
  }

  Widget _buildToggleButton(int index, String label, IconData icon) {
    final isSelected = _selectedViewIndex == index;
    
    return Expanded(
      child: GestureDetector(
        onTap: () {
          setState(() {
            _selectedViewIndex = index;
          });
        },
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: isSelected ? Theme.of(context).colorScheme.primary : Colors.transparent,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 18,
                color: isSelected 
                    ? Theme.of(context).colorScheme.onPrimary 
                    : Colors.grey[600],
              ),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                  color: isSelected 
                      ? Theme.of(context).colorScheme.onPrimary 
                      : Colors.grey[600],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSelectedView(List<ProductPrice> prices) {
    switch (_selectedViewIndex) {
      case 0:
        return _buildChartView(prices);
      case 1:
        return _buildListView(prices);
      case 2:
        return _buildHistoryView(prices);
      default:
        return _buildChartView(prices);
    }
  }

  Widget _buildChartView(List<ProductPrice> prices) {
    if (prices.isEmpty) {
      return const Center(
        child: Text('Geen prijzen beschikbaar'),
      );
    }

    return Container(
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
          const Text(
            'Prijsvergelijking per supermarkt',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 20),
          
          SizedBox(
            height: 300,
            child: PriceComparisonChart(prices: prices),
          ),
        ],
      ),
    );
  }

  Widget _buildListView(List<ProductPrice> prices) {
    if (prices.isEmpty) {
      return const Center(
        child: Text('Geen prijzen beschikbaar'),
      );
    }

    // Sort prices by lowest first
    final sortedPrices = List<ProductPrice>.from(prices)
      ..sort((a, b) => a.price.compareTo(b.price));

    return Container(
      margin: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.only(bottom: 16),
            child: Text(
              'Prijzen per supermarkt',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          
          ...sortedPrices.asMap().entries.map((entry) {
            final index = entry.key;
            final price = entry.value;
            final isLowest = index == 0;
            final isHighest = index == sortedPrices.length - 1;
            
            return PriceComparisonCard(
              price: price,
              isLowest: isLowest,
              isHighest: isHighest && sortedPrices.length > 1,
              rank: index + 1,
            );
          }),
        ],
      ),
    );
  }

  Widget _buildHistoryView(List<ProductPrice> prices) {
    return Container(
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
          const Text(
            'Prijsgeschiedenis',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 20),
          
          // Placeholder for price history chart
          Container(
            height: 200,
            decoration: BoxDecoration(
              color: Colors.grey[100],
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.timeline,
                    size: 48,
                    color: Colors.grey,
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Prijsgeschiedenis wordt binnenkort toegevoegd',
                    style: TextStyle(
                      color: Colors.grey,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAdditionalInfo(Product product) {
    return Container(
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
          const Text(
            'Productinformatie',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          
          if (product.barcode != null) ...[
            _buildInfoRow('Barcode', product.barcode!),
            const SizedBox(height: 8),
          ],
          
          if (product.categoryName != null) ...[
            _buildInfoRow('Categorie', product.categoryName!),
            const SizedBox(height: 8),
          ],
          
          if (product.description != null) ...[
            _buildInfoRow('Beschrijving', product.description!),
            const SizedBox(height: 8),
          ],
          
          _buildInfoRow('Type', product.unitType),
          
          const SizedBox(height: 16),
          
          // Special attributes
          Wrap(
            spacing: 8,
            children: [
              if (product.isOrganic)
                _buildAttributeChip('Biologisch', Colors.green),
              if (product.isBio)
                _buildAttributeChip('Bio', Colors.green),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 80,
          child: Text(
            '$label:',
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[600],
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: const TextStyle(fontSize: 14),
          ),
        ),
      ],
    );
  }

  Widget _buildAttributeChip(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          color: color,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  Widget _buildBottomActions(Product product) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: OutlinedButton.icon(
              onPressed: _addToShoppingList,
              icon: const Icon(Icons.add_shopping_cart),
              label: const Text('Toevoegen aan lijst'),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: ElevatedButton.icon(
              onPressed: _findInStores,
              icon: const Icon(Icons.location_on),
              label: const Text('Vind in winkel'),
            ),
          ),
        ],
      ),
    );
  }

  void _shareProduct() {
    // TODO: Implement share functionality
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Deel functie wordt binnenkort toegevoegd')),
    );
  }

  void _addToFavorites() {
    // TODO: Implement favorites functionality
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Toegevoegd aan favorieten')),
    );
  }

  void _addToShoppingList() {
    // TODO: Implement shopping list functionality
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Toegevoegd aan boodschappenlijst')),
    );
  }

  void _findInStores() {
    // TODO: Implement store locator
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Winkelzoeker wordt binnenkort toegevoegd')),
    );
  }
}