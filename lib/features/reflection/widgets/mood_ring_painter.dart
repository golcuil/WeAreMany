import 'dart:math';

import 'package:flutter/material.dart';

class MoodRingPainter extends CustomPainter {
  MoodRingPainter({
    required this.distribution,
    required this.colors,
    this.progress = 1,
    this.strokeWidth = 16,
  });

  final Map<String, int> distribution;
  final List<Color> colors;
  final double progress;
  final double strokeWidth;

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final radius = min(size.width, size.height) / 2 - strokeWidth / 2;
    if (radius <= 0) {
      return;
    }

    final total = distribution.values.fold<int>(0, (sum, value) {
      return sum + value;
    });

    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    if (total <= 0 || progress <= 0) {
      paint.color = const Color(0x1F000000);
      canvas.drawCircle(center, radius, paint);
      return;
    }

    var startAngle = -pi / 2;
    final entries = distribution.entries.toList(growable: false);
    for (var i = 0; i < entries.length; i++) {
      final value = entries[i].value;
      if (value <= 0) {
        continue;
      }
      final sweep = (value / total) * 2 * pi * progress;
      paint.color = colors[i % colors.length];
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        sweep,
        false,
        paint,
      );
      startAngle += sweep;
    }
  }

  @override
  bool shouldRepaint(covariant MoodRingPainter oldDelegate) {
    return oldDelegate.strokeWidth != strokeWidth ||
        oldDelegate.progress != progress ||
        oldDelegate.distribution != distribution ||
        oldDelegate.colors != colors;
  }
}
