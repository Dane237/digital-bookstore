import 'package:flutter_stripe/flutter_stripe.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class PaymentService {
  static const String baseUrl = 'https://digital-bookstore-wm64.onrender.com/api';

  Future<bool> processStripePayment(double amount) async {
    try {
      // 1. Request a PaymentIntent Client Secret from your Django backend
      final response = await http.post(
        Uri.parse('$baseUrl/create-payment-intent/'),
        body: {'amount': (amount * 100).toInt().toString()}, // Stripe expects amounts in cents
      );

      if (response.statusCode != 200) return false;

      final jsonResponse = json.decode(response.body);
      final clientSecret = jsonResponse['client_secret'];

      // 2. Initialize the Payment Sheet
      await Stripe.instance.initPaymentSheet(
        paymentSheetParameters: SetupPaymentSheetParameters(
          paymentIntentClientSecret: clientSecret,
          merchantDisplayName: 'PUC Digital Bookstore',
        ),
      );

      // 3. Present the Payment Sheet to the user
      await Stripe.instance.presentPaymentSheet();

      return true; // Payment successful
    } catch (e) {
      print('Payment failed: $e');
      return false;
    }
  }
}