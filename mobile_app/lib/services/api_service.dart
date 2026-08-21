import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/book.dart';
import 'package:flutter/foundation.dart';
import 'dart:io' show Platform;

class ApiService {
  static String get baseUrl {
    if (kIsWeb) {
      return 'http://localhost:8000/api';
    }
    if (Platform.isAndroid) {
      return 'http://10.0.2.2:8000/api';
    } else {
      return 'http://localhost:8000/api';
    }
  }

  Future<List<String>> fetchDepartments() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/departments/'));
      if (response.statusCode == 200) {
        List data = json.decode(response.body);
        return data.cast<String>();
      }
      return [];
    } catch (e) {
      print('API Error (fetchDepartments): $e');
      return [];
    }
  }

  Future<List<Book>> fetchBooks({
    String department = 'all',
    String query = '',
  }) async {
    try {
      final queryParams = {
        'department': department,
        'q': query,
      };
      
      final uri = Uri.parse('$baseUrl/books/').replace(queryParameters: queryParams);
      final response = await http.get(uri);
      
      if (response.statusCode == 200) {
        List data = json.decode(response.body);
        return data.map((json) => Book.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      print('API Error (fetchBooks): $e');
      return [];
    }
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/login/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': password}),
      );
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return {'error': 'Invalid credentials'};
    } catch (e) {
      return {'error': 'Connection failed: $e'};
    }
  }

  Future<Map<String, dynamic>> register(String username, String email, String password, {String? employeeId}) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/register/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'email': email,
          'password': password,
          'employee_id': employeeId,
        }),
      );
      return json.decode(response.body);
    } catch (e) {
      return {'error': 'Connection failed: $e'};
    }
  }

  Future<List<dynamic>> fetchUserOrders(int userId) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/orders/$userId'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return [];
    } catch (e) {
      print('API Error (fetchUserOrders): $e');
      return [];
    }
  }

  Future<List<dynamic>> fetchOrderItems(String orderId) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/orders/detail/$orderId'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return [];
    } catch (e) {
      print('API Error (fetchOrderItems): $e');
      return [];
    }
  }

  Future<Map<String, dynamic>> cancelOrder(int orderId) async {
    try {
      final response = await http.patch(Uri.parse('$baseUrl/orders/$orderId/cancel/'));
      return json.decode(response.body);
    } catch (e) {
      return {'error': 'Connection failed: $e'};
    }
  }
}
