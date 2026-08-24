import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/auth_provider.dart';
import '../providers/cart_provider.dart';
import 'processing_payment_screen.dart';

class CheckoutScreen extends ConsumerStatefulWidget {
  final double subtotal;
  final List<CartItem> cartItems;

  const CheckoutScreen({super.key, required this.subtotal, required this.cartItems});

  @override
  ConsumerState<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends ConsumerState<CheckoutScreen> {
  String selectedPaymentMethod = 'Stripe';

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authProvider);
    final double total = widget.subtotal;

    return Scaffold(
      backgroundColor: const Color(0xFFFBFBFE),
      appBar: AppBar(
        title: const Text('Secure Checkout', 
          style: TextStyle(color: Color(0xFF1E293B), fontWeight: FontWeight.bold, fontSize: 18)),
        centerTitle: true,
        backgroundColor: Colors.white,
        elevation: 0.5,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Color(0xFF1E293B)),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // CUSTOMER INFO
            _buildSectionLabel('CUSTOMER INFO'),
            _buildInfoCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(user?.username ?? 'Dara Sok', 
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1E293B))),
                  const SizedBox(height: 4),
                  Text(user?.email ?? 'dara.sok@student.puc.edu.kh', 
                    style: const TextStyle(fontSize: 14, color: Color(0xFF64748B))),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // PICKUP DETAILS
            _buildSectionLabel('PICKUP DETAILS'),
            _buildInfoCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.storefront, color: Color(0xFF1E293B), size: 22),
                      SizedBox(width: 12),
                      Text('In-store pickup', 
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF1E293B))),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Row(
                    children: [
                      Icon(Icons.location_on_outlined, color: Color(0xFF64748B), size: 22),
                      SizedBox(width: 12),
                      Text('PUC Bookstore', 
                        style: TextStyle(color: Color(0xFF64748B), fontSize: 15)),
                    ],
                  ),
                  const SizedBox(height: 10),
                  const Padding(
                    padding: EdgeInsets.only(left: 34),
                    child: Text('Pickup PIN will be shown after payment.', 
                      style: TextStyle(fontStyle: FontStyle.italic, color: Color(0xFF94A3B8), fontSize: 13)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // ORDER ITEMS
            _buildSectionLabel('ORDER ITEMS'),
            _buildInfoCard(
              child: Column(
                children: widget.cartItems.map((item) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          '${item.book.title} x${item.quantity}', 
                          style: const TextStyle(fontSize: 14, color: Color(0xFF475569)),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Text('\$${(item.book.price * item.quantity).toStringAsFixed(2)}', 
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF1E293B))),
                    ],
                  ),
                )).toList(),
              ),
            ),
            const SizedBox(height: 16),

            // PAYMENT METHOD
            _buildSectionLabel('PAYMENT METHOD'),
            _buildPaymentMethodContainer(),
            const SizedBox(height: 32),

            // TOTAL
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Total Amount', 
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF1E293B))),
                Text('\$${total.toStringAsFixed(2)}', 
                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF003FB3))),
              ],
            ),
            const SizedBox(height: 24),

            // CONFIRM AND PAY BUTTON
            SizedBox(
              height: 56,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF003FB3),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  elevation: 0,
                ),
                onPressed: () {
                   Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => ProcessingPaymentScreen(
                        amount: total,
                        method: selectedPaymentMethod,
                        cartItems: widget.cartItems,
                        userId: user?.userId ?? 0,
                      ),
                    ),
                  );
                },
                child: const Text(
                  'Confirm and Pay', 
                  style: TextStyle(
                    fontSize: 18, 
                    color: Colors.white, 
                    fontWeight: FontWeight.bold,
                  )
                ),
              ),
            ),
            const SizedBox(height: 30),
          ],
        ),
      ),

      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          boxShadow: [
            BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, -5)),
          ],
        ),
        child: BottomNavigationBar(
          currentIndex: 1, 
          type: BottomNavigationBarType.fixed,
          selectedItemColor: const Color(0xFF003FB3),
          unselectedItemColor: const Color(0xFF94A3B8),
          backgroundColor: Colors.white,
          selectedFontSize: 12,
          unselectedFontSize: 12,
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.home_outlined), label: 'Home'),
            BottomNavigationBarItem(icon: Icon(Icons.shopping_cart), label: 'Cart'),
            BottomNavigationBarItem(icon: Icon(Icons.assignment_outlined), label: 'Orders'),
            BottomNavigationBarItem(icon: Icon(Icons.person_outline), label: 'Account'),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(left: 2, bottom: 8, top: 4),
      child: Text(text, 
        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF94A3B8), letterSpacing: 0.5)),
    );
  }

  Widget _buildInfoCard({required Widget child}) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFEDF2F7)),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.01), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: child,
    );
  }

  Widget _buildPaymentMethodContainer() {
    return _buildInfoCard(
      child: Column(
        children: [
          _buildPaymentOption(
            title: 'Secure Checkout via Stripe',
            subtitle: 'Fast, secure checkout',
            value: 'Stripe',
            isStripe: true,
          ),
          const SizedBox(height: 12),
          _buildPaymentOption(
            title: 'Mobile Banking Transfer',
            subtitle: 'Link to your bank app',
            value: 'Mobile Banking',
          ),
          const SizedBox(height: 12),
          _buildPaymentOption(
            title: 'Direct Card Payment',
            subtitle: 'Pay with Card',
            value: 'Card',
          ),
        ],
      ),
    );
  }

  Widget _buildPaymentOption({
    required String title,
    required String subtitle,
    required String value,
    bool isStripe = false,
  }) {
    final bool isSelected = selectedPaymentMethod == value;

    return InkWell(
      onTap: () => setState(() => selectedPaymentMethod = value),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFFF0F7FF) : const Color(0xFFF8FAFC),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: isSelected ? const Color(0xFF3B82F6) : const Color(0xFFF1F5F9),
            width: isSelected ? 1.5 : 1,
          ),
        ),
        child: Row(
          children: [
            if (isStripe)
              Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: Colors.white,
                  shape: BoxShape.circle,
                  border: Border.all(color: const Color(0xFF10B981).withOpacity(0.2)),
                ),
                child: const Icon(Icons.verified_user_outlined, color: Color(0xFF10B981), size: 20),
              )
            else
              Icon(
                isSelected ? Icons.radio_button_checked : Icons.radio_button_off,
                color: isSelected ? const Color(0xFF3B82F6) : const Color(0xFFCBD5E1),
                size: 24,
              ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, 
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Color(0xFF1E293B))),
                  const SizedBox(height: 2),
                  Text(subtitle, 
                    style: const TextStyle(fontSize: 12, color: Color(0xFF64748B))),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
