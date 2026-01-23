import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:we_are_many/core/local/journal_store.dart';

void main() {
  test('Save today entry succeeds and loads', () async {
    SharedPreferences.setMockInitialValues({});
    final ok = await JournalStore.saveTodayEntry(
      'Hello',
      emotionLabel: 'calm',
      now: DateTime.utc(2026, 1, 20, 10),
    );
    expect(ok, isTrue);
    final entries = await JournalStore.loadEntries();
    expect(entries.length, 1);
    expect(entries.first.dateKey, '2026-01-20');
    expect(entries.first.emotionLabel, 'calm');
  });

  test('Save entry rejects non-today date key', () async {
    SharedPreferences.setMockInitialValues({});
    final ok = await JournalStore.saveTodayEntry(
      'Old',
      now: DateTime.utc(2026, 1, 20),
      dateKeyOverride: '2026-01-19',
    );
    expect(ok, isFalse);
    final entries = await JournalStore.loadEntries();
    expect(entries, isEmpty);
  });

  test('Delete entry removes it', () async {
    SharedPreferences.setMockInitialValues({});
    await JournalStore.saveTodayEntry('Hello', now: DateTime.utc(2026, 1, 20));
    await JournalStore.deleteEntry('2026-01-20');
    final entries = await JournalStore.loadEntries();
    expect(entries, isEmpty);
  });

  test('Store keeps only the newest entries', () async {
    SharedPreferences.setMockInitialValues({});
    final now = DateTime.utc(2026, 1, 1);
    for (var i = 0; i < JournalStore.maxEntries + 5; i += 1) {
      await JournalStore.saveTodayEntry(
        'Note $i',
        now: now.add(Duration(days: i)),
      );
    }
    final entries = await JournalStore.loadEntries();
    expect(entries.length, JournalStore.maxEntries);
  });
}
