import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../services/api_service.dart';
import 'show_pin_screen.dart';

final orderDetailProvider = FutureProvider.family<List<dynamic>, String>((ref, orderId) async {
  final apiService = ApiService();
  return await apiService.fetchOrderItems(orderId);
});

class OrderDetailScreen extends ConsumerWidget {
  final dynamic order;

  const OrderDetailScreen({super.key, required this.order});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final String orderIdStr = (order['order_id'] ?? order['id'] ?? '').toString();
    final itemsAsyncValue = ref.watch(orderDetailProvider(orderIdStr));
    final String status = order['status'] ?? 'Pending';
    final bool isCurrent = status == 'Pending' || status == 'Ready for Pickup';
    final String pickupPin = order['pickup_pin']?.toString() ?? '';

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text('Order Details', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        centerTitle: true,
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: Colors.grey[50], borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.grey.shade200)),
              child: Column(
                children: [
                  _buildDetailRow('Order ID', order['display_id'] ?? orderIdStr),
                  _buildDetailRow('Date', order['created_at'] ?? 'N/A'),
                  _buildDetailRow('Status', status, isStatus: true),
                  _buildDetailRow('Method', order['payment_method'] ?? 'Online'),
                  const Divider(height: 32),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Total Amount', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      Text('\$${double.tryParse(order['total_amount'].toString())?.toStringAsFixed(2) ?? '0.00'}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Color(0xFF003399))),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),

            if (isCurrent) ...[
              const Text('PICKUP TOKEN', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.grey, letterSpacing: 0.5)),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: const Color(0xFF003399).withOpacity(0.05), 
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: const Color(0xFF003399).withOpacity(0.1)),
                ),
                child: Column(
                  children: [
                    if (pickupPin.isNotEmpty) ...[
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.grey.shade200)),
                        child: QrImageView(
                          data: pickupPin,
                          version: QrVersions.auto,
                          size: 140.0,
                          foregroundColor: const Color(0xFF003399),
                        ),
                      ),
                      const SizedBox(height: 20),
                      Text(
                        pickupPin,
                        style: const TextStyle(fontSize: 40, fontWeight: FontWeight.bold, color: Color(0xFF003399), letterSpacing: 6),
                      ),
                    ],
                    const SizedBox(height: 16),
                    _buildPickupRow(Icons.location_on, 'Location', status == 'Ready for Pickup' ? 'Ready at ${order['prepared_location']}' : 'Preparing...'),
                  ],
                ),
              ),
              const SizedBox(height: 40),
            ],

            if (status == 'Picked Up') ...[
              const Text('FULFILLMENT INFO', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.grey, letterSpacing: 0.5)),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: Colors.green.shade50.withOpacity(0.5), borderRadius: BorderRadius.circular(12)),
                child: Column(
                  children: [
                    _buildPickupRow(Icons.check_circle_outline, 'Handover Status', 'Books Collected ✅'),
                    if (order['released_by_staff_id'] != null) ...[
                      const Divider(height: 24),
                      _buildPickupRow(Icons.badge_outlined, 'Released By', 'Staff ID: ${order['released_by_staff_id']}'),
                    ],
                    if (order['picked_up_at'] != null) ...[
                      const Divider(height: 24),
                      _buildPickupRow(Icons.access_time, 'Collected On', order['picked_up_at'].toString()),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 40),
            ],

            const Text('ITEMS IN THIS ORDER', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.grey, letterSpacing: 0.5)),
            const SizedBox(height: 16),
            itemsAsyncValue.when(
              data: (items) {
                if (items.isEmpty) return const Center(child: Text('No items found.'));
                return Column(
                  children: items.map((item) => Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.grey.shade100)),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(item['title'] ?? 'Book', style: const TextStyle(fontWeight: FontWeight.bold)),
                              Text('Quantity: ${item['quantity']}', style: const TextStyle(color: Colors.grey, fontSize: 13)),
                            ],
                          ),
                        ),
                        Text('\$${(item['unit_price'] * item['quantity']).toStringAsFixed(2)}', style: const TextStyle(fontWeight: FontWeight.bold)),
                      ],
                    ),
                  )).toList(),
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, s) => Text('Error: $err'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPickupRow(IconData icon, String label, String value) {
    return Row(
      children: [
        Icon(icon, color: const Color(0xFF003399), size: 20),
        const SizedBox(width: 12),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
            Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
          ],
        ),
      ],
    );
  }

  Widget _buildDetailRow(String label, String value, {bool isStatus = false}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 14)),
          if (isStatus)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(color: Colors.green.shade50, borderRadius: BorderRadius.circular(4)),
              child: Text(value, style: const TextStyle(color: Colors.green, fontWeight: FontWeight.bold, fontSize: 12)),
            )
          else
            Text(value, style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 14)),
        ],
      ),
    );
  }
}
