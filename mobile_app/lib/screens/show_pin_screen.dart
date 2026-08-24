import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';

class ShowPinScreen extends StatelessWidget {
  final String orderId;
  final String pin;
  final double totalAmount;
  final int itemCount;

  const ShowPinScreen({
    super.key, 
    required this.orderId, 
    required this.pin,
    this.totalAmount = 0.0,
    this.itemCount = 0,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF003399),
      appBar: AppBar(
        title: const Text('Staff Verification', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18)),
        centerTitle: true,
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(vertical: 24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 24),
                padding: const EdgeInsets.all(32),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(24),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.2),
                      blurRadius: 20,
                      offset: const Offset(0, 10),
                    )
                  ],
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text('SHOW TO STAFF', style: TextStyle(color: Colors.grey, fontWeight: FontWeight.bold, fontSize: 12, letterSpacing: 1.5)),
                    const SizedBox(height: 24),
                    
                    // PIN
                    Text(
                      pin,
                      style: const TextStyle(fontSize: 48, fontWeight: FontWeight.bold, color: Colors.black, letterSpacing: 4),
                    ),
                    const SizedBox(height: 24),
                    
                    // QR Code (Added back for fast scanning)
                    QrImageView(
                      data: pin,
                      version: QrVersions.auto,
                      size: 180.0,
                      foregroundColor: const Color(0xFF003399),
                    ),
                    
                    const SizedBox(height: 24),
                    const Divider(),
                    const SizedBox(height: 16),
                    
                    // Compact Summary
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Total Paid', style: TextStyle(color: Colors.grey, fontSize: 11)),
                            Text('\$${totalAmount.toStringAsFixed(2)}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                          ],
                        ),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            const Text('Order ID', style: TextStyle(color: Colors.grey, fontSize: 11)),
                            Text('#$orderId', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                          ],
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 40),
              TextButton(
                onPressed: () => Navigator.popUntil(context, (route) => route.isFirst),
                child: const Text('Back to Home', style: TextStyle(color: Colors.white70, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
