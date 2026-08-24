import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'order_success_screen.dart';
import '../services/api_service.dart';
import '../providers/auth_provider.dart';
import '../providers/cart_provider.dart';

class ProcessingPaymentScreen extends ConsumerStatefulWidget {
  final double amount;
  final String method;
  final List<dynamic> cartItems;
  final int userId;

  const ProcessingPaymentScreen({
    super.key, 
    required this.amount, 
    required this.method,
    required this.cartItems,
    required this.userId,
  });

  @override
  ConsumerState<ProcessingPaymentScreen> createState() => _ProcessingPaymentScreenState();
}

class _ProcessingPaymentScreenState extends ConsumerState<ProcessingPaymentScreen> {
  @override
  void initState() {
    super.initState();
    _processRealOrder();
  }

  void _processRealOrder() async {
    final user = ref.read(authProvider);
    await Future.delayed(const Duration(seconds: 2));
    
    try {
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final orderPayload = {
        "user_id": widget.userId,
        "total_amount": widget.amount,
        "payment_method": widget.method,
        "stripe_payment_id": widget.method.contains('Card') ? "ST-TEST-$timestamp" : "BANK-TEST-$timestamp",
        "items": widget.cartItems.map((item) => {
          "book_id": item.book.bookId,
          "quantity": item.quantity,
          "unit_price": item.book.price,
        }).toList(),
      };

      final response = await http.post(
        Uri.parse('${ApiService.baseUrl}/orders/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(orderPayload),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final finalItems = List.from(widget.cartItems);
        ref.read(cartProvider.notifier).clearCart();

        if (mounted) {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (context) => OrderSuccessScreen(
                orderId: data['order_id'].toString(),
                pickupPin: data['pickup_pin'].toString(),
                totalPaid: widget.amount,
                paymentMethod: widget.method,
                customerName: user?.fullName ?? "Guest Student",
                items: finalItems,
              ),
            ),
          );
        }
      } else {
        final errorBody = jsonDecode(response.body);
        throw Exception(errorBody['detail'] ?? 'Server error');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Order failed: $e')));
        Navigator.pop(context);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Spacer(),
              Container(
                width: 200, height: 200,
                decoration: BoxDecoration(color: Colors.blue.shade50.withValues(alpha: 0.3), shape: BoxShape.circle),
                child: Center(
                  child: Container(
                    width: 140, height: 140,
                    decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
                    child: Center(child: Icon(Icons.lock_outline, size: 60, color: Colors.blue.shade900)),
                  ),
                ),
              ),
              const SizedBox(height: 40),
              const Text('Processing Order', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Color(0xFF003399))),
              const SizedBox(height: 12),
              const Text(
                'Securing your transaction and generating your pickup PIN...', 
                textAlign: TextAlign.center, 
                style: TextStyle(fontSize: 16, color: Colors.grey)
              ),
              const SizedBox(height: 40),
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(color: Colors.grey[50], borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.grey.shade100)),
                child: Column(
                  children: [
                    Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                      const Text('Total Amount', style: TextStyle(color: Colors.grey, fontSize: 15)),
                      Text('\$${widget.amount.toStringAsFixed(2)}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Color(0xFF003399))),
                    ]),
                    const Divider(height: 24),
                    Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                      const Text('Method', style: TextStyle(color: Colors.grey, fontSize: 15)),
                      Text(widget.method, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                    ]),
                  ],
                ),
              ),
              const SizedBox(height: 40),
              const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.blue)),
                  SizedBox(width: 12),
                  Text('Please wait...', style: TextStyle(color: Colors.grey)),
                ],
              ),
              const Spacer(),
            ],
          ),
        ),
      ),
    );
  }
}
