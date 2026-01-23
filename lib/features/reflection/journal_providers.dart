import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/local/journal_store.dart';
import '../../core/local/mood_history_store.dart';

final journalRefreshProvider = StateProvider<int>((ref) => 0);

final journalEntriesProvider = FutureProvider<List<JournalEntry>>((ref) async {
  ref.watch(journalRefreshProvider);
  return JournalStore.loadEntries();
});

final moodHistoryEntriesProvider = FutureProvider<List<MoodHistoryEntry>>((
  ref,
) async {
  return MoodHistoryStore.loadEntries();
});
