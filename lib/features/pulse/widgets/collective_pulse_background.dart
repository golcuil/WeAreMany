import 'package:flutter/material.dart';

class CollectivePulseBackground extends StatelessWidget {
  const CollectivePulseBackground({
    super.key,
    required this.distribution,
    required this.child,
  });

  final Map<String, int> distribution;
  final Widget child;

  static const Color _mistyBlue = Color(0xFFAEC6CF);
  static const Color _softGold = Color(0xFFF4D35E);
  static const Color _warmAmber = Color(0xFFF0B429);
  static const Color _indigo = Color(0xFF7C83A6);
  static const Color _dustyBlue = Color(0xFFA7B3C2);
  static const Color _sage = Color(0xFFB2C9AB);

  @override
  Widget build(BuildContext context) {
    final gradient = _buildGradient(distribution);
    return AnimatedContainer(
      duration: const Duration(seconds: 8),
      curve: Curves.easeInOut,
      decoration: BoxDecoration(gradient: gradient),
      child: Container(
        color: Colors.black.withValues(alpha: 0.02),
        child: child,
      ),
    );
  }

  LinearGradient _buildGradient(Map<String, int> distribution) {
    if (distribution.isEmpty) {
      return const LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [_mistyBlue, _mistyBlue],
      );
    }

    final entries = distribution.entries
        .where((entry) => entry.value > 0)
        .toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    if (entries.isEmpty) {
      return const LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [_mistyBlue, _mistyBlue],
      );
    }

    final top = entries.take(3).toList();
    final total = top.fold<int>(0, (sum, entry) => sum + entry.value);
    if (total <= 0) {
      return const LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [_mistyBlue, _mistyBlue],
      );
    }

    final colors = top.map((entry) => _colorForEmotion(entry.key)).toList();
    final stops = <double>[];
    var cumulative = 0.0;
    for (final entry in top) {
      cumulative += entry.value / total;
      stops.add(cumulative.clamp(0.0, 1.0));
    }
    if (colors.length == 1) {
      colors.add(colors.first);
      stops
        ..clear()
        ..addAll([1.0, 1.0]);
    } else if (colors.length == 2) {
      colors.add(colors.last);
      stops.add(1.0);
    }

    return LinearGradient(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
      colors: colors,
      stops: stops,
    );
  }

  Color _colorForEmotion(String emotion) {
    switch (emotion.toLowerCase()) {
      case 'calm':
        return _mistyBlue;
      case 'hopeful':
      case 'content':
        return _softGold;
      case 'happy':
        return _warmAmber;
      case 'anxious':
      case 'overwhelmed':
        return _indigo;
      case 'sad':
        return _dustyBlue;
      default:
        return _sage;
    }
  }
}
