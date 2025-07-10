import 'package:flutter/material.dart';
import '../services/product_service.dart';
import '../services/complete_data_import_service.dart';

class AdminPage extends StatefulWidget {
  const AdminPage({super.key});

  @override
  State<AdminPage> createState() => _AdminPageState();
}

class _AdminPageState extends State<AdminPage> {
  bool _isImporting = false;
  String? _importStatus;
  ImportResult? _lastImportResult;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Data Import Admin'),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Import Status Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Complete Dataset Import',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Import the complete checkjebon.nl dataset from their GitHub repository. This will replace all existing product data.',
                      style: TextStyle(color: Colors.grey[600]),
                    ),
                    const SizedBox(height: 16),
                    
                    if (_isImporting) ...[
                      const Row(
                        children: [
                          CircularProgressIndicator(),
                          SizedBox(width: 16),
                          Text('Importing dataset...'),
                        ],
                      ),
                      if (_importStatus != null) ...[
                        const SizedBox(height: 8),
                        Text(
                          _importStatus!,
                          style: const TextStyle(fontSize: 12),
                        ),
                      ],
                    ] else ...[
                      ElevatedButton.icon(
                        onPressed: _startCompleteImport,
                        icon: const Icon(Icons.download),
                        label: const Text('Start Complete Import'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.green,
                          foregroundColor: Colors.white,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Import Results Card
            if (_lastImportResult != null) ...[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Last Import Results',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 16),
                      
                      _buildResultItem(
                        'Products Imported',
                        _lastImportResult!.totalProducts.toString(),
                        Icons.inventory,
                        Colors.blue,
                      ),
                      const SizedBox(height: 8),
                      
                      _buildResultItem(
                        'Prices Added',
                        _lastImportResult!.totalPrices.toString(),
                        Icons.euro,
                        Colors.green,
                      ),
                      const SizedBox(height: 8),
                      
                      _buildResultItem(
                        'Product Groups Processed',
                        _lastImportResult!.processedGroups.toString(),
                        Icons.group_work,
                        Colors.orange,
                      ),
                    ],
                  ),
                ),
              ),
              
              const SizedBox(height: 16),
            ],
            
            // Quick Actions Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Quick Actions',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: _isImporting ? null : _checkDatabaseStatus,
                            icon: const Icon(Icons.info),
                            label: const Text('Check Status'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: _isImporting ? null : _clearDatabase,
                            icon: const Icon(Icons.delete),
                            label: const Text('Clear Data'),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: Colors.red,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Instructions Card
            Card(
              color: Colors.blue[50],
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.info_outline, color: Colors.blue[700]),
                        const SizedBox(width: 8),
                        Text(
                          'Instructions',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Colors.blue[700],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    
                    const Text(
                      '1. The complete import will download all products from checkjebon.nl GitHub repository\n'
                      '2. All existing product data will be cleared before import\n'
                      '3. Products will be categorized automatically based on their names\n'
                      '4. The import may take several minutes to complete\n'
                      '5. Do not close the app during import',
                      style: TextStyle(fontSize: 14),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResultItem(String label, String value, IconData icon, Color color) {
    return Row(
      children: [
        Icon(icon, color: color, size: 20),
        const SizedBox(width: 8),
        Text(
          '$label: ',
          style: const TextStyle(fontWeight: FontWeight.w500),
        ),
        Text(
          value,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ],
    );
  }

  Future<void> _startCompleteImport() async {
    setState(() {
      _isImporting = true;
      _importStatus = 'Starting import...';
      _lastImportResult = null;
    });

    try {
      setState(() {
        _importStatus = 'Downloading dataset from GitHub...';
      });

      final result = await ProductService.importCompleteDataset();

      setState(() {
        _isImporting = false;
        _importStatus = 'Import completed successfully!';
        _lastImportResult = result;
      });

      // Show success dialog
      if (mounted) {
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Import Successful'),
            content: Text(
              'Successfully imported:\n\n'
              '• ${result.totalProducts} products\n'
              '• ${result.totalPrices} prices\n'
              '• ${result.processedGroups} product groups\n\n'
              'The app now has the complete checkjebon.nl dataset!',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('OK'),
              ),
            ],
          ),
        );
      }
    } catch (e) {
      setState(() {
        _isImporting = false;
        _importStatus = 'Import failed: $e';
      });

      // Show error dialog
      if (mounted) {
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Import Failed'),
            content: Text('Error: $e'),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('OK'),
              ),
            ],
          ),
        );
      }
    }
  }

  Future<void> _checkDatabaseStatus() async {
    try {
      // You could add a method to get database statistics
      showDialog(
        context: context,
        builder: (context) => const AlertDialog(
          title: Text('Database Status'),
          content: Text('Use the main app to check current product counts and search functionality.'),
          actions: [
            TextButton(
              onPressed: null,
              child: Text('OK'),
            ),
          ],
        ),
      );
    } catch (e) {
      print('Error checking database status: $e');
    }
  }

  Future<void> _clearDatabase() async {
    // Show confirmation dialog
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Clear Database'),
        content: const Text(
          'Are you sure you want to clear all product data? This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Clear'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await CompleteDataImportService.clearProductData();
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Database cleared successfully'),
              backgroundColor: Colors.green,
            ),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Error clearing database: $e'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    }
  }
}