import 'package:flutter/material.dart';

import '../home/home_screen.dart';
import 'crisis_support_content.dart';

class CrisisScreen extends StatelessWidget {
  const CrisisScreen({super.key});

  static const routeName = '/crisis';

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      child: Scaffold(
        key: const Key('crisis_screen'),
        appBar: AppBar(
          title: const Text('Crisis Support'),
          automaticallyImplyLeading: false,
        ),
        body: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const CrisisSupportContent(),
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
      ),
    );
  }
}
