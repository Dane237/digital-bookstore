class Book {
  final int bookId;
  final String isbn;
  final String title;
  final String author;
  final double price;
  final int stockQuantity;
  final String description;
  final String coverImg;
  final String? departments;

  Book({
    required this.bookId,
    required this.isbn,
    required this.title,
    required this.author,
    required this.price,
    required this.stockQuantity,
    required this.description,
    required this.coverImg,
    this.departments,
  });

  factory Book.fromJson(Map<String, dynamic> json) {
    return Book(
      bookId: json['book_id'] ?? json['id'] ?? 0,
      isbn: json['isbn'] ?? '',
      title: json['title'] ?? 'Unknown Title',
      author: json['author'] ?? '',
      price: (json['price'] ?? 0.0).toDouble(),
      stockQuantity: json['stock_quantity'] ?? 0,
      description: json['description'] ?? '',
      coverImg: json['cover_img'] ?? '',
      departments: (json['departments'] ?? json['genres'] ?? json['department'] ?? '').toString(),
    );
  }

  // Getters for compatibility across all screens
  String get department => (departments != null && departments!.isNotEmpty) ? departments!.split(',').first : 'General';
  String get genre => department; 
  String get id => bookId.toString();
}
