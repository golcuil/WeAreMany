import 'package:flutter/material.dart';

import '../home/home_screen.dart';

class CrisisScreen extends StatelessWidget {
  const CrisisScreen({super.key});

  static const routeName = '/crisis';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Crisis Support')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'If you are in immediate danger, contact local emergency services.\n'
              'Consider reaching out to someone you trust.\n'
              'You can also look for local help resources near you.',
            ),
            const SizedBox(height: 24),
            TextButton(
              onPressed: () {},
              child: const Text('Find local help'),
            ),
            const SizedBox(height: 8),
            ElevatedButton(
              onPressed: () {
                Navigator.of(context).pushNamedAndRemoveUntil(
                  HomeScreen.routeName,
                  (route) => false,
                );
              },
              child: const Text('Back to Home'),
            ),
          ],
        ),
      ),
    );
  }
}
