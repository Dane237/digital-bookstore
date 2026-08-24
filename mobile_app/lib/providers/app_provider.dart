import 'package:flutter/foundation.dart';

class UserProfile {
  final int userId;
  final String fullName;
  final String studentId;
  final String email;

  UserProfile({
    required this.userId,
    required this.fullName,
    required this.studentId,
    required this.email,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      userId: json['user_id'],
      fullName: json['full_name'],
      studentId: json['student_id'],
      email: json['email'],
    );
  }
}

class AppProvider extends ChangeNotifier {
  UserProfile? _currentUser;

  UserProfile? get currentUser => _currentUser;
  bool get isLoggedIn => _currentUser != null;

  void setUser(UserProfile user) {
    _currentUser = user;
    notifyListeners();
  }

  void logout() {
    _currentUser = null;
    notifyListeners();
  }
}