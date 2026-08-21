import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';
import 'order_detail_screen.dart';
import 'order_detail_screen.dart';

final ordersProvider = FutureProvider.family<List<dynamic>, int>((ref, userId) async {
  final apiService = ApiService();
  return await apiService.fetchUserOrders(userId);
});

class OrdersScreen extends ConsumerWidget {
  const OrdersScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider);

    if (user == null) {
      return Scaffold(
        backgroundColor: Colors.white,
        appBar: AppBar(
          title: const Text('My Orders', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
          centerTitle: true,
          elevation: 0,
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.lock_outline, size: 64, color: Colors.grey),
              const SizedBox(height: 16),
              const Text('Please login to view your orders.', style: TextStyle(color: Colors.grey)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => Navigator.of(context).pushNamed('/login'),
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF003399)),
                child: const Text('Login', style: TextStyle(color: Colors.white)),
              ),
            ],
          ),
        ),
      );
    }

    final ordersAsyncValue = ref.watch(ordersProvider(user.userId));

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text('My Orders', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        centerTitle: true,
        backgroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Color(0xFF003399)),
            onPressed: () => ref.invalidate(ordersProvider(user.userId)),
          ),
        ],
      ),
      body: ordersAsyncValue.when(
        data: (orders) {
          if (orders.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.assignment_outlined, size: 64, color: Colors.grey),
                  const SizedBox(height: 16),
                  const Text('No orders yet.', style: TextStyle(color: Colors.grey)),
                ],
              ),
            );
          }

          final currentOrders = orders.where((o) => o['status'] == 'Pending' || o['status'] == 'Ready for Pickup').toList();
          final pastOrders = orders.where((o) => o['status'] == 'Picked Up' || o['status'] == 'Cancelled').toList();

          return ListView(
            padding: const EdgeInsets.all(24.0),
            children: [
              if (currentOrders.isNotEmpty) ...[
                const Text('CURRENT ORDER', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey, fontSize: 13, letterSpacing: 0.5)),
                const SizedBox(height: 16),
                ...currentOrders.map((order) => _buildOrderCard(context, ref, order, true)).toList(),
                const SizedBox(height: 32),
              ],
              if (pastOrders.isNotEmpty) ...[
                const Text('PAST ORDERS', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey, fontSize: 13, letterSpacing: 0.5)),
                const SizedBox(height: 16),
                ...pastOrders.map((order) => _buildOrderCard(context, ref, order, false)).toList(),
              ],
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }

  Widget _buildOrderCard(BuildContext context, WidgetRef ref, dynamic order, bool isCurrent) {
    final String displayId = order['display_id']?.toString() ?? order['id']?.toString() ?? 'N/A';
    final String status = order['status']?.toString() ?? 'Pending';
    final String location = order['prepared_location']?.toString() ?? '';

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isCurrent ? Colors.white : Colors.grey[50],
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade200),
        boxShadow: isCurrent ? [
          BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 10, offset: const Offset(0, 5)),
        ] : null,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(displayId, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: status == 'Cancelled' ? Colors.red.shade50 : (status == 'Ready for Pickup' ? Colors.blue.shade50 : (isCurrent ? Colors.green.shade50 : Colors.grey.shade200)),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  status,
                  style: TextStyle(
                    color: status == 'Cancelled' ? Colors.red : (status == 'Ready for Pickup' ? Colors.blue : (isCurrent ? Colors.green : Colors.grey)),
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _buildOrderInfo('Date', order['created_at']?.toString() ?? 'N/A'),
          _buildOrderInfo('Total Paid', '\$${order['total_amount']}', isBlue: true),
          
          if (status == 'Ready for Pickup' && location.isNotEmpty)
            _buildOrderInfo('PICKUP AT', location.toUpperCase(), isBlue: true, isBold: true),
          
          const Divider(height: 32),
          
          if (isCurrent)
            Column(
              children: [
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      side: BorderSide(color: Colors.grey.shade300),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      backgroundColor: Colors.white,
                    ),
                    onPressed: () {
                      Navigator.push(context, MaterialPageRoute(builder: (context) => OrderDetailScreen(order: order)));
                    },
                    child: const Text('View Receipt', style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold)),
                  ),
                ),
                if (status == 'Pending') ...[
                  const SizedBox(height: 8),
                  TextButton(
                    onPressed: () => _handleCancel(context, ref, order),
                    child: const Text('Cancel Order', style: TextStyle(color: Colors.red, fontSize: 13)),
                  ),
                ],
              ],
            )
          else
            SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                onPressed: () {
                  Navigator.push(context, MaterialPageRoute(builder: (context) => OrderDetailScreen(order: order)));
                },
                child: const Text('View Details'),
              ),
            ),
        ],
      ),
    );
  }

  void _handleCancel(BuildContext context, WidgetRef ref, dynamic order) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cancel Order?'),
        content: const Text('Are you sure you want to cancel this order?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('No')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Yes, Cancel', style: TextStyle(color: Colors.red))),
        ],
      ),
    );
    if (confirm == true) {
      final api = ApiService();
      final res = await api.cancelOrder(order['order_id']);
      if (res['status'] == 'success') {
        ref.invalidate(ordersProvider(order['user_id']));
      }
    }
  }

  Widget _buildOrderInfo(String label, String value, {bool isBlue = false, bool isBold = false}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 14)),
          Text(
            value,
            style: TextStyle(
              fontWeight: isBold ? FontWeight.bold : FontWeight.w500,
              fontSize: 14,
              color: isBlue ? const Color(0xFF003399) : Colors.black,
            ),
          ),
        ],
      ),
    );
  }
}
