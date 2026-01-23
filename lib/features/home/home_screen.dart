import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../content/helpful_series_v1.dart';
import '../inbox/inbox_screen.dart';
import '../mood/mood_entry_screen.dart';
import '../reflection/reflection_screen.dart';
import '../profile/profile_providers.dart';
import 'helpful_detail_screen.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  static const routeName = '/';

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final historyAsync = ref.watch(moodHistoryEntriesProvider);
    return Scaffold(
      key: const Key('home_screen'),
      appBar: AppBar(title: const Text('We Are Many')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('How do you feel right now?'),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () =>
                Navigator.of(context).pushNamed(MoodEntryScreen.routeName),
            child: const Text('Share a mood'),
          ),
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: () =>
                Navigator.of(context).pushNamed(InboxScreen.routeName),
            child: const Text('Inbox'),
          ),
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: () =>
                Navigator.of(context).pushNamed(ReflectionScreen.routeName),
            child: const Text('Reflection'),
          ),
          const SizedBox(height: 24),
          historyAsync.when(
            data: (entries) {
              final card = pickHelpfulCard(entries);
              if (card == null) {
                return const SizedBox.shrink();
              }
              return Card(
                key: const Key('helpful_card'),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        card.title,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(card.bullets.first),
                      if (card.bullets.length > 1) Text(card.bullets[1]),
                      const SizedBox(height: 8),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: TextButton(
                          onPressed: () {
                            Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => HelpfulDetailScreen(card: card),
                              ),
                            );
                          },
                          child: const Text('Open'),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
            loading: () => const SizedBox.shrink(),
            error: (error, stackTrace) => const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }
}
