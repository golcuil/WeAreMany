import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/local/mood_history_store.dart';
import '../../core/local/profile_store.dart';
import 'about_safety_screen.dart';
import 'profile_providers.dart';

class PrivacyScreen extends ConsumerWidget {
  const PrivacyScreen({super.key});

  static const routeName = '/privacy';

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      key: const Key('privacy_screen'),
      appBar: AppBar(title: const Text('Privacy')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'What We Store (Today)',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          const Text(
            'On this device: day-level mood history (last ~60 entries) and your display name.',
          ),
          const SizedBox(height: 6),
          const Text(
            'On the server: sanitized messages for delivery, one-shot acknowledgements, and an aggregate impact count.',
          ),
          const SizedBox(height: 16),
          const Text(
            'What We Never Show',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          const Text(
            'No sender identity, no public profiles, no threads, and no lists of who acknowledged your messages.',
          ),
          const SizedBox(height: 16),
          const Text(
            'Safety',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          const Text(
            'If a crisis signal is detected, peer messaging is blocked and crisis resources are shown.',
          ),
          const SizedBox(height: 16),
          const Text(
            'Your Controls',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          ElevatedButton(
            key: const Key('privacy_clear_mood_history'),
            onPressed: () async {
              await MoodHistoryStore.clearHistory();
              ref.read(moodHistoryRefreshProvider.notifier).state++;
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Local mood history cleared.')),
                );
              }
            },
            child: const Text('Clear local mood history'),
          ),
          const SizedBox(height: 8),
          ElevatedButton(
            key: const Key('privacy_reset_display_name'),
            onPressed: () async {
              await ProfileStore.clearDisplayName();
              ref.read(displayNameRefreshProvider.notifier).state++;
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Display name reset.')),
                );
              }
            },
            child: const Text('Reset private display name'),
          ),
          const SizedBox(height: 8),
          TextButton(
            key: const Key('privacy_about_safety'),
            onPressed: () =>
                Navigator.of(context).pushNamed(AboutSafetyScreen.routeName),
            child: const Text('Open About & Safety'),
          ),
        ],
      ),
    );
  }
}
