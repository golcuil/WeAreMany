import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/local/journal_store.dart';
import 'journal_providers.dart';

class JournalEntryScreen extends ConsumerStatefulWidget {
  const JournalEntryScreen({
    super.key,
    this.entry,
    this.todayEmotionLabel,
    this.now,
  });

  final JournalEntry? entry;
  final String? todayEmotionLabel;
  final DateTime? now;

  @override
  ConsumerState<JournalEntryScreen> createState() => _JournalEntryScreenState();
}

class _JournalEntryScreenState extends ConsumerState<JournalEntryScreen> {
  final TextEditingController _controller = TextEditingController();
  late final String _dateKey;
  late final bool _isToday;

  @override
  void initState() {
    super.initState();
    final todayKey = _dateKeyFor((widget.now ?? DateTime.now()).toUtc());
    _dateKey = widget.entry?.dateKey ?? todayKey;
    _isToday = _dateKey == todayKey;
    _controller.text = widget.entry?.text ?? '';
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_isToday ? "Today's note" : 'Journal entry')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(_dateKey),
            const SizedBox(height: 12),
            if (_isToday)
              TextField(
                key: const Key('journal_text_field'),
                controller: _controller,
                maxLength: JournalStore.maxLength,
                maxLines: 6,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: 'Write a private note...',
                ),
              )
            else
              Text(
                widget.entry?.text ?? '',
                key: const Key('journal_read_only'),
              ),
            const SizedBox(height: 12),
            if (_isToday)
              ElevatedButton(
                key: const Key('journal_save'),
                onPressed: () async {
                  final ok = await JournalStore.saveTodayEntry(
                    _controller.text,
                    emotionLabel: widget.todayEmotionLabel,
                  );
                  if (ok) {
                    ref.read(journalRefreshProvider.notifier).state++;
                    if (context.mounted) {
                      Navigator.of(context).pop();
                    }
                  }
                },
                child: const Text('Save'),
              ),
            if (widget.entry != null) ...[
              const SizedBox(height: 8),
              TextButton(
                key: const Key('journal_delete'),
                onPressed: () async {
                  await JournalStore.deleteEntry(_dateKey);
                  ref.read(journalRefreshProvider.notifier).state++;
                  if (context.mounted) {
                    Navigator.of(context).pop();
                  }
                },
                child: const Text('Delete'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  String _dateKeyFor(DateTime value) {
    final utc = value.toUtc();
    return '${utc.year.toString().padLeft(4, '0')}-'
        '${utc.month.toString().padLeft(2, '0')}-'
        '${utc.day.toString().padLeft(2, '0')}';
  }
}
