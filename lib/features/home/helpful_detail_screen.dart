import 'package:flutter/material.dart';

import '../../content/helpful_series_v1.dart';

class HelpfulDetailScreen extends StatelessWidget {
  const HelpfulDetailScreen({super.key, required this.card});

  final HelpfulCard card;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Helpful Series')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            card.title,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 12),
          ...card.bullets.map(
            (bullet) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('• '),
                  Expanded(child: Text(bullet)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text(card.why, style: const TextStyle(color: Colors.black54)),
        ],
      ),
    );
  }
}
