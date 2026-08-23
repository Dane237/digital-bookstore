import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

class User {
  final int userId;
  final String username;
  final String email;
  final String role;
  final String? employeeId;

  User({
    required this.userId,
    required this.username,
    required this.email,
    required this.role,
    this.employeeId,
  });

  Map<String, dynamic> toJson() => {
    'user_id': userId,
    'username': username,
    'email': email,
    'role': role,
    'employee_id': employeeId,
  };

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      userId: json['user_id'] ?? 0,
      username: json['username'] ?? '',
      email: json['email'] ?? '',
      role: json['role'] ?? 'Customer',
      employeeId: json['employee_id'],
    );
  }

  // ALIAS GETTERS
  String get fullName => username;
}

class AuthNotifier extends StateNotifier<User?> {
  AuthNotifier() : super(null) {
    _loadUser();
  }

  Future<void> _loadUser() async {
    final prefs = await SharedPreferences.getInstance();
    final userJson = prefs.getString('user_session');
    if (userJson != null) {
      try {
        state = User.fromJson(json.decode(userJson));
      } catch (e) {
        state = null;
      }
    }
  }

  Future<void> login(Map<String, dynamic> userData) async {
    // FORCE Admin role if the email is the root admin email
    if (userData['email'].toString().toLowerCase() == 'vongchantha2001@gmail.com') {
      userData['role'] = 'Admin';
      userData['employee_id'] = 'PUC-ROOT-001';
    }

    final user = User.fromJson(userData);
    state = user;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('user_session', json.encode(user.toJson()));
  }

  Future<void> logout() async {
    state = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('user_session');
  }

  bool get isStaff => state?.role.toLowerCase() == 'staff' || state?.role.toLowerCase() == 'admin';
  bool get isAdmin => state?.role.toLowerCase() == 'admin';
}

final authProvider = StateNotifierProvider<AuthNotifier, User?>((ref) {
  return AuthNotifier();
});
