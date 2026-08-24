import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/book.dart';
import '../services/api_service.dart';
import 'book_detail_screen.dart';

// Providers for State Management
final searchProvider = StateProvider<String>((ref) => "");
final departmentProvider = StateProvider<String>((ref) => "all");
final selectedBookProvider = StateProvider<Book?>((ref) => null);

final departmentsProvider = FutureProvider<List<String>>((ref) async {
  final apiService = ApiService();
  return await apiService.fetchDepartments();
});

final booksProvider = FutureProvider<List<Book>>((ref) async {
  final apiService = ApiService();
  final query = ref.watch(searchProvider);
  final dept = ref.watch(departmentProvider);
  return await apiService.fetchBooks(department: dept, query: query);
});

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedBook = ref.watch(selectedBookProvider);

    // If a book is selected, show the detail view within this tab
    if (selectedBook != null) {
      return BookDetailScreen(
        book: selectedBook, 
        onBack: () => ref.read(selectedBookProvider.notifier).state = null,
      );
    }

    // Otherwise, show the main catalog
    return const BookCatalogView();
  }
}

class BookCatalogView extends ConsumerStatefulWidget {
  const BookCatalogView({super.key});

  @override
  ConsumerState<BookCatalogView> createState() => _BookCatalogViewState();
}

class _BookCatalogViewState extends ConsumerState<BookCatalogView> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _searchController.text = ref.read(searchProvider);
    _searchController.addListener(() {
      ref.read(searchProvider.notifier).state = _searchController.text;
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final booksAsyncValue = ref.watch(booksProvider);
    final currentDept = ref.watch(departmentProvider);
    final isSearching = ref.watch(searchProvider).isNotEmpty;

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text('PUC Bookstore', style: TextStyle(color: Color(0xFF003399), fontWeight: FontWeight.bold)),
        centerTitle: true,
        backgroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Color(0xFF003399)),
            onPressed: () {
              ref.invalidate(booksProvider);
              ref.invalidate(departmentsProvider);
            },
          ),
        ],
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: Container(
              height: 50,
              decoration: BoxDecoration(color: Colors.grey[50], borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.grey.shade200)),
              child: TextField(
                controller: _searchController,
                decoration: InputDecoration(
                  hintText: 'Search title, ISBN...',
                  prefixIcon: const Icon(Icons.search, color: Color(0xFF003399)),
                  suffixIcon: isSearching ? IconButton(icon: const Icon(Icons.close), onPressed: () { _searchController.clear(); ref.read(searchProvider.notifier).state = ""; }) : null,
                  border: InputBorder.none,
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
          
          SizedBox(
            height: 40,
            child: ref.watch(departmentsProvider).when(
              data: (depts) => ListView.builder(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: depts.length + 1,
                itemBuilder: (context, index) {
                  final dept = index == 0 ? 'all' : depts[index - 1];
                  final isSelected = currentDept == dept;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: Text(dept == 'all' ? 'All Books' : dept),
                      selected: isSelected,
                      onSelected: (val) {
                        if (val) ref.read(departmentProvider.notifier).state = dept;
                      },
                      selectedColor: const Color(0xFF003399),
                      labelStyle: TextStyle(color: isSelected ? Colors.white : Colors.black87),
                      backgroundColor: Colors.grey[50],
                      elevation: 0,
                    ),
                  );
                },
              ),
              loading: () => const SizedBox(),
              error: (_, __) => const SizedBox(),
            ),
          ),
          
          const SizedBox(height: 16),
          Expanded(
            child: booksAsyncValue.when(
              data: (books) {
                if (books.isEmpty) return const Center(child: Text('No books found.'));
                return ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: books.length,
                  itemBuilder: (context, index) => _buildBookCard(context, books[index], ref),
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, stack) => Center(child: Text('Error: $err')),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBookCard(BuildContext context, Book book, WidgetRef ref) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: InkWell(
        onTap: () => ref.read(selectedBookProvider.notifier).state = book,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.white, borderRadius: BorderRadius.circular(16), 
            border: Border.all(color: Colors.grey.shade100),
            boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.02), blurRadius: 10, offset: const Offset(0, 4))]
          ),
          child: Row(
            children: [
              Container(
                width: 80, height: 110,
                decoration: BoxDecoration(color: Colors.grey[100], borderRadius: BorderRadius.circular(8)),
                child: book.coverImg.trim().isNotEmpty 
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(8), 
                        child: Image.network(
                          book.coverImg.trim(), fit: BoxFit.cover, 
                          frameBuilder: (context, child, frame, wasSynchronouslyLoaded) {
                            if (wasSynchronouslyLoaded) return child;
                            return AnimatedOpacity(opacity: frame == null ? 0 : 1, duration: const Duration(milliseconds: 500), curve: Curves.easeOut, child: child);
                          },
                          errorBuilder: (c, e, s) => const Center(child: Icon(Icons.image_not_supported_outlined, color: Colors.grey)),
                        )
                      )
                    : const Center(child: Icon(Icons.book_outlined, color: Colors.grey)),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(book.department, style: const TextStyle(color: Color(0xFF003399), fontSize: 9, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    Text(book.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Color(0xFF003399)), maxLines: 2, overflow: TextOverflow.ellipsis),
                    if (book.author.isNotEmpty)
                      Text(book.author, style: const TextStyle(color: Colors.grey, fontSize: 12), maxLines: 1, overflow: TextOverflow.ellipsis),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('\$${book.price.toStringAsFixed(2)}', style: const TextStyle(color: Color(0xFF003399), fontWeight: FontWeight.bold, fontSize: 18)),
                        Text(
                      book.stockQuantity > 0 ? '${book.stockQuantity} in stock' : 'Out of Stock', 
                      style: TextStyle(
                        color: book.stockQuantity > 0 ? Colors.green : Colors.red, 
                        fontSize: 11, 
                        fontWeight: FontWeight.bold
                      )
                    ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    const Text('View Details →', style: TextStyle(color: Colors.orange, fontWeight: FontWeight.bold, fontSize: 13)),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
