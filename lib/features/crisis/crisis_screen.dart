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
              'You may be in a tough moment. You are not alone.\n'
              'Please consider reaching out to local crisis resources.',
            ),
            const SizedBox(height: 24),
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
