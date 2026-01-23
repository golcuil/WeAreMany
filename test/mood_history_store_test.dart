import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:we_are_many/core/local/mood_history_store.dart';

void main() {
  test('Filters entries by day range and counts frequency', () {
    final entries = [
      MoodHistoryEntry(
        dateKey: '2026-01-10',
        emotionLabel: 'calm',
        valence: 'positive',
        intensity: 'low',
      ),
      MoodHistoryEntry(
        dateKey: '2026-01-09',
        emotionLabel: 'sad',
        valence: 'negative',
        intensity: 'medium',
      ),
      MoodHistoryEntry(
        dateKey: '2026-01-01',
        emotionLabel: 'anxious',
        valence: 'negative',
        intensity: 'high',
      ),
    ];

    final snapshot = MoodHistoryStore.computeSnapshot(
      entries,
      7,
      now: DateTime.utc(2026, 1, 10),
    );

    expect(snapshot.frequency, 2);
    expect(snapshot.countsByEmotion['calm'], 1);
    expect(snapshot.countsByEmotion['sad'], 1);
  });

  test('Volatility counts emotion changes day to day', () {
    final entries = [
      MoodHistoryEntry(
        dateKey: '2026-01-10',
        emotionLabel: 'calm',
        valence: 'positive',
        intensity: 'low',
      ),
      MoodHistoryEntry(
        dateKey: '2026-01-09',
        emotionLabel: 'sad',
        valence: 'negative',
        intensity: 'medium',
      ),
      MoodHistoryEntry(
        dateKey: '2026-01-08',
        emotionLabel: 'sad',
        valence: 'negative',
        intensity: 'high',
      ),
    ];

    final snapshot = MoodHistoryStore.computeSnapshot(
      entries,
      7,
      now: DateTime.utc(2026, 1, 10),
    );

    expect(snapshot.volatilityDays, 1);
    expect(snapshot.timeline.length, 3);
  });

  test('Record/load roundtrip with UTC day key', () async {
    SharedPreferences.setMockInitialValues({});
    await MoodHistoryStore.recordEntry(
      emotionLabel: 'calm',
      valence: 'positive',
      intensity: 'low',
      now: DateTime.utc(2026, 1, 15, 23, 30),
    );

    final entries = await MoodHistoryStore.loadEntries();
    expect(entries.length, 1);
    expect(entries.first.dateKey, '2026-01-15');
    expect(entries.first.emotionLabel, 'calm');
  });

  test('Stores only the most recent entries', () async {
    SharedPreferences.setMockInitialValues({});
    for (var i = 0; i < MoodHistoryStore.maxEntries + 5; i += 1) {
      await MoodHistoryStore.recordEntry(
        emotionLabel: 'calm',
        valence: 'positive',
        intensity: 'low',
        now: DateTime.utc(2026, 1, 1).add(Duration(days: i)),
      );
    }

    final entries = await MoodHistoryStore.loadEntries();
    expect(entries.length, MoodHistoryStore.maxEntries);
    expect(entries.first.dateKey, '2026-03-06');
    expect(entries.last.dateKey, '2026-01-06');
  });
}
