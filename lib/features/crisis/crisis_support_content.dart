import 'package:flutter/material.dart';

class CrisisSupportContent extends StatelessWidget {
  const CrisisSupportContent({super.key});

  @override
  Widget build(BuildContext context) {
    return const Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'You may be going through a hard moment. You are not alone.',
        ),
        SizedBox(height: 16),
        Text(
          'If you are in immediate danger, contact local emergency services.',
        ),
        SizedBox(height: 8),
        Text('Consider reaching out to someone you trust.'),
        SizedBox(height: 8),
        Text('Look for local help resources near you.'),
      ],
    );
  }
}
