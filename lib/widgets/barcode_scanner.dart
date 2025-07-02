import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

class BarcodeScanner extends StatefulWidget {
  final Function(String) onBarcodeDetected;
  final String? overlayText;

  const BarcodeScanner({
    super.key,
    required this.onBarcodeDetected,
    this.overlayText,
  });

  @override
  State<BarcodeScanner> createState() => _BarcodeScannerState();
}

class _BarcodeScannerState extends State<BarcodeScanner> {
  MobileScannerController controller = MobileScannerController(
    formats: [
      BarcodeFormat.ean13,
      BarcodeFormat.ean8,
      BarcodeFormat.code128,
      BarcodeFormat.code39,
      BarcodeFormat.qrCode,
    ],
  );

  bool _isScanning = true;
  String? _lastScannedCode;

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Camera view
        MobileScanner(
          controller: controller,
          onDetect: _onBarcodeDetected,
        ),
        
        // Overlay with scanning frame
        _buildScannerOverlay(),
        
        // Top controls
        Positioned(
          top: 50,
          left: 16,
          right: 16,
          child: Row(
            children: [
              // Back button
              CircleAvatar(
                backgroundColor: Colors.black54,
                child: IconButton(
                  icon: const Icon(Icons.arrow_back, color: Colors.white),
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ),
              const Spacer(),
              
              // Flash toggle
              CircleAvatar(
                backgroundColor: Colors.black54,
                child: ValueListenableBuilder(
                  valueListenable: controller,
                  builder: (context, state, child) {
                    if (!state.isInitialized) {
                      return const Icon(Icons.flash_off, color: Colors.white);
                    }
                    
                    return IconButton(
                      icon: Icon(
                        state.torchState == TorchState.on
                            ? Icons.flash_on
                            : Icons.flash_off,
                        color: Colors.white,
                      ),
                      onPressed: () => controller.toggleTorch(),
                    );
                  },
                ),
              ),
              
              const SizedBox(width: 8),
              
              // Camera flip
              CircleAvatar(
                backgroundColor: Colors.black54,
                child: ValueListenableBuilder(
                  valueListenable: controller,
                  builder: (context, state, child) {
                    if (!state.isInitialized || !state.isRunning) {
                      return const Icon(Icons.camera_alt, color: Colors.white);
                    }
                    
                    return IconButton(
                      icon: const Icon(Icons.flip_camera_ios, color: Colors.white),
                      onPressed: () => controller.switchCamera(),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
        
        // Bottom info
        Positioned(
          bottom: 100,
          left: 16,
          right: 16,
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.black54,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  widget.overlayText ?? 'Richt de camera op een barcode',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                  ),
                  textAlign: TextAlign.center,
                ),
                if (_lastScannedCode != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Laatste scan: $_lastScannedCode',
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 12,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    ElevatedButton.icon(
                      onPressed: _isScanning ? _pauseScanning : _resumeScanning,
                      icon: Icon(_isScanning ? Icons.pause : Icons.play_arrow),
                      label: Text(_isScanning ? 'Pauzeren' : 'Hervatten'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: Colors.black,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildScannerOverlay() {
    return Container(
      decoration: ShapeDecoration(
        shape: ScannerOverlay(),
      ),
    );
  }

  void _onBarcodeDetected(BarcodeCapture capture) {
    if (!_isScanning) return;
    
    final List<Barcode> barcodes = capture.barcodes;
    for (final barcode in barcodes) {
      final String? code = barcode.rawValue;
      if (code != null && code != _lastScannedCode) {
        setState(() {
          _lastScannedCode = code;
        });
        
        // Provide haptic feedback
        _showDetectionFeedback();
        
        // Call the callback
        widget.onBarcodeDetected(code);
        
        // Brief pause to prevent multiple scans
        _pauseScanning();
        Future.delayed(const Duration(seconds: 2), () {
          if (mounted) _resumeScanning();
        });
        
        break; // Only process first detected barcode
      }
    }
  }

  void _showDetectionFeedback() {
    // Visual feedback
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Barcode gedetecteerd: $_lastScannedCode'),
          duration: const Duration(seconds: 2),
          backgroundColor: Colors.green,
        ),
      );
    }
  }

  void _pauseScanning() {
    setState(() {
      _isScanning = false;
    });
    controller.stop();
  }

  void _resumeScanning() {
    setState(() {
      _isScanning = true;
    });
    controller.start();
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }
}

class ScannerOverlay extends ShapeBorder {
  const ScannerOverlay();

  @override
  EdgeInsetsGeometry get dimensions => const EdgeInsets.all(10);

  @override
  Path getInnerPath(Rect rect, {TextDirection? textDirection}) {
    return Path()..addRect(rect);
  }

  @override
  Path getOuterPath(Rect rect, {TextDirection? textDirection}) {
    Path path = Path()..addRect(rect);
    
    // Calculate scanner window size and position
    const double scanAreaWidth = 250.0;
    const double scanAreaHeight = 150.0;
    final double left = (rect.width - scanAreaWidth) / 2;
    final double top = (rect.height - scanAreaHeight) / 2;
    
    final Rect scanArea = Rect.fromLTWH(left, top, scanAreaWidth, scanAreaHeight);
    
    // Create the overlay with a transparent scanning area
    return Path.combine(
      PathOperation.difference,
      path,
      Path()..addRRect(RRect.fromRectAndRadius(scanArea, const Radius.circular(12))),
    );
  }

  @override
  void paint(Canvas canvas, Rect rect, {TextDirection? textDirection}) {
    const double scanAreaWidth = 250.0;
    const double scanAreaHeight = 150.0;
    final double left = (rect.width - scanAreaWidth) / 2;
    final double top = (rect.height - scanAreaHeight) / 2;
    
    final Rect scanArea = Rect.fromLTWH(left, top, scanAreaWidth, scanAreaHeight);
    
    // Paint the dark overlay
    final Paint overlayPaint = Paint()
      ..color = Colors.black.withOpacity(0.5);
    
    // Paint the entire rect first
    canvas.drawRect(rect, overlayPaint);
    
    // Clear the scanning area
    final Paint clearPaint = Paint()
      ..blendMode = BlendMode.clear;
    
    canvas.drawRRect(
      RRect.fromRectAndRadius(scanArea, const Radius.circular(12)),
      clearPaint,
    );
    
    // Draw corner brackets
    final Paint bracketPaint = Paint()
      ..color = Colors.white
      ..strokeWidth = 3.0
      ..style = PaintingStyle.stroke;
    
    const double bracketLength = 20.0;
    
    // Top-left corner
    canvas.drawPath(
      Path()
        ..moveTo(scanArea.left, scanArea.top + bracketLength)
        ..lineTo(scanArea.left, scanArea.top)
        ..lineTo(scanArea.left + bracketLength, scanArea.top),
      bracketPaint,
    );
    
    // Top-right corner
    canvas.drawPath(
      Path()
        ..moveTo(scanArea.right - bracketLength, scanArea.top)
        ..lineTo(scanArea.right, scanArea.top)
        ..lineTo(scanArea.right, scanArea.top + bracketLength),
      bracketPaint,
    );
    
    // Bottom-left corner
    canvas.drawPath(
      Path()
        ..moveTo(scanArea.left, scanArea.bottom - bracketLength)
        ..lineTo(scanArea.left, scanArea.bottom)
        ..lineTo(scanArea.left + bracketLength, scanArea.bottom),
      bracketPaint,
    );
    
    // Bottom-right corner
    canvas.drawPath(
      Path()
        ..moveTo(scanArea.right - bracketLength, scanArea.bottom)
        ..lineTo(scanArea.right, scanArea.bottom)
        ..lineTo(scanArea.right, scanArea.bottom - bracketLength),
      bracketPaint,
    );
    
    // Draw scanning line animation would go here
    // For simplicity, we'll add a static center line
    final Paint linePaint = Paint()
      ..color = Colors.red
      ..strokeWidth = 2.0;
    
    canvas.drawLine(
      Offset(scanArea.left, scanArea.center.dy),
      Offset(scanArea.right, scanArea.center.dy),
      linePaint,
    );
  }

  @override
  ShapeBorder scale(double t) => this;
}

// Simple barcode scanner widget for simpler use cases
class SimpleBarcodeScanner extends StatelessWidget {
  final Function(String) onBarcodeDetected;

  const SimpleBarcodeScanner({
    super.key,
    required this.onBarcodeDetected,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 200,
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey),
        borderRadius: BorderRadius.circular(12),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: MobileScanner(
          onDetect: (capture) {
            final List<Barcode> barcodes = capture.barcodes;
            for (final barcode in barcodes) {
              final String? code = barcode.rawValue;
              if (code != null) {
                onBarcodeDetected(code);
                break;
              }
            }
          },
        ),
      ),
    );
  }
}