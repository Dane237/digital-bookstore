import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'pickup_instructions_screen.dart';
import 'show_pin_screen.dart';

class OrderSuccessScreen extends StatelessWidget {
  final String orderId;
  final String pickupPin;
  final double totalPaid;
  final String paymentMethod;
  final String customerName;
  final List<dynamic> items;

  const OrderSuccessScreen({
    super.key,
    required this.orderId,
    required this.pickupPin,
    required this.totalPaid,
    required this.paymentMethod,
    required this.customerName,
    required this.items,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // 1. Success Indicator & Header
              const Center(
                child: Icon(Icons.check_circle, color: Colors.green, size: 64),
              ),
              const SizedBox(height: 12),
              const Text(
                'Payment Successful',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Color(0xFF003399)),
              ),
              const SizedBox(height: 24),
              
              // 2. Receipt Card
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.grey[50],
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.grey.shade200),
                ),
                child: Column(
                  children: [
                    _buildRow('Order ID', orderId),
                    _buildRow('Method', paymentMethod),
                    _buildRow('Status', 'Paid', isStatus: true),
                    const Divider(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Total Paid', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        Text('\$${totalPaid.toStringAsFixed(2)}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Color(0xFF003399))),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              
              // 3. Highlighted PIN & QR Section
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: const Color(0xFF003399),
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(color: const Color(0xFF003399).withOpacity(0.3), blurRadius: 15, offset: const Offset(0, 8))
                  ],
                ),
                child: Column(
                  children: [
                    const Text('YOUR PICKUP TOKEN', style: TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
                    const SizedBox(height: 12),
                    
                    // QR Code for fast scanning
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
                      child: QrImageView(
                        data: pickupPin,
                        version: QrVersions.auto,
                        size: 140.0,
                        foregroundColor: const Color(0xFF003399),
                      ),
                    ),
                    
                    const SizedBox(height: 16),
                    Text(
                      pickupPin,
                      style: const TextStyle(color: Colors.white, fontSize: 48, fontWeight: FontWeight.bold, letterSpacing: 8),
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton.icon(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => ShowPinScreen(
                              orderId: orderId,
                              pin: pickupPin,
                              totalAmount: totalPaid,
                              itemCount: items.length,
                            ),
                          ),
                        );
                      },
                      icon: const Icon(Icons.qr_code_2),
                      label: const Text('FULLSCREEN QR / PIN'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: const Color(0xFF003399),
                        minimumSize: const Size.fromHeight(44),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                    ),
                    const SizedBox(height: 12),
                    const Text('Show this to bookstore staff', style: TextStyle(color: Colors.white60, fontSize: 12)),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              
              // 4. Books Summary
              const Text('BOOKS IN ORDER', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.grey, letterSpacing: 0.5)),
              const SizedBox(height: 12),
              ...items.map((item) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  children: [
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4), 
                      child: item.book.coverImg.isNotEmpty 
                        ? Image.network(item.book.coverImg, width: 32, height: 40, fit: BoxFit.cover, errorBuilder: (c,e,s) => const Icon(Icons.book, size: 20))
                        : const Icon(Icons.book, size: 20),
                    ),
                    const SizedBox(width: 12),
                    Expanded(child: Text('${item.book.title} x${item.quantity}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500), maxLines: 1, overflow: TextOverflow.ellipsis)),
                    Text('\$${(item.book.price * item.quantity).toStringAsFixed(2)}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                  ],
                ),
              )),
              
              const SizedBox(height: 32),
              
              // 5. Action Buttons
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF003399),
                  foregroundColor: Colors.white,
                  minimumSize: const Size.fromHeight(54),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  elevation: 0,
                ),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => PickupInstructionsScreen(
                        orderId: orderId, 
                        pin: pickupPin,
                        totalAmount: totalPaid,
                        itemCount: items.length,
                      ),
                    ),
                  );
                },
                child: const Text('Pickup Instructions', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: Color(0xFF003399)),
                  minimumSize: const Size.fromHeight(54),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                onPressed: () => Navigator.popUntil(context, (route) => route.isFirst),
                child: const Text('Back to Home', style: TextStyle(color: Color(0xFF003399), fontSize: 16, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRow(String label, String value, {bool isStatus = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 14)),
          if (isStatus)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(color: Colors.green.shade50, borderRadius: BorderRadius.circular(4)),
              child: Text(value, style: const TextStyle(color: Colors.green, fontWeight: FontWeight.bold, fontSize: 11)),
            )
          else
            Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
        ],
      ),
    );
  }
}
