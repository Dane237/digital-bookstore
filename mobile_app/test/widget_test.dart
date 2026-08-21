import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:puc_digital_bookstore/main.dart';

void main() {
  testWidgets('Bookstore smoke test', (WidgetTester tester) async {
    // Build our app wrapped in ProviderScope and trigger a frame.
    await tester.pumpWidget(
      const ProviderScope(
        child: PUCBookstoreApp(),
      ),
    );

    // Verify that our home screen loads and shows the bookstore title
    expect(find.text('PUC Digital Bookstore'), findsOneWidget);
  });
}