import 'package:flutter/material.dart';

import '../crisis/crisis_screen.dart';

class AboutSafetyScreen extends StatelessWidget {
  const AboutSafetyScreen({super.key});

  static const routeName = '/about-safety';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('About & Safety')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'What this app is',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text('A private space to reflect on your mood patterns.'),
          const SizedBox(height: 16),
          const Text(
            'What this app is not',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text('Not therapy and not a social network.'),
          const SizedBox(height: 16),
          const Text(
            'Anonymity basics',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text('No public sharing and no sender identity is shown.'),
          const SizedBox(height: 16),
          const Text(
            'Safety',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text(
            'If you are in immediate danger, contact local emergency services.',
          ),
          const SizedBox(height: 8),
          const Text('Consider reaching out to someone you trust.'),
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: () =>
                Navigator.of(context).pushNamed(CrisisScreen.routeName),
            child: const Text('View crisis resources'),
          ),
          const SizedBox(height: 16),
          const Text(
            'Data handling',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text(
            'We store only the minimum needed to provide private reflections.',
          ),
        ],
      ),
    );
  }
}
