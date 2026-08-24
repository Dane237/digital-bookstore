import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/book.dart';
import '../providers/cart_provider.dart';

class BookDetailScreen extends ConsumerStatefulWidget {
  final Book book;
  final VoidCallback onBack;

  const BookDetailScreen({super.key, required this.book, required this.onBack});

  @override
  ConsumerState<BookDetailScreen> createState() => _BookDetailScreenState();
}

class _BookDetailScreenState extends ConsumerState<BookDetailScreen> {
  int _quantity = 1;

  void _addToCart() {
    HapticFeedback.lightImpact();
    final added = ref.read(cartProvider.notifier).addCartItem(widget.book, _quantity);
    
    if (added > 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('${widget.book.title} added to cart!'),
          backgroundColor: Colors.green,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
      );
      setState(() {
        _quantity = 1;
      });
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Cannot add more. You have already reached the stock limit.'),
          backgroundColor: Colors.red,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final cartItems = ref.watch(cartProvider);
    final int currentInCart = ref.read(cartProvider.notifier).getQuantityInCart(widget.book.bookId);
    final int maxCanAdd = widget.book.stockQuantity - currentInCart;

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text('Book Details', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        iconTheme: const IconThemeData(color: Colors.black),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: widget.onBack,
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                height: 280,
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.grey.shade50,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.grey.shade100),
                ),
                child: widget.book.coverImg.isNotEmpty
                  ? ClipRRect(
                      borderRadius: BorderRadius.circular(20),
                      child: Image.network(
                        widget.book.coverImg.trim(),
                        fit: BoxFit.contain,
                        frameBuilder: (context, child, frame, wasSynchronouslyLoaded) {
                          if (wasSynchronouslyLoaded) return child;
                          return AnimatedOpacity(opacity: frame == null ? 0 : 1, duration: const Duration(milliseconds: 500), curve: Curves.easeOut, child: child);
                        },
                        loadingBuilder: (context, child, loadingProgress) {
                          if (loadingProgress == null) return child;
                          return const Center(child: CircularProgressIndicator());
                        },
                        errorBuilder: (c, e, s) => const Center(child: Icon(Icons.image_not_supported_outlined, size: 48, color: Colors.grey)),
                      ),
                    )
                  : const Center(child: Icon(Icons.book_outlined, size: 64, color: Colors.grey)),
              ),
            ),
            const SizedBox(height: 24),
            
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(6)),
              child: Text(
                widget.book.department,
                style: TextStyle(color: Colors.blue.shade900, fontSize: 11, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(height: 12),
            
            Text(widget.book.title, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Color(0xFF003399))),
            if (widget.book.author.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 8.0),
                child: Text('By ${widget.book.author}', style: const TextStyle(fontSize: 16, color: Colors.grey, fontStyle: FontStyle.italic)),
              ),
            const Divider(height: 40, thickness: 1),
            
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('\$${widget.book.price.toStringAsFixed(2)}', style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: Colors.blue.shade900)),
                Row(
                  children: [
                    Icon(Icons.circle, color: widget.book.stockQuantity > 0 ? Colors.green : Colors.red, size: 10),
                    const SizedBox(width: 6),
                    Text(
                      widget.book.stockQuantity > 0 ? '${widget.book.stockQuantity} in stock' : 'Out of Stock',
                      style: TextStyle(fontSize: 14, color: widget.book.stockQuantity > 0 ? Colors.green : Colors.red, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ],
            ),
            if (currentInCart > 0)
              Padding(
                padding: const EdgeInsets.only(top: 8.0),
                child: Text(
                  '($currentInCart already in cart)',
                  style: const TextStyle(color: Colors.orange, fontSize: 13, fontWeight: FontWeight.w500),
                ),
              ),
            const SizedBox(height: 32),
            
            const Text('Description', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(
              widget.book.description.isNotEmpty ? widget.book.description : 'Official PUC course textbook for the current semester.',
              style: const TextStyle(fontSize: 15, color: Colors.black87, height: 1.5),
            ),
            const SizedBox(height: 40),
            
            if (widget.book.stockQuantity > 0 && maxCanAdd > 0) ...[
              Row(
                children: [
                  const Text('Quantity', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const Spacer(),
                  Container(
                    decoration: BoxDecoration(border: Border.all(color: Colors.grey.shade300), borderRadius: BorderRadius.circular(12)),
                    child: Row(
                      children: [
                        IconButton(icon: const Icon(Icons.remove), onPressed: () {
                          HapticFeedback.selectionClick();
                          setState(() { if (_quantity > 1) _quantity--; });
                        }),
                        Padding(padding: const EdgeInsets.symmetric(horizontal: 16), child: Text('$_quantity', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold))),
                        IconButton(icon: const Icon(Icons.add), onPressed: () {
                          HapticFeedback.selectionClick();
                          setState(() { if (_quantity < maxCanAdd) _quantity++; });
                        }),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                height: 60,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF003399), 
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    elevation: 0,
                  ),
                  onPressed: _addToCart,
                  child: const Text('Add to Cart', style: TextStyle(fontSize: 18, color: Colors.white, fontWeight: FontWeight.bold)),
                ),
              ),
            ] else if (widget.book.stockQuantity > 0 && maxCanAdd <= 0) ...[
              const Center(
                child: Text(
                  'Maximum stock reached in cart',
                  style: TextStyle(color: Colors.orange, fontWeight: FontWeight.bold),
                ),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity, height: 60,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.grey.shade200, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)), elevation: 0),
                  onPressed: null,
                  child: const Text('Limit Reached', style: TextStyle(fontSize: 18, color: Colors.grey, fontWeight: FontWeight.bold)),
                ),
              ),
            ] else ...[
              SizedBox(
                width: double.infinity, height: 60,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.grey.shade200, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)), elevation: 0),
                  onPressed: null,
                  child: const Text('Out of Stock', style: TextStyle(fontSize: 18, color: Colors.grey, fontWeight: FontWeight.bold)),
                ),
              ),
            ],
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}
