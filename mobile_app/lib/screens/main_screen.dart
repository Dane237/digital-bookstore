import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/cart_provider.dart';
import '../providers/auth_provider.dart';
import 'home_screen.dart';
import 'cart_screen.dart';
import 'orders_screen.dart';
import 'account_screen.dart';

// Provider to control the selected tab from anywhere in the app
final navigationProvider = StateProvider<int>((ref) => 0);

class MainScreen extends ConsumerStatefulWidget {
  const MainScreen({super.key});

  @override
  ConsumerState<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends ConsumerState<MainScreen> {
  final List<Widget> _screens = [
    const HomeScreen(),
    const CartScreen(),
    const OrdersScreen(),
    const AccountScreen(),
  ];

  void _onItemTapped(int index) {
    final currentIndex = ref.read(navigationProvider);
    if (currentIndex == index) {
       // If tapping Home again, reset to catalog view
       if (index == 0) {
         ref.read(selectedBookProvider.notifier).state = null;
       }
       return;
    }
    
    ref.read(navigationProvider.notifier).state = index;

    if (index == 0) {
      ref.invalidate(booksProvider);
      ref.invalidate(departmentsProvider);
    } else if (index == 2) {
      final user = ref.read(authProvider);
      if (user != null) ref.invalidate(ordersProvider(user.userId));
    }
  }

  @override
  Widget build(BuildContext context) {
    final selectedIndex = ref.watch(navigationProvider);
    final cartItems = ref.watch(cartProvider);
    final cartCount = cartItems.fold(0, (sum, item) => sum + item.quantity);

    return Scaffold(
      body: IndexedStack(index: selectedIndex, children: _screens),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: selectedIndex,
        onTap: _onItemTapped,
        type: BottomNavigationBarType.fixed,
        selectedItemColor: const Color(0xFF003399),
        unselectedItemColor: Colors.grey,
        items: [
          const BottomNavigationBarItem(icon: Icon(Icons.home_outlined), activeIcon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(
            icon: Badge(label: Text(cartCount.toString()), isLabelVisible: cartCount > 0, child: const Icon(Icons.shopping_cart_outlined)),
            activeIcon: Badge(label: Text(cartCount.toString()), isLabelVisible: cartCount > 0, child: const Icon(Icons.shopping_cart)),
            label: 'Cart',
          ),
          const BottomNavigationBarItem(icon: Icon(Icons.assignment_outlined), activeIcon: Icon(Icons.assignment), label: 'Orders'),
          const BottomNavigationBarItem(icon: Icon(Icons.person_outline), activeIcon: Icon(Icons.person), label: 'Account'),
        ],
      ),
    );
  }
}
