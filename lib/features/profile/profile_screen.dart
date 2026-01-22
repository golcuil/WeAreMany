import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'settings_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  static const routeName = '/profile';

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  static const _displayNameKey = 'display_name';

  final TextEditingController _nameController = TextEditingController();
  String _displayName = '';
  bool _isEditing = false;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadDisplayName();
  }

  Future<void> _loadDisplayName() async {
    final prefs = await SharedPreferences.getInstance();
    final stored = prefs.getString(_displayNameKey) ?? '';
    if (!mounted) {
      return;
    }
    setState(() {
      _displayName = stored;
      _nameController.text = stored;
      _loading = false;
    });
  }

  Future<void> _saveDisplayName() async {
    final prefs = await SharedPreferences.getInstance();
    final nextName = _nameController.text.trim();
    await prefs.setString(_displayNameKey, nextName);
    if (!mounted) {
      return;
    }
    setState(() {
      _displayName = nextName;
      _isEditing = false;
    });
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: const Key('profile_screen'),
      appBar: AppBar(title: const Text('Profile')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Identity (private)',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 12),
          if (_loading)
            const Center(child: CircularProgressIndicator())
          else ...[
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Display Name:'),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _displayName.isEmpty ? 'Not set' : _displayName,
                    key: const Key('profile_display_name'),
                  ),
                ),
                TextButton(
                  onPressed: () => setState(() => _isEditing = !_isEditing),
                  child: Text(_isEditing ? 'Cancel' : 'Edit'),
                ),
              ],
            ),
          if (_isEditing) ...[
            TextField(
              controller: _nameController,
              decoration: const InputDecoration(
                labelText: 'Display name',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerLeft,
              child: ElevatedButton(
                onPressed: _saveDisplayName,
                child: const Text('Save'),
              ),
            ),
          ],
          ],
          const SizedBox(height: 16),
          ListTile(
            key: const Key('profile_settings'),
            leading: const Icon(Icons.settings_outlined),
            title: const Text('Settings'),
            subtitle: const Text('Privacy, notifications, About & Safety'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () =>
                Navigator.of(context).pushNamed(SettingsScreen.routeName),
          ),
          const SizedBox(height: 16),
          const Text(
            'Profile summary',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          const Text(
            'A private space to keep your identity and preferences organized.',
          ),
          const SizedBox(height: 16),
          const Text(
            'This profile is private and not visible to others.',
            style: TextStyle(color: Colors.black54),
          ),
        ],
      ),
    );
  }
}
