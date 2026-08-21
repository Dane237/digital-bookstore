import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../services/api_service.dart';
import '../providers/auth_provider.dart';
import 'register_screen.dart';

class LoginScreen extends ConsumerStatefulWidget {
  final bool isFromCheckout;
  const LoginScreen({super.key, this.isFromCheckout = false});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  bool _obscurePassword = true;

  void _handleLogin() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text.trim();

    if (email.isEmpty || password.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please fill all fields')));
      return;
    }

    setState(() => _isLoading = true);
    final api = ApiService();
    final result = await api.login(email, password);
    
    if (mounted) {
      setState(() => _isLoading = false);
    }

    if (result['status'] == 'success') {
      await ref.read(authProvider.notifier).login(result['user']);
      if (mounted) {
        if (widget.isFromCheckout) {
          Navigator.pop(context);
        } else {
          Navigator.popUntil(context, (route) => route.isFirst);
        }
      }
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['error'] ?? 'Login failed')),
        );
      }
    }
  }

  void _showForgotPasswordFlow() {
    final resetEmailController = TextEditingController();
    bool isRequesting = false;

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Forgot Password', style: TextStyle(fontWeight: FontWeight.bold)),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Enter your registered Gmail to receive a 6-digit verification code.', style: TextStyle(fontSize: 13, color: Colors.grey)),
              const SizedBox(height: 24),
              TextField(
                controller: resetEmailController,
                decoration: InputDecoration(
                  labelText: 'Gmail Address', 
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  prefixIcon: const Icon(Icons.email_outlined),
                ),
                keyboardType: TextInputType.emailAddress,
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF003399), foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))),
              onPressed: isRequesting ? null : () async {
                final email = resetEmailController.text.trim();
                if (email.isEmpty) return;

                setDialogState(() => isRequesting = true);
                try {
                  final response = await http.post(
                    Uri.parse('${ApiService.baseUrl}/forgot-password/'),
                    headers: {'Content-Type': 'application/json'},
                    body: jsonEncode({'email': email}),
                  );
                  
                  if (mounted) {
                    if (response.statusCode == 200) {
                      Navigator.pop(context);
                      _showOTPVerifyDialog(email);
                    } else {
                      setDialogState(() => isRequesting = false);
                      final err = jsonDecode(response.body);
                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: ${err['detail']}'), backgroundColor: Colors.red));
                    }
                  }
                } catch (e) {
                  setDialogState(() => isRequesting = false);
                  if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed: $e')));
                }
              },
              child: isRequesting ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Text('Send Code'),
            ),
          ],
        ),
      ),
    );
  }

  void _showOTPVerifyDialog(String email) {
    final otpController = TextEditingController();
    final newPassController = TextEditingController();
    bool isResetting = false;

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Verify Code', style: TextStyle(fontWeight: FontWeight.bold)),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('Enter the code sent to $email', style: const TextStyle(fontSize: 13, color: Colors.grey)),
              const SizedBox(height: 24),
              TextField(
                controller: otpController,
                style: const TextStyle(letterSpacing: 8, fontSize: 24, fontWeight: FontWeight.bold),
                decoration: InputDecoration(
                  labelText: '6-Digit Code', 
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                textAlign: TextAlign.center,
                keyboardType: TextInputType.number,
                maxLength: 6,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: newPassController,
                decoration: InputDecoration(labelText: 'New Password', border: OutlineInputBorder(borderRadius: BorderRadius.circular(12))),
                obscureText: true,
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))),
              onPressed: isResetting ? null : () async {
                final otp = otpController.text.trim();
                final pass = newPassController.text.trim();
                if (otp.length < 6 || pass.isEmpty) return;

                setDialogState(() => isResetting = true);
                try {
                  final response = await http.post(
                    Uri.parse('${ApiService.baseUrl}/reset-password-confirm/'),
                    headers: {'Content-Type': 'application/json'},
                    body: jsonEncode({'email': email, 'otp': otp, 'new_password': pass}),
                  );
                  
                  if (mounted) {
                    if (response.statusCode == 200) {
                      Navigator.pop(context);
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Password Reset Successful!'), backgroundColor: Colors.green));
                    } else {
                      setDialogState(() => isResetting = false);
                      final err = jsonDecode(response.body);
                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: ${err['detail']}'), backgroundColor: Colors.red));
                    }
                  }
                } catch (e) {
                  setDialogState(() => isResetting = false);
                  if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Reset Failed: $e')));
                }
              },
              child: isResetting ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Text('Reset Password'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text('Login', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        centerTitle: true,
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close, color: Colors.black),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Welcome Back',
              style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Color(0xFF003399)),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            const Text(
              'Sign in to your PUC account to continue.',
              style: TextStyle(fontSize: 16, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 40),
            
            _buildField('Email Address', 'dara.sok@student.puc.edu.kh', _emailController, keyboardType: TextInputType.emailAddress),
            const SizedBox(height: 20),
            _buildField(
              'Password', 
              '••••••••••••', 
              _passwordController, 
              isPassword: true,
              suffixIcon: IconButton(
                icon: Icon(_obscurePassword ? Icons.visibility_off : Icons.visibility, color: Colors.grey),
                onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
              ),
            ),
            
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: _showForgotPasswordFlow,
                child: const Text('Forgot Password?', style: TextStyle(color: Colors.orange, fontWeight: FontWeight.bold)),
              ),
            ),

            const SizedBox(height: 20),
            
            SizedBox(
              height: 56,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF003399),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  elevation: 0,
                ),
                onPressed: _isLoading ? null : _handleLogin,
                child: _isLoading 
                    ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : const Text('Login', style: TextStyle(fontSize: 18, color: Colors.white, fontWeight: FontWeight.bold)),
              ),
            ),
            const SizedBox(height: 24),
            
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text('Don\'t have an account?', style: TextStyle(color: Colors.grey)),
                TextButton(
                  onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const RegisterScreen())), 
                  child: const Text('Create Account', style: TextStyle(color: Color(0xFF003399), fontWeight: FontWeight.bold)),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildField(String label, String hint, TextEditingController controller, {bool isPassword = false, TextInputType? keyboardType, Widget? suffixIcon}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
        const SizedBox(height: 8),
        TextField(
          controller: controller,
          obscureText: isPassword ? _obscurePassword : false,
          keyboardType: keyboardType,
          decoration: InputDecoration(
            hintText: hint,
            suffixIcon: suffixIcon,
            filled: true,
            fillColor: Colors.grey[50],
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.grey.shade300)),
            enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.grey.shade300)),
            focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF003399))),
          ),
        ),
      ],
    );
  }
}
