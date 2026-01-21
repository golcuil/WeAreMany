import 'package:flutter/material.dart';

import '../inbox/inbox_screen.dart';
import '../mood/mood_entry_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  static const routeName = '/';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('We Are Many')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
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
          ],
        ),
      ),
    );
  }
}
