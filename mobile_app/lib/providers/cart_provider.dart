import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/book.dart';

class CartItem {
  final Book book;
  int quantity;

  CartItem({required this.book, this.quantity = 1});

  Map<String, dynamic> toJson() => {
    'book': {
      'book_id': book.bookId,
      'isbn': book.isbn,
      'title': book.title,
      'author': book.author,
      'price': book.price,
      'stock_quantity': book.stockQuantity,
      'description': book.description,
      'cover_img': book.coverImg,
      'departments': book.departments,
    },
    'quantity': quantity,
  };

  factory CartItem.fromJson(Map<String, dynamic> json) {
    return CartItem(
      book: Book.fromJson(json['book']),
      quantity: json['quantity'],
    );
  }
}

class CartNotifier extends StateNotifier<List<CartItem>> {
  CartNotifier() : super([]) {
    _loadCart();
  }

  Future<void> _loadCart() async {
    final prefs = await SharedPreferences.getInstance();
    final cartJson = prefs.getString('cart_items');
    if (cartJson != null) {
      try {
        final List<dynamic> decoded = json.decode(cartJson);
        state = decoded.map((item) => CartItem.fromJson(item)).toList();
      } catch (e) {
        state = [];
      }
    }
  }

  Future<void> _saveCart() async {
    final prefs = await SharedPreferences.getInstance();
    final cartJson = json.encode(state.map((item) => item.toJson()).toList());
    await prefs.setString('cart_items', cartJson);
  }

  /// Adds or updates quantity of a book in the cart.
  /// Returns the actual amount added (0 if limit reached).
  int addCartItem(Book book, int delta) {
    final index = state.indexWhere((item) => item.book.bookId == book.bookId);
    int currentInCart = index != -1 ? state[index].quantity : 0;
    
    if (delta > 0) {
      // Increase quantity
      int maxCanAdd = book.stockQuantity - currentInCart;
      int toAdd = delta > maxCanAdd ? maxCanAdd : delta;

      if (toAdd <= 0) return 0;

      if (index != -1) {
        var newState = [...state];
        newState[index].quantity += toAdd;
        state = newState;
      } else {
        state = [...state, CartItem(book: book, quantity: toAdd)];
      }
      _saveCart();
      return toAdd;
    } else if (delta < 0) {
      // Decrease quantity
      if (index != -1) {
        var newState = [...state];
        newState[index].quantity += delta; // delta is negative
        if (newState[index].quantity <= 0) {
          newState.removeAt(index);
        }
        state = newState;
        _saveCart();
        return delta;
      }
    }
    return 0;
  }

  void removeCartItem(int bookId) {
    state = state.where((item) => item.book.bookId != bookId).toList();
    _saveCart();
  }

  void clearCart() {
    state = [];
    _saveCart();
  }

  int getQuantityInCart(int bookId) {
    final index = state.indexWhere((item) => item.book.bookId == bookId);
    return index != -1 ? state[index].quantity : 0;
  }

  double get subtotal {
    return state.fold(0, (total, item) => total + (item.book.price * item.quantity));
  }
}

final cartProvider = StateNotifierProvider<CartNotifier, List<CartItem>>((ref) {
  return CartNotifier();
});
