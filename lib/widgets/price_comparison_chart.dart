import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/product.dart';

class PriceComparisonChart extends StatelessWidget {
  final List<ProductPrice> prices;

  const PriceComparisonChart({
    super.key,
    required this.prices,
  });

  @override
  Widget build(BuildContext context) {
    if (prices.isEmpty) {
      return const Center(
        child: Text('Geen prijsdata beschikbaar'),
      );
    }

    // Sort prices for better visualization
    final sortedPrices = List<ProductPrice>.from(prices)
      ..sort((a, b) => a.price.compareTo(b.price));

    return BarChart(
      BarChartData(
        alignment: BarChartAlignment.spaceAround,
        maxY: _getMaxY(sortedPrices),
        minY: 0,
        barTouchData: BarTouchData(
          enabled: true,
          touchTooltipData: BarTouchTooltipData(
            getTooltipColor: (group) => Colors.black87,
            tooltipRoundedRadius: 8,
            getTooltipItem: (group, groupIndex, rod, rodIndex) {
              final price = sortedPrices[group.x.toInt()];
              return BarTooltipItem(
                '${price.supermarketName}\n€${price.price.toStringAsFixed(2)}',
                const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              );
            },
          ),
        ),
        titlesData: FlTitlesData(
          show: true,
          rightTitles: const AxisTitles(
            sideTitles: SideTitles(showTitles: false),
          ),
          topTitles: const AxisTitles(
            sideTitles: SideTitles(showTitles: false),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index >= 0 && index < sortedPrices.length) {
                  final supermarket = sortedPrices[index].supermarketName;
                  return Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      _getShortName(supermarket),
                      style: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w500,
                      ),
                      maxLines: 2,
                      textAlign: TextAlign.center,
                    ),
                  );
                }
                return const Text('');
              },
              reservedSize: 40,
            ),
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 40,
              getTitlesWidget: (value, meta) {
                return Text(
                  '€${value.toStringAsFixed(0)}',
                  style: const TextStyle(
                    fontSize: 10,
                    color: Colors.grey,
                  ),
                );
              },
            ),
          ),
        ),
        borderData: FlBorderData(
          show: false,
        ),
        barGroups: _buildBarGroups(sortedPrices),
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
          horizontalInterval: _getGridInterval(sortedPrices),
          getDrawingHorizontalLine: (value) {
            return FlLine(
              color: Colors.grey.withOpacity(0.2),
              strokeWidth: 1,
            );
          },
        ),
      ),
    );
  }

  List<BarChartGroupData> _buildBarGroups(List<ProductPrice> sortedPrices) {
    final lowestPrice = sortedPrices.first.price;
    final highestPrice = sortedPrices.last.price;
    
    return sortedPrices.asMap().entries.map((entry) {
      final index = entry.key;
      final price = entry.value;
      
      // Color coding based on price position
      Color barColor;
      if (price.price == lowestPrice) {
        barColor = Colors.green; // Best deal
      } else if (price.price == highestPrice) {
        barColor = Colors.red; // Most expensive
      } else {
        // Gradient between yellow and orange for middle prices
        final ratio = (price.price - lowestPrice) / (highestPrice - lowestPrice);
        barColor = Color.lerp(Colors.green, Colors.red, ratio) ?? Colors.orange;
      }
      
      // Add extra height for sale items
      final isOnSale = price.isOnSale;
      
      return BarChartGroupData(
        x: index,
        barRods: [
          BarChartRodData(
            toY: price.price,
            color: barColor,
            width: 20,
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(6),
              topRight: Radius.circular(6),
            ),
            gradient: LinearGradient(
              begin: Alignment.bottomCenter,
              end: Alignment.topCenter,
              colors: [
                barColor.withOpacity(0.8),
                barColor,
              ],
            ),
            // Add pattern for sale items
            borderSide: isOnSale 
                ? BorderSide(color: Colors.yellow, width: 2)
                : BorderSide.none,
          ),
        ],
        showingTooltipIndicators: [],
      );
    }).toList();
  }

  double _getMaxY(List<ProductPrice> prices) {
    if (prices.isEmpty) return 10;
    final maxPrice = prices.map((p) => p.price).reduce((a, b) => a > b ? a : b);
    return (maxPrice * 1.2).ceilToDouble();
  }

  double _getGridInterval(List<ProductPrice> prices) {
    if (prices.isEmpty) return 1;
    final maxPrice = prices.map((p) => p.price).reduce((a, b) => a > b ? a : b);
    
    if (maxPrice <= 5) return 1;
    if (maxPrice <= 10) return 2;
    if (maxPrice <= 20) return 5;
    if (maxPrice <= 50) return 10;
    return 20;
  }

  String _getShortName(String supermarketName) {
    // Abbreviate long supermarket names for chart display
    switch (supermarketName.toLowerCase()) {
      case 'albert heijn':
        return 'AH';
      case 'jan linders':
        return 'Jan L.';
      default:
        if (supermarketName.length > 6) {
          return '${supermarketName.substring(0, 6)}...';
        }
        return supermarketName;
    }
  }
}

class PriceComparisonCard extends StatelessWidget {
  final ProductPrice price;
  final bool isLowest;
  final bool isHighest;
  final int rank;

  const PriceComparisonCard({
    super.key,
    required this.price,
    required this.isLowest,
    required this.isHighest,
    required this.rank,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isLowest 
              ? Colors.green.withOpacity(0.5)
              : isHighest 
                  ? Colors.red.withOpacity(0.5)
                  : Colors.grey.withOpacity(0.2),
          width: isLowest || isHighest ? 2 : 1,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            // Rank badge
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: isLowest 
                    ? Colors.green
                    : isHighest 
                        ? Colors.red
                        : Colors.grey,
                shape: BoxShape.circle,
              ),
              child: Center(
                child: isLowest
                    ? const Icon(Icons.star, color: Colors.white, size: 18)
                    : Text(
                        rank.toString(),
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
              ),
            ),
            const SizedBox(width: 12),
            
            // Supermarket logo placeholder
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: _getSupermarketColor(price.supermarketSlug),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Center(
                child: Text(
                  _getSupermarketInitials(price.supermarketName),
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 12),
            
            // Supermarket info
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    price.supermarketName,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 2),
                  if (price.lastUpdated != null)
                    Text(
                      'Bijgewerkt: ${_formatDate(price.lastUpdated)}',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[600],
                      ),
                    ),
                ],
              ),
            ),
            
            // Price info
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '€${price.price.toStringAsFixed(2)}',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: isLowest 
                        ? Colors.green
                        : isHighest 
                            ? Colors.red
                            : Colors.black,
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
                    style: TextStyle(
                      fontSize: 10,
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ],
            ),
            
            // Special indicators
            const SizedBox(width: 8),
            Column(
              children: [
                if (isLowest) ...[
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.green,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Text(
                      'BEST',
                      style: TextStyle(
                        fontSize: 10,
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(height: 4),
                ],
                if (price.isOnSale) ...[
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.orange,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Text(
                      'SALE',
                      style: TextStyle(
                        fontSize: 10,
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ],
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

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);
    
    if (difference.inDays > 0) {
      return '${difference.inDays}d geleden';
    } else if (difference.inHours > 0) {
      return '${difference.inHours}u geleden';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes}m geleden';
    } else {
      return 'Net';
    }
  }
}