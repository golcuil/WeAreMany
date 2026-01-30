import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:we_are_many/core/network/api_client.dart';
import 'package:we_are_many/features/home/home_screen.dart';
import 'package:we_are_many/features/pulse/pulse_controller.dart';
import 'package:we_are_many/features/pulse/widgets/collective_pulse_background.dart';

class FakePulseController extends PulseController {
  FakePulseController(PulseState state)
    : super(
        apiClient: _NoopApiClient(),
        autoStart: false,
      ) {
    this.state = state;
  }
}

class _NoopApiClient implements ApiClient {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  testWidgets('Pulse background falls back to misty blue', (tester) async {
    final controller = FakePulseController(const PulseState(distribution: {}));
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          pulseControllerProvider.overrideWith((ref) => controller),
        ],
        child: const MaterialApp(home: HomeScreen()),
      ),
    );

    await tester.pump();
    final container = tester.widget<AnimatedContainer>(
      find.descendant(
        of: find.byType(CollectivePulseBackground),
        matching: find.byType(AnimatedContainer),
      ).first,
    );
    final decoration = container.decoration as BoxDecoration;
    final gradient = decoration.gradient as LinearGradient;
    expect(
      gradient.colors,
      equals(
        const [
          Color(0xFFAEC6CF),
          Color(0xFFAEC6CF),
        ],
      ),
    );
  });

  testWidgets('Pulse background uses weighted colors', (tester) async {
    final controller = FakePulseController(
      const PulseState(
        distribution: {
          'calm': 60,
          'hopeful': 30,
          'sad': 10,
        },
      ),
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          pulseControllerProvider.overrideWith((ref) => controller),
        ],
        child: const MaterialApp(home: HomeScreen()),
      ),
    );

    await tester.pump();
    final container = tester.widget<AnimatedContainer>(
      find.descendant(
        of: find.byType(CollectivePulseBackground),
        matching: find.byType(AnimatedContainer),
      ).first,
    );
    final decoration = container.decoration as BoxDecoration;
    final gradient = decoration.gradient as LinearGradient;
    expect(
      gradient.colors,
      equals(
        const [
          Color(0xFFAEC6CF),
          Color(0xFFF4D35E),
          Color(0xFFA7B3C2),
        ],
      ),
    );
  });
}
