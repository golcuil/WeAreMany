import 'package:flutter/material.dart';

class CrisisScreen extends StatelessWidget {
  const CrisisScreen({super.key});

  static const routeName = '/crisis';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Crisis Support')),
      body: const Padding(
        padding: EdgeInsets.all(24),
        child: Text(
          'You may be in a tough moment. You are not alone.\n'
          'Please consider reaching out to local crisis resources.',
        ),
      ),
    );
  }
}
