import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/local/journal_store.dart';
import '../../core/local/mood_history_store.dart';
import 'journal_entry_screen.dart';
import 'journal_providers.dart';
import 'reflection_controller.dart';

class ReflectionScreen extends ConsumerStatefulWidget {
  const ReflectionScreen({super.key});

  static const routeName = '/reflection';

  @override
  ConsumerState<ReflectionScreen> createState() => _ReflectionScreenState();
}

class _ReflectionScreenState extends ConsumerState<ReflectionScreen> {
  int _journalDays = 7;

  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      ref.read(reflectionControllerProvider.notifier).load();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(reflectionControllerProvider);
    final summary = state.summary;
    final journalEntriesAsync = ref.watch(journalEntriesProvider);
    final moodHistoryAsync = ref.watch(moodHistoryEntriesProvider);
    final todayKey = _dateKey(DateTime.now().toUtc());

    return Scaffold(
      key: const Key('reflection_screen'),
      appBar: AppBar(title: const Text('Reflection')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Last 7 days'),
          const SizedBox(height: 12),
          if (state.isLoading) const LinearProgressIndicator(),
          if (state.error != null) ...[
            const SizedBox(height: 12),
            Text(state.error!, style: const TextStyle(color: Colors.red)),
          ],
          if (summary != null) ...[
            const SizedBox(height: 12),
            Text('Entries: ${summary.totalEntries}'),
            Text('Trend: ${summary.trend}'),
            Text('Volatility days: ${summary.volatilityDays}'),
            const SizedBox(height: 12),
            const Text('Distribution'),
            const SizedBox(height: 8),
            for (final entry in summary.distribution.entries)
              Text('${entry.key}: ${entry.value}'),
          ],
          const SizedBox(height: 20),
          const Text(
            'Journal',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          moodHistoryAsync.when(
            data: (entries) {
              final moodToday = _emotionForDate(entries, todayKey);
              final prompts = _promptsForEmotion(moodToday);
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Today’s prompts'),
                  const SizedBox(height: 6),
                  for (final prompt in prompts) Text('• $prompt'),
                ],
              );
            },
            loading: () => const SizedBox.shrink(),
            error: (error, stackTrace) => const SizedBox.shrink(),
          ),
          const SizedBox(height: 12),
          journalEntriesAsync.when(
            data: (entries) {
              final todayEntry = entries.firstWhere(
                (entry) => entry.dateKey == todayKey,
                orElse: () => JournalEntry(dateKey: '', text: ''),
              );
              final hasTodayEntry = todayEntry.dateKey == todayKey;
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ElevatedButton(
                    onPressed: () {
                      Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => JournalEntryScreen(
                            entry: hasTodayEntry ? todayEntry : null,
                            todayEmotionLabel: moodHistoryAsync.maybeWhen(
                              data: (entries) =>
                                  _emotionForDate(entries, todayKey),
                              orElse: () => null,
                            ),
                          ),
                        ),
                      );
                    },
                    child: Text(
                      hasTodayEntry ? "Edit today's note" : "Write today's note",
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      ChoiceChip(
                        label: const Text('7 days'),
                        selected: _journalDays == 7,
                        onSelected: (_) => setState(() => _journalDays = 7),
                      ),
                      const SizedBox(width: 8),
                      ChoiceChip(
                        label: const Text('30 days'),
                        selected: _journalDays == 30,
                        onSelected: (_) => setState(() => _journalDays = 30),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  ..._buildJournalList(
                    context,
                    _filterEntries(entries, _journalDays),
                    todayKey,
                  ),
                ],
              );
            },
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, stackTrace) =>
                const Text('Unable to load journal entries.'),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildJournalList(
    BuildContext context,
    List<JournalEntry> entries,
    String todayKey,
  ) {
    if (entries.isEmpty) {
      return [const Text('No journal entries yet.')];
    }
    return entries.map((entry) {
      final preview = entry.text.length > 80
          ? '${entry.text.substring(0, 80)}…'
          : entry.text;
      final isToday = entry.dateKey == todayKey;
      return ListTile(
        title: Text(entry.dateKey),
        subtitle: Text(preview),
        trailing: Text(isToday ? 'Today' : 'Locked'),
        onTap: () {
          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => JournalEntryScreen(entry: entry),
            ),
          );
        },
      );
    }).toList();
  }

  List<JournalEntry> _filterEntries(List<JournalEntry> entries, int days) {
    final now = DateTime.now().toUtc();
    final start = DateTime.utc(now.year, now.month, now.day)
        .subtract(Duration(days: days - 1));
    final filtered = entries.where((entry) {
      final parsed = DateTime.tryParse(entry.dateKey);
      if (parsed == null) {
        return false;
      }
      return !parsed.isBefore(start) && !parsed.isAfter(now);
    }).toList();
    filtered.sort((a, b) => b.dateKey.compareTo(a.dateKey));
    return filtered;
  }

  String _dateKey(DateTime value) {
    final utc = value.toUtc();
    return '${utc.year.toString().padLeft(4, '0')}-'
        '${utc.month.toString().padLeft(2, '0')}-'
        '${utc.day.toString().padLeft(2, '0')}';
  }

  String? _emotionForDate(List<MoodHistoryEntry> entries, String dateKey) {
    for (final entry in entries) {
      if (entry.dateKey == dateKey) {
        return entry.emotionLabel;
      }
    }
    return null;
  }

  List<String> _promptsForEmotion(String? emotionLabel) {
    switch (emotionLabel) {
      case 'calm':
        return [
          'What helped you feel steady today?',
          'Which moment felt most peaceful?',
        ];
      case 'anxious':
        return [
          'What felt hardest today?',
          'What small support could help tomorrow?',
        ];
      case 'sad':
        return [
          'What do you wish others understood today?',
          'What gave you a little relief?',
        ];
      default:
        return [
          'What stood out most today?',
          'What is one thing you want to remember?',
          'What would you like to carry into tomorrow?',
        ];
    }
  }
}
