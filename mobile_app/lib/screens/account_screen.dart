import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/auth_provider.dart';
import 'admin_dashboard_screen.dart';
import 'login_screen.dart';

class AccountScreen extends ConsumerWidget {
  const AccountScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider);

    if (user == null) {
      return Scaffold(
        backgroundColor: Colors.white,
        appBar: AppBar(
          title: const Text('Account', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
          centerTitle: true,
          elevation: 0,
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.person_outline, size: 64, color: Colors.grey),
              const SizedBox(height: 16),
              const Text('Please login to view your account.', style: TextStyle(color: Colors.grey)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () {
                   Navigator.push(context, MaterialPageRoute(builder: (context) => const LoginScreen()));
                },
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF003399)),
                child: const Text('Login', style: TextStyle(color: Colors.white)),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text(
          'Account',
          style: TextStyle(
            color: Color(0xFF1D2939),
            fontWeight: FontWeight.bold,
            fontSize: 24,
          ),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
      ),
      body: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 20.0),
        children: [
          const SizedBox(height: 10),
          // User Profile Card
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFFF9FAFB),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFFEAECF0)),
            ),
            child: Row(
              children: [
                Container(
                  width: 60,
                  height: 60,
                  decoration: const BoxDecoration(
                    color: Color(0xFF003399),
                    shape: BoxShape.circle,
                  ),
                  child: Center(
                    child: Text(
                      user.fullName.isNotEmpty
                          ? user.fullName.split(' ').map((e) => e[0]).take(2).join().toUpperCase()
                          : '?',
                      style: const TextStyle(
                        fontSize: 20,
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        user.fullName,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF1D2939),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        user.email,
                        style: const TextStyle(
                          color: Color(0xFF667085),
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),

          const Text(
            'ACCOUNT SETTINGS',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: Color(0xFF667085),
              letterSpacing: 0.5,
            ),
          ),
          const SizedBox(height: 12),

          Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFFEAECF0)),
            ),
            child: Column(
              children: [
                // Student ID Tile (or Staff ID)
                _buildTile(
                  Icons.credit_card_outlined,
                  user.role.toLowerCase() == 'customer' ? 'Student ID' : 'Staff ID',
                  subtitle: user.employeeId ?? '2026-1234',
                  onTap: () {},
                ),
                _buildDivider(),
                
                if (ref.read(authProvider.notifier).isStaff) ...[
                  _buildTile(
                    Icons.admin_panel_settings_outlined,
                    'Manager Dashboard',
                    onTap: () {
                      Navigator.push(context, MaterialPageRoute(builder: (context) => const AdminDashboardScreen()));
                    },
                  ),
                  _buildDivider(),
                ],

                _buildTile(
                  Icons.info_outline,
                  'Edit Profile',
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Edit Profile feature coming soon')),
                    );
                  },
                ),
                _buildDivider(),

                _buildTile(
                  Icons.info_outline,
                  'Help & Support',
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Support center coming soon')),
                    );
                  },
                ),
                _buildDivider(),

                _buildTile(
                  Icons.info_outline,
                  'About PUC Bookstore',
                  onTap: () {
                    showAboutDialog(
                      context: context,
                      applicationName: 'PUC Digital Bookstore',
                      applicationVersion: '1.0.0',
                      applicationIcon: const Icon(Icons.menu_book, color: Color(0xFF003399), size: 48),
                      children: [
                        const Text('The official digital bookstore system for PUC Students. Securely browse, pay, and pickup your academic textbooks.'),
                      ],
                    );
                  },
                ),
                _buildDivider(),

                _buildTile(
                  Icons.logout,
                  'Logout',
                  isLogout: true,
                  onTap: () async {
                    await ref.read(authProvider.notifier).logout();
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Logged out.')));
                    }
                  },
                ),
              ],
            ),
          ),
          const SizedBox(height: 40),
        ],
      ),
    );
  }

  Widget _buildTile(IconData icon, String title, {String? subtitle, bool isLogout = false, VoidCallback? onTap}) {
    return ListTile(
      leading: Icon(
        icon,
        color: isLogout ? const Color(0xFFD92D20) : const Color(0xFF344054),
        size: 24,
      ),
      title: Text(
        title,
        style: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w600,
          color: isLogout ? const Color(0xFFD92D20) : const Color(0xFF1D2939),
        ),
      ),
      subtitle: subtitle != null
          ? Text(
              subtitle,
              style: const TextStyle(
                fontSize: 14,
                color: Color(0xFF667085),
              ),
            )
          : null,
      trailing: const Icon(
        Icons.chevron_right,
        color: Color(0xFF98A2B3),
        size: 20,
      ),
      onTap: onTap,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    );
  }

  Widget _buildDivider() {
    return const Divider(
      height: 1,
      color: Color(0xFFEAECF0),
      indent: 0,
      endIndent: 0,
    );
  }

}
