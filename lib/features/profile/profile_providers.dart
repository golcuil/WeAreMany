import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/local/mood_history_store.dart';

final displayNameRefreshProvider = StateProvider<int>((ref) => 0);

final moodHistoryRefreshProvider = StateProvider<int>((ref) => 0);

final moodHistoryEntriesProvider =
    FutureProvider<List<MoodHistoryEntry>>((ref) async {
      ref.watch(moodHistoryRefreshProvider);
      return MoodHistoryStore.loadEntries();
    });
