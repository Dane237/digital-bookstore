import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';

class PickupInstructionsScreen extends StatelessWidget {
  final String orderId;
  final String pin;
  final double totalAmount;
  final int itemCount;

  const PickupInstructionsScreen({
    super.key, 
    required this.orderId, 
    required this.pin,
    this.totalAmount = 0.0,
    this.itemCount = 0,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text('How to Pickup', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 18)),
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.white,
        leading: IconButton(icon: const Icon(Icons.arrow_back, color: Colors.black), onPressed: () => Navigator.pop(context)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Compact Header Card
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: Colors.grey[50], borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.grey.shade100)),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('Order #$orderId', style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.black87)),
                  const Text('Paid ✅', style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold, fontSize: 12)),
                ],
              ),
            ),
            const SizedBox(height: 24),
            
            _buildStep(1, 'Go to the PUC Bookstore Counter'),
            _buildStep(2, 'Show your unique QR Code or PIN'),
            _buildStep(3, 'Staff will verify and hand over books'),
            
            const SizedBox(height: 32),
            
            // Highlighted QR & PIN Token
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: const Color(0xFF003399).withOpacity(0.05),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: const Color(0xFF003399).withOpacity(0.1)),
              ),
              child: Column(
                children: [
                  const Text('YOUR PICKUP TOKEN', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF003399), letterSpacing: 1)),
                  const SizedBox(height: 20),
                  
                  // QR Code
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.grey.shade200)),
                    child: QrImageView(
                      data: pin,
                      version: QrVersions.auto,
                      size: 160.0,
                      foregroundColor: const Color(0xFF003399),
                    ),
                  ),
                  
                  const SizedBox(height: 20),
                  Text(pin, style: const TextStyle(fontSize: 40, fontWeight: FontWeight.bold, color: Color(0xFF003399), letterSpacing: 6)),
                ],
              ),
            ),
            
            const SizedBox(height: 40),
            
            OutlinedButton(
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: Color(0xFF003399)),
                minimumSize: const Size.fromHeight(56),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              onPressed: () => Navigator.popUntil(context, (route) => route.isFirst),
              child: const Text('Back to Home', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF003399))),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStep(int number, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(radius: 12, backgroundColor: const Color(0xFF003399), child: Text('$number', style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold))),
          const SizedBox(width: 16),
          Expanded(child: Text(text, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500, color: Colors.black87))),
        ],
      ),
    );
  }
}
