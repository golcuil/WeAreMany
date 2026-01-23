import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:we_are_many/core/local/mood_history_store.dart';
import 'package:we_are_many/features/home/home_screen.dart';
import 'package:we_are_many/features/profile/profile_providers.dart';

void main() {
  testWidgets('Home shows Faydalı Serisi card and opens detail', (
    tester,
  ) async {
    final entries = [
      MoodHistoryEntry(
        dateKey: '2026-01-20',
        emotionLabel: 'sad',
        valence: 'negative',
        intensity: 'low',
      ),
    ];

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          moodHistoryEntriesProvider.overrideWithValue(
            AsyncValue.data(entries),
          ),
        ],
        child: const MaterialApp(home: HomeScreen()),
      ),
    );
    await tester.pump();

    expect(find.byKey(const Key('faydali_card')), findsOneWidget);
    await tester.tap(find.text('Open'));
    await tester.pumpAndSettle();

    expect(find.textContaining('Faydalı Serisi'), findsWidgets);
  });
}
