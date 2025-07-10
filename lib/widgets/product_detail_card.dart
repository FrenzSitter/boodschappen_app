import 'package:flutter/material.dart';
import '../models/product.dart';
import 'product_card.dart';

class ProductDetailCard extends StatelessWidget {
  final ProductWithPrices productWithPrices;
  final bool showCompactView;

  const ProductDetailCard({
    super.key,
    required this.productWithPrices,
    this.showCompactView = false,
  });

  @override
  Widget build(BuildContext context) {
    final product = productWithPrices.product;
    final prices = productWithPrices.prices;
    final cheapestPrice = prices.isNotEmpty
        ? prices.reduce((a, b) => a.price < b.price ? a : b)
        : null;

    if (showCompactView) {
      return _buildCompactView(context, product, cheapestPrice);
    }

    return _buildDetailedView(context, product, prices);
  }

  Widget _buildCompactView(BuildContext context, Product product, ProductPrice? cheapestPrice) {
    return Container(
      padding: const EdgeInsets.all(16),
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Product name and brand
          Text(
            product.name,
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
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
          
          // Price info
          if (cheapestPrice != null) ...[
            Row(
              children: [
                Text(
                  '€${cheapestPrice.price.toStringAsFixed(2)}',
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Colors.green,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  'bij ${cheapestPrice.supermarketName}',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          ],
          
          const SizedBox(height: 8),
          
          // Product details
          if (product.description != null) ...[
            Text(
              product.description!,
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[600],
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
          
          // Category and tags
          const SizedBox(height: 8),
          Wrap(
            spacing: 4,
            children: [
              if (product.categoryName != null)
                _buildTag(product.categoryName!, Colors.blue),
              if (product.isOrganic)
                _buildTag('Biologisch', Colors.green),
              if (product.isBio)
                _buildTag('Bio', Colors.green),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildDetailedView(BuildContext context, Product product, List<ProductPrice> prices) {
    return Container(
      padding: const EdgeInsets.all(16),
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Product header
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Product image placeholder
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  color: Colors.grey[200],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(
                  Icons.image,
                  size: 40,
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
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
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
                    if (product.description != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        product.description!,
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[600],
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 16),
          
          // Product details
          _buildProductDetails(product),
          
          const SizedBox(height: 16),
          
          // Price comparison
          if (prices.isNotEmpty) ...[
            const Text(
              'Prijzen per supermarkt',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            
            // Sort prices by price (lowest first)
            ...prices.map((price) => _buildPriceRow(price)).toList()
              ..sort((a, b) {
                final aPrice = prices.firstWhere((p) => p.supermarketName == a.key).price;
                final bPrice = prices.firstWhere((p) => p.supermarketName == b.key).price;
                return aPrice.compareTo(bPrice);
              }),
          ] else ...[
            const Text(
              'Geen prijsinformatie beschikbaar',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildProductDetails(Product product) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Productinformatie',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          
          // Product details rows
          if (product.categoryName != null)
            _buildDetailRow('Categorie', product.categoryName!),
          if (product.unitType != null)
            _buildDetailRow('Eenheid', product.unitType!),
          if (product.packageSize != null && product.packageUnit != null)
            _buildDetailRow('Verpakking', '${product.packageSize} ${product.packageUnit}'),
          if (product.barcode != null)
            _buildDetailRow('Barcode', product.barcode!),
          
          // Tags
          const SizedBox(height: 8),
          Wrap(
            spacing: 6,
            runSpacing: 4,
            children: [
              if (product.isOrganic)
                _buildTag('Biologisch', Colors.green),
              if (product.isBio)
                _buildTag('Bio', Colors.green),
              if (product.unitType == 'kg' || product.unitType == 'liter')
                _buildTag('Vers', Colors.blue),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(
              '$label:',
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[600],
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPriceRow(ProductPrice price) {
    return Container(
      key: ValueKey(price.supermarketName),
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
      margin: const EdgeInsets.only(bottom: 4),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        children: [
          // Supermarket indicator
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(
              color: _getSupermarketColor(price.supermarketSlug),
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 8),
          
          // Supermarket name
          Expanded(
            child: Text(
              price.supermarketName,
              style: const TextStyle(
                fontSize: 14,
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
              if (price.pricePerUnit != null && price.pricePerUnit != price.price) ...[
                Text(
                  '€${price.pricePerUnit!.toStringAsFixed(2)}/unit',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ],
          ),
          
          // Sale indicator
          if (price.isOnSale) ...[
            const SizedBox(width: 8),
            const Icon(
              Icons.local_offer,
              size: 16,
              color: Colors.red,
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildTag(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 10,
          color: color,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
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
      case 'dekamarkt':
        return const Color(0xFFE30613);
      default:
        return Colors.grey;
    }
  }
}