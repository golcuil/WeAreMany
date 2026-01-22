import 'package:flutter/material.dart';

import 'about_safety_screen.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  static const routeName = '/settings';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: const Key('settings_screen'),
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          const ListTile(title: Text('Account'), subtitle: Text('Placeholder')),
          const Divider(height: 1),
          const ListTile(title: Text('Privacy'), subtitle: Text('Placeholder')),
          const Divider(height: 1),
          const ListTile(
            title: Text('Notifications'),
            subtitle: Text('Placeholder'),
          ),
          const Divider(height: 1),
          ListTile(
            title: const Text('About & Safety'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () =>
                Navigator.of(context).pushNamed(AboutSafetyScreen.routeName),
          ),
        ],
      ),
    );
  }
}
