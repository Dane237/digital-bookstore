import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:fl_chart/fl_chart.dart';
import '../services/api_service.dart';
import '../providers/auth_provider.dart';
import 'home_screen.dart';
import 'qr_scanner_screen.dart';

class AdminDashboardScreen extends ConsumerStatefulWidget {
  const AdminDashboardScreen({super.key});

  @override
  ConsumerState<AdminDashboardScreen> createState() => _AdminDashboardScreenState();
}

class _AdminDashboardScreenState extends ConsumerState<AdminDashboardScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  Map<String, dynamic>? _analytics;
  bool _isLoadingAnalytics = true;
  List<dynamic> _pendingOrders = [];
  List<dynamic> _readyOrders = [];
  List<dynamic> _pickedUpOrders = [];
  List<dynamic> _cancelledOrders = [];
  
  final TextEditingController _inventorySearchController = TextEditingController();
  String _inventorySearchQuery = "";

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _refreshAll();
    _inventorySearchController.addListener(() {
      setState(() => _inventorySearchQuery = _inventorySearchController.text.toLowerCase());
    });
  }

  Future<void> _refreshAll() async {
    await Future.wait([
      _fetchAnalytics(),
      _fetchOrdersByStatus('Pending'),
      _fetchOrdersByStatus('Ready for Pickup'),
      _fetchOrdersByStatus('Picked Up'),
      _fetchOrdersByStatus('Cancelled'),
    ]);
  }

  Future<void> _fetchAnalytics() async {
    try {
      final response = await http.get(Uri.parse('${ApiService.baseUrl}/staff/analytics/'));
      if (response.statusCode == 200) {
        if (mounted) {
          setState(() {
            _analytics = json.decode(response.body);
            _isLoadingAnalytics = false;
          });
        }
      }
    } catch (e) {
      if (mounted) setState(() => _isLoadingAnalytics = false);
    }
  }

  Future<void> _fetchOrdersByStatus(String status) async {
    try {
      final response = await http.get(Uri.parse('${ApiService.baseUrl}/admin/orders/?status=$status'));
      if (response.statusCode == 200) {
        if (mounted) {
          setState(() {
            if (status == 'Pending') _pendingOrders = json.decode(response.body);
            if (status == 'Ready for Pickup') _readyOrders = json.decode(response.body);
            if (status == 'Picked Up') _pickedUpOrders = json.decode(response.body);
            if (status == 'Cancelled') _cancelledOrders = json.decode(response.body);
          });
        }
      }
    } catch (_) {}
  }

  Future<void> _lookupAndProcessOrder(String pin) async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      final response = await http.get(Uri.parse('${ApiService.baseUrl}/admin/orders/lookup/$pin'));
      if (response.statusCode == 200) {
        HapticFeedback.vibrate();
        final order = json.decode(response.body);
        if (!mounted) return;
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('PIN VALID ✅', style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Customer: ${order['customer_name']}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                const SizedBox(height: 12),
                Text('Order Total: \$${double.tryParse(order['total_amount'].toString())?.toStringAsFixed(2) ?? '0.00'}'),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(8)),
                  child: Row(
                    children: [
                      const Icon(Icons.location_on, color: Color(0xFF003399)),
                      const SizedBox(width: 12),
                      Text('LOC: ${order['prepared_location']}', style: const TextStyle(fontSize: 16, color: Color(0xFF003399), fontWeight: FontWeight.bold)),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                const Text('Retrieve books and release to student.', style: TextStyle(fontSize: 13, color: Colors.grey)),
              ],
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
              ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))),
                onPressed: () async {
                  final user = ref.read(authProvider);
                  final staffId = user?.userId ?? 0;
                  final fulfillRes = await http.patch(Uri.parse('${ApiService.baseUrl}/admin/orders/${order['order_id']}/pickup/?staff_id=$staffId'));
                  if (fulfillRes.statusCode == 200) {
                    if (!mounted) return;
                    Navigator.pop(context);
                    messenger.showSnackBar(const SnackBar(content: Text('Order Status: Picked Up ✅'), backgroundColor: Colors.green));
                    _refreshAll();
                  }
                }, 
                child: const Text('RELEASE BOOKS')
              ),
            ],
          )
        );
      } else {
        final errorData = json.decode(response.body);
        messenger.showSnackBar(SnackBar(content: Text('REJECTED: ${errorData['detail'] ?? 'Invalid PIN.'}'), backgroundColor: Colors.red));
      }
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text('Error: $e')));
    }
  }

  void _verifyPinFlow() {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Manual PIN Entry'),
        content: TextField(
          controller: controller, 
          decoration: const InputDecoration(hintText: 'Enter 6-digit PIN', border: OutlineInputBorder()),
          keyboardType: TextInputType.number,
          maxLength: 6,
          textAlign: TextAlign.center,
          style: const TextStyle(letterSpacing: 4, fontSize: 20, fontWeight: FontWeight.bold),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () {
              final pin = controller.text.trim();
              if (pin.length < 6) return;
              Navigator.pop(context);
              _lookupAndProcessOrder(pin);
            }, 
            child: const Text('VERIFY')
          ),
        ],
      ),
    );
  }

  void _startScanFlow() async {
    final String? result = await Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const QrScannerScreen()),
    );
    if (result != null) {
      // Ensure the result is trimmed of any whitespace/newlines from the scanner
      _lookupAndProcessOrder(result.trim());
    }
  }

  void _showIsbnImportDialog() {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('ISBN Metadata Import'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Uses Google Books API to fetch book details.', style: TextStyle(fontSize: 12, color: Colors.grey)),
            const SizedBox(height: 16),
            TextField(controller: controller, decoration: const InputDecoration(hintText: 'Enter ISBN', border: OutlineInputBorder())),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () async {
              final isbn = controller.text.trim();
              if (isbn.isEmpty) return;
              final messenger = ScaffoldMessenger.of(context);
              final navigator = Navigator.of(context);
              try {
                final response = await http.get(Uri.parse('${ApiService.baseUrl}/admin/isbn-lookup/$isbn'));
                if (response.statusCode == 200) {
                  final data = json.decode(response.body);
                  if (data.containsKey('error')) {
                    messenger.showSnackBar(SnackBar(content: Text('ISBN not found: ${data['error']}')));
                    return;
                  }
                  navigator.pop();
                  if (!mounted) return;
                  _showManualAddDialog(existingBook: {
                    'isbn': isbn,
                    'title': data['title'],
                    'author': data['author'],
                    'description': data['description'],
                    'cover_img': data['cover_img'],
                    'price': 0.0,
                    'stock_quantity': 10,
                  });
                } else {
                  messenger.showSnackBar(const SnackBar(content: Text('Failed to connect to service.')));
                }
              } catch (e) {
                messenger.showSnackBar(SnackBar(content: Text('Error: $e')));
              }
            }, 
            child: const Text('FETCH DETAILS')
          ),
        ],
      ),
    );
  }

  void _showManualAddDialog({Map<String, dynamic>? existingBook}) {
    final isEdit = existingBook != null && existingBook.containsKey('book_id');
    final titleController = TextEditingController(text: existingBook?['title']);
    final authorController = TextEditingController(text: existingBook?['author']);
    final isbnController = TextEditingController(text: existingBook?['isbn']);
    final priceController = TextEditingController(text: existingBook?['price']?.toString());
    final stockController = TextEditingController(text: existingBook?['stock_quantity']?.toString());
    final coverImgController = TextEditingController(text: existingBook?['cover_img']);
    final descController = TextEditingController(text: existingBook?['description']);
    String selectedDept = existingBook?['department'] ?? '';

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) {
          final departmentsAsync = ref.watch(departmentsProvider);
          return AlertDialog(
            title: Text(isEdit ? 'Update Book' : 'Add Book Manually'),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(controller: titleController, decoration: const InputDecoration(labelText: 'Title')),
                  TextField(controller: authorController, decoration: const InputDecoration(labelText: 'Author')),
                  TextField(controller: isbnController, decoration: const InputDecoration(labelText: 'ISBN'), readOnly: isEdit),
                  Row(children: [
                    Expanded(child: TextField(controller: priceController, decoration: const InputDecoration(labelText: 'Price'), keyboardType: TextInputType.number)),
                    const SizedBox(width: 12),
                    Expanded(child: TextField(controller: stockController, decoration: const InputDecoration(labelText: 'Stock'), keyboardType: TextInputType.number)),
                  ]),
                  const SizedBox(height: 12),
                  departmentsAsync.when(
                    data: (departmentsList) {
                      if (selectedDept.isEmpty && departmentsList.isNotEmpty) selectedDept = departmentsList.first;
                      return DropdownButtonFormField<String>(
                        value: departmentsList.contains(selectedDept) ? selectedDept : (departmentsList.isNotEmpty ? departmentsList.first : null),
                        decoration: const InputDecoration(labelText: 'Department'),
                        items: [
                          ...departmentsList.map((d) => DropdownMenuItem(value: d, child: Text(d))),
                          const DropdownMenuItem(value: 'NEW_DEPT', child: Text('+ Add New Department')),
                        ],
                        onChanged: (val) async {
                          if (val == 'NEW_DEPT') {
                            final newDept = await _showNewDeptDialog();
                            if (newDept != null && newDept.isNotEmpty) setDialogState(() => selectedDept = newDept);
                          } else {
                            setDialogState(() => selectedDept = val!);
                          }
                        },
                      );
                    },
                    loading: () => const CircularProgressIndicator(),
                    error: (_, __) => const Text('Error'),
                  ),
                  TextField(controller: coverImgController, decoration: const InputDecoration(labelText: 'Cover URL')),
                  TextField(controller: descController, decoration: const InputDecoration(labelText: 'Description'), maxLines: 3),
                ],
              ),
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
              ElevatedButton(
                onPressed: () async {
                  final payload = {
                    'title': titleController.text, 
                    'author': authorController.text,
                    'isbn': isbnController.text,
                    'price': double.tryParse(priceController.text) ?? 0.0,
                    'stock_quantity': int.tryParse(stockController.text) ?? 0,
                    'department_name': selectedDept, 'description': descController.text, 'cover_img': coverImgController.text,
                  };
                  final messenger = ScaffoldMessenger.of(context);
                  Navigator.pop(context);
                  try {
                    final response = await http.post(Uri.parse('${ApiService.baseUrl}/admin/books/add/'), headers: {'Content-Type': 'application/json'}, body: json.encode(payload));
                    if (response.statusCode == 200) {
                      if (mounted) {
                        messenger.showSnackBar(const SnackBar(content: Text('Inventory Updated!')));
                        ref.invalidate(booksProvider);
                        ref.invalidate(departmentsProvider);
                        _fetchAnalytics();
                      }
                    }
                  } catch (e) {
                    if (mounted) messenger.showSnackBar(SnackBar(content: Text('Error: $e')));
                  }
                }, 
                child: Text(isEdit ? 'Update' : 'Add Book')
              ),
            ],
          );
        },
      ),
    );
  }

  Future<String?> _showNewDeptDialog() async {
    final controller = TextEditingController();
    return showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add New Department'),
        content: TextField(controller: controller, decoration: const InputDecoration(hintText: 'e.g. Science'), autofocus: true),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.pop(context, controller.text.trim()), child: const Text('Add')),
        ],
      ),
    );
  }

  Future<void> _deleteBook(int bookId) async {
    final confirm = await showDialog<bool>(context: context, builder: (context) => AlertDialog(title: const Text('Confirm Delete'), content: const Text('Remove from catalog?'), actions: [TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')), ElevatedButton(onPressed: () => Navigator.pop(context, true), child: const Text('Delete'))]));
    if (confirm != true) return;
    final messenger = ScaffoldMessenger.of(context);
    try {
      final response = await http.delete(Uri.parse('${ApiService.baseUrl}/admin/books/$bookId/'));
      if (response.statusCode == 200) {
        if (mounted) {
          messenger.showSnackBar(const SnackBar(content: Text('Book deleted successfully.'), backgroundColor: Colors.green));
          ref.invalidate(booksProvider);
          _fetchAnalytics();
        }
      } else {
        final err = json.decode(response.body);
        if (mounted) {
          messenger.showSnackBar(SnackBar(
            content: Text('REJECTED: ${err['detail'] ?? "Could not delete book."}'), 
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 4),
          ));
        }
      }
    } catch (e) {
      if (mounted) messenger.showSnackBar(SnackBar(content: Text('Network Error: $e'), backgroundColor: Colors.red));
    }
  }

  Future<void> _cancelOrder(int orderId) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cancel Order?'),
        content: const Text('This will restore book stock and mark the order as Cancelled.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('No')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(context, true), 
            child: const Text('Yes, Cancel', style: TextStyle(color: Colors.white))
          ),
        ],
      ),
    );
    if (confirm != true) return;

    final messenger = ScaffoldMessenger.of(context);
    try {
      final response = await http.patch(Uri.parse('${ApiService.baseUrl}/orders/$orderId/cancel/'));
      if (response.statusCode == 200) {
        if (mounted) {
          HapticFeedback.mediumImpact();
          _refreshAll();
          messenger.showSnackBar(const SnackBar(content: Text('Order Cancelled ✅')));
        }
      } else {
        final err = json.decode(response.body);
        messenger.showSnackBar(SnackBar(content: Text('Error: ${err['detail']}')));
      }
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text('Error: $e')));
    }
  }

  Future<void> _prepareOrder(int orderId) async {
    final controller = TextEditingController(text: 'Shelf B-4');
    final loc = await showDialog<String>(context: context, builder: (context) => AlertDialog(title: const Text('Pickup Location'), content: TextField(controller: controller), actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')), ElevatedButton(onPressed: () => Navigator.pop(context, controller.text), child: const Text('Confirm'))]));
    if (loc == null || loc.isEmpty) return;
    final messenger = ScaffoldMessenger.of(context);
    try {
      final user = ref.read(authProvider);
      final staffId = user?.userId ?? 0;
      final response = await http.patch(Uri.parse('${ApiService.baseUrl}/admin/orders/$orderId/prepare/?location=$loc&staff_id=$staffId'));
      if (response.statusCode == 200) {
        if (mounted) { 
          HapticFeedback.heavyImpact();
          _refreshAll(); 
          messenger.showSnackBar(const SnackBar(content: Text('Order Status: Ready!'))); 
        }
      }
    } catch (e) { if (mounted) messenger.showSnackBar(SnackBar(content: Text('Error: $e'))); }
  }

  void _showAddStaffDialog() {
    final nameController = TextEditingController();
    final idController = TextEditingController();
    final emailController = TextEditingController();
    final passController = TextEditingController();
    bool isSaving = false;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Add Staff Member'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(controller: nameController, decoration: const InputDecoration(labelText: 'Full Name')),
                TextField(controller: idController, decoration: const InputDecoration(labelText: 'Staff ID (e.g. EMP-101)')),
                TextField(controller: emailController, decoration: const InputDecoration(labelText: 'Email Address')),
                TextField(controller: passController, decoration: const InputDecoration(labelText: 'Assign Password'), obscureText: true),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: isSaving ? null : () async {
                if (emailController.text.isEmpty || passController.text.isEmpty) return;
                setDialogState(() => isSaving = true);
                try {
                  final response = await http.post(
                    Uri.parse('${ApiService.baseUrl}/admin/staff/add/'),
                    headers: {'Content-Type': 'application/json'},
                    body: json.encode({
                      'username': nameController.text,
                      'email': emailController.text,
                      'password': passController.text,
                      'employee_id': idController.text,
                    }),
                  );
                  if (mounted) {
                    if (response.statusCode == 200) {
                      Navigator.pop(context);
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Staff account created!'), backgroundColor: Colors.green));
                    } else {
                      setDialogState(() => isSaving = false);
                      final err = json.decode(response.body);
                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: ${err['detail']}')));
                    }
                  }
                } catch (e) {
                  setDialogState(() => isSaving = false);
                  if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed: $e')));
                }
              },
              child: isSaving ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Text('Create Account'),
            ),
          ],
        ),
      ),
    );
  }

  void _runSeeder() async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      final response = await http.post(Uri.parse('${ApiService.baseUrl}/admin/seed/'));
      if (response.statusCode == 200) {
        if (mounted) {
          messenger.showSnackBar(const SnackBar(content: Text('System Verified! Login as admin@puc.edu.kh')));
          _refreshAll();
          ref.invalidate(booksProvider);
          ref.invalidate(departmentsProvider);
        }
      }
    } catch (e) { if (mounted) messenger.showSnackBar(SnackBar(content: Text('Seeding Error: $e'))); }
  }

  void _wipeInventory() async {
    final confirm = await showDialog<bool>(
      context: context, 
      builder: (context) => AlertDialog(
        title: const Text('Wipe All Books?'), 
        content: const Text('This will permanently delete ALL books from the catalog. This cannot be undone.'), 
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')), 
          ElevatedButton(style: ElevatedButton.styleFrom(backgroundColor: Colors.red), onPressed: () => Navigator.pop(context, true), child: const Text('Wipe All', style: TextStyle(color: Colors.white)))
        ]
      )
    );
    if (confirm != true) return;
    final messenger = ScaffoldMessenger.of(context);
    try {
      final response = await http.post(Uri.parse('${ApiService.baseUrl}/admin/wipe-inventory/'));
      if (response.statusCode == 200) {
        if (mounted) {
          messenger.showSnackBar(const SnackBar(content: Text('Inventory Wiped.')));
          _refreshAll();
          ref.invalidate(booksProvider);
          ref.invalidate(departmentsProvider);
        }
      }
    } catch (e) { if (mounted) messenger.showSnackBar(SnackBar(content: Text('Error: $e'))); }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text('Manager Dashboard', style: TextStyle(fontWeight: FontWeight.bold)),
        bottom: TabBar(
          controller: _tabController,
          labelColor: const Color(0xFF003399),
          indicatorColor: const Color(0xFF003399),
          tabs: const [Tab(text: 'Reports'), Tab(text: 'Inventory'), Tab(text: 'Flow'), Tab(text: 'History')],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [_buildReportsTab(), _buildInventoryTab(), _buildOrdersFlowTab(), _buildHistoryTab()],
      ),
    );
  }

  Widget _buildReportsTab() {
    if (_isLoadingAnalytics) return const Center(child: CircularProgressIndicator());
    
    final trend = _analytics?['revenue_trend'] as List? ?? [];
    final salesDept = _analytics?['sales_by_department'] as List? ?? [];
    final topBooks = _analytics?['top_selling'] as List? ?? [];
    final userState = ref.watch(authProvider);
    final bool isAdmin = userState?.role.toLowerCase() == 'admin' || userState?.email.toLowerCase() == 'vongchantha2001@gmail.com';
    
    return RefreshIndicator(
      onRefresh: _refreshAll,
      child: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('OVERVIEW', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey, fontSize: 12)),
              Row(
                children: [
                  IconButton(onPressed: _refreshAll, icon: const Icon(Icons.refresh, size: 20, color: Color(0xFF003399))),
                  if (isAdmin) ...[
                    TextButton.icon(onPressed: _showAddStaffDialog, icon: const Icon(Icons.person_add_alt_1_outlined, size: 16), label: const Text('Add Staff', style: TextStyle(fontSize: 11))),
                  ],
                ],
              ),
            ],
          ),
          const SizedBox(height: 12),
          _buildStatCard('Total Revenue', '\$${_analytics?['total_revenue']?.toStringAsFixed(2) ?? '0.00'}', Icons.payments, Colors.green),
          _buildStatCard('Total Orders', '${_analytics?['total_orders'] ?? 0}', Icons.shopping_bag, Colors.blue),
          _buildStatCard('Total Assets Worth', '\$${_analytics?['business_value']?.toStringAsFixed(2) ?? '0.00'}', Icons.account_balance_wallet_outlined, Colors.orange),
          
          const SizedBox(height: 32),
          const Text('REVENUE TREND (LAST 7 DAYS)', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey, fontSize: 12)),
          const SizedBox(height: 20),
          if (trend.isNotEmpty)
            SizedBox(
              height: 180,
              child: BarChart(
                BarChartData(
                  alignment: BarChartAlignment.spaceAround,
                  maxY: trend.fold(0.0, (m, e) => (e['revenue'] as double) > m ? e['revenue'] as double : m) + 50,
                  barGroups: trend.asMap().entries.map((e) {
                    return BarChartGroupData(
                      x: e.key,
                      barRods: [BarChartRodData(toY: e.value['revenue'], color: const Color(0xFF003399), width: 16, borderRadius: BorderRadius.circular(4))],
                    );
                  }).toList(),
                  titlesData: FlTitlesData(
                    leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (val, meta) {
                          if (val.toInt() >= trend.length) return const SizedBox();
                          final date = trend[val.toInt()]['date'] as String;
                          return Text(date.substring(8), style: const TextStyle(fontSize: 10, color: Colors.grey));
                        },
                      ),
                    ),
                  ),
                  gridData: const FlGridData(show: false),
                  borderData: FlBorderData(show: false),
                ),
              ),
            ),

          const SizedBox(height: 40),
          const Text('TOP SELLING BOOKS', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey, fontSize: 12)),
          const SizedBox(height: 16),
          if (topBooks.isNotEmpty)
            ...topBooks.map((item) => ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const CircleAvatar(backgroundColor: Color(0xFF003399), child: Icon(Icons.star, color: Colors.white, size: 16)),
              title: Text(item['title'], style: const TextStyle(fontWeight: FontWeight.bold)),
              trailing: Text('${item['sold']} sold', style: const TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
            ))
          else
            const Text('No sales yet.', style: TextStyle(color: Colors.grey, fontSize: 13)),

          const SizedBox(height: 40),
          const Text('REVENUE BY DEPARTMENT', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey, fontSize: 12)),
          const SizedBox(height: 16),
          if (salesDept.isNotEmpty)
            ...salesDept.map((item) {
              final rev = item['revenue'] ?? 0.0;
              final maxRev = salesDept.fold(0.0, (m, e) => (e['revenue'] as double) > m ? e['revenue'] as double : m);
              return Column(
                children: [
                  Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                    Text(item['name'] ?? ''),
                    Text('\$${rev.toStringAsFixed(2)}', style: const TextStyle(fontWeight: FontWeight.bold)),
                  ]),
                  const SizedBox(height: 8),
                  LinearProgressIndicator(value: (rev / (maxRev == 0 ? 1 : maxRev)).clamp(0, 1), backgroundColor: Colors.grey[100], color: const Color(0xFF003399), minHeight: 8),
                  const SizedBox(height: 16),
                ],
              );
            })
          else
            const Text('No sales by department yet.', style: TextStyle(color: Colors.grey, fontSize: 13)),
          
          const SizedBox(height: 40),
        ],
      ),
    );
  }

  Widget _buildInventoryTab() {
    final booksAsync = ref.watch(booksProvider);
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(24, 24, 24, 0),
          child: Row(children: [
            Expanded(child: ElevatedButton.icon(onPressed: _showIsbnImportDialog, icon: const Icon(Icons.auto_awesome), label: const Text('ISBN Metadata'))),
            const SizedBox(width: 12),
            Expanded(child: OutlinedButton.icon(onPressed: () => _showManualAddDialog(), icon: const Icon(Icons.add), label: const Text('Manual Add'))),
          ]),
        ),
        Padding(
          padding: const EdgeInsets.all(24),
          child: TextField(
            controller: _inventorySearchController,
            decoration: InputDecoration(
              hintText: "Search inventory...",
              prefixIcon: const Icon(Icons.search),
              filled: true, fillColor: Colors.grey[50],
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
            ),
          ),
        ),
        Expanded(
          child: booksAsync.when(
            data: (books) {
              final filtered = books.where((b) => b.title.toLowerCase().contains(_inventorySearchQuery) || b.isbn.contains(_inventorySearchQuery)).toList();
              if (filtered.isEmpty) return const Center(child: Text('No books in inventory.'));
              return ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                itemCount: filtered.length,
                itemBuilder: (context, index) {
                  final b = filtered[index];
                  return Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    child: InkWell(
                      onTap: () => _showManualAddDialog(existingBook: {'book_id': b.bookId, 'title': b.title, 'isbn': b.isbn, 'price': b.price, 'stock_quantity': b.stockQuantity, 'department': b.department, 'cover_img': b.coverImg, 'description': b.description, 'author': b.author}),
                      borderRadius: BorderRadius.circular(12),
                      child: Padding(
                        padding: const EdgeInsets.all(12.0),
                        child: Row(
                          children: [
                            Container(
                              width: 60, height: 80,
                              decoration: BoxDecoration(color: Colors.grey[100], borderRadius: BorderRadius.circular(8)),
                              child: b.coverImg.isNotEmpty 
                                  ? ClipRRect(borderRadius: BorderRadius.circular(8), child: Image.network(b.coverImg, fit: BoxFit.cover, errorBuilder: (c,e,s) => const Icon(Icons.book_outlined)))
                                  : const Icon(Icons.book_outlined),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(b.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16), maxLines: 1, overflow: TextOverflow.ellipsis),
                                  const SizedBox(height: 4),
                                  Text('Author: ${b.author.isEmpty ? "Unknown" : b.author}', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                                  Text('ISBN: ${b.isbn}', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                                  const SizedBox(height: 8),
                                  Row(
                                    children: [
                                      Text('\$${b.price.toStringAsFixed(2)}', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF003399))),
                                      const SizedBox(width: 12),
                                      Text('Stock: ${b.stockQuantity}', style: TextStyle(color: b.stockQuantity > 0 ? Colors.green : Colors.red, fontWeight: FontWeight.bold, fontSize: 12)),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                            IconButton(icon: const Icon(Icons.edit, size: 20), onPressed: () => _showManualAddDialog(existingBook: {'book_id': b.bookId, 'title': b.title, 'isbn': b.isbn, 'price': b.price, 'stock_quantity': b.stockQuantity, 'department': b.department, 'cover_img': b.coverImg, 'description': b.description, 'author': b.author})),
                            IconButton(icon: const Icon(Icons.delete_outline, color: Colors.red, size: 20), onPressed: () => _deleteBook(b.bookId)),
                          ],
                        ),
                      ),
                    ),
                  );
                },
              );
            },
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, s) => Text('Error: $e'),
          ),
        ),
      ],
    );
  }

  Widget _buildOrdersFlowTab() {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: const Color(0xFF003399).withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFF003399).withValues(alpha: 0.1)),
          ),
          child: Column(
            children: [
              const Text('STUDENT HANDOVER', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Color(0xFF003399))),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: _startScanFlow, 
                      icon: const Icon(Icons.qr_code_scanner), 
                      label: const Text('SCAN QR'), 
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF003399), 
                        minimumSize: const Size.fromHeight(56), 
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      )
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _verifyPinFlow, 
                      icon: const Icon(Icons.keyboard_alt_outlined), 
                      label: const Text('TYPE PIN'), 
                      style: OutlinedButton.styleFrom(
                        minimumSize: const Size.fromHeight(56), 
                        side: const BorderSide(color: Color(0xFF003399)),
                        foregroundColor: const Color(0xFF003399),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      )
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 32),
        const Text('1. PENDING (PREPARE)', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey, fontSize: 12)),
        const SizedBox(height: 16),
        if (_pendingOrders.isEmpty) const Padding(padding: EdgeInsets.symmetric(vertical: 20), child: Center(child: Text('No pending orders.', style: TextStyle(color: Colors.grey)))),
        ..._pendingOrders.map((o) => Card(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(o['display_id'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    Text('\$${o['total_amount']}', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF003399))),
                  ],
                ),
                const SizedBox(height: 8),
                Text('Customer: ${o['customer_name']}', style: const TextStyle(color: Colors.black87)),
                const SizedBox(height: 4),
                Text('Items: ${o['items_summary'] ?? 'No items'}', style: const TextStyle(color: Colors.blue, fontSize: 13, fontWeight: FontWeight.w500)),
                const Divider(height: 24),
                Row(
                  children: [
                    Expanded(
                      child: TextButton(
                        onPressed: () => _cancelOrder(o['order_id']), 
                        style: TextButton.styleFrom(foregroundColor: Colors.red),
                        child: const Text('CANCEL ORDER')
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () => _prepareOrder(o['order_id']), 
                        style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF003399), foregroundColor: Colors.white),
                        child: const Text('PREPARE')
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        )),
        const SizedBox(height: 32),
        const Text('2. READY (PICKUP)', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey, fontSize: 12)),
        const SizedBox(height: 16),
        if (_readyOrders.isEmpty) const Padding(padding: EdgeInsets.symmetric(vertical: 20), child: Center(child: Text('No orders ready for pickup.', style: TextStyle(color: Colors.grey)))),
        ..._readyOrders.map((o) => Card(
          color: Colors.green.shade50, 
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(o['display_id'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    const Icon(Icons.hourglass_empty, color: Colors.green, size: 20),
                  ],
                ),
                const SizedBox(height: 8),
                Text('Loc: ${o['prepared_location']} • \$${o['total_amount']}', style: const TextStyle(fontWeight: FontWeight.bold)),
                Text('Customer: ${o['customer_name']}', style: const TextStyle(fontSize: 13)),
                const SizedBox(height: 4),
                Text('Items: ${o['items_summary'] ?? ''}', style: const TextStyle(fontSize: 12)),
              ],
            ),
          ),
        )),
      ],
    );
  }

  Widget _buildHistoryTab() {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        const Text('COMPLETED ORDERS', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey, fontSize: 12)),
        const SizedBox(height: 12),
        if (_pickedUpOrders.isEmpty) const Padding(padding: EdgeInsets.symmetric(vertical: 20), child: Center(child: Text('No history yet.', style: TextStyle(color: Colors.grey)))),
        ..._pickedUpOrders.map((o) => Card(child: ListTile(
          title: Text(o['display_id'], style: const TextStyle(fontWeight: FontWeight.bold)), 
          subtitle: Text('Customer: ${o['customer_name']}\nItems: ${o['items_summary'] ?? ''}'), 
          trailing: const Icon(Icons.check_circle, color: Colors.blue),
          isThreeLine: true,
        ))),
        const SizedBox(height: 32),
        const Text('CANCELLED ORDERS', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey, fontSize: 12)),
        const SizedBox(height: 12),
        if (_cancelledOrders.isEmpty) const Padding(padding: EdgeInsets.symmetric(vertical: 20), child: Center(child: Text('No cancelled orders.', style: TextStyle(color: Colors.grey, fontSize: 12)))),
        ..._cancelledOrders.map((o) => Card(
          color: Colors.red.shade50,
          child: ListTile(
            title: Text(o['display_id'], style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.red)), 
            subtitle: Text('Customer: ${o['customer_name']}\nItems: ${o['items_summary'] ?? ''}'), 
            trailing: const Icon(Icons.cancel_outlined, color: Colors.red),
            isThreeLine: true,
          )
        )),
      ],
    );
  }

  Widget _buildStatCard(String label, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(20), margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.05), borderRadius: BorderRadius.circular(16), border: Border.all(color: color.withValues(alpha: 0.1))),
      child: Row(children: [Icon(icon, color: color, size: 24), const SizedBox(width: 16), Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(label, style: const TextStyle(color: Colors.grey, fontSize: 13)), Text(value, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold))])]),
    );
  }
}
