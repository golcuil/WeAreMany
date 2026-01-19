import 'package:flutter/material.dart';

import '../features/crisis/crisis_screen.dart';
import '../features/home/home_screen.dart';
import '../features/mood/mood_entry_screen.dart';

class WeAreManyApp extends StatelessWidget {
  const WeAreManyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'We Are Many',
      theme: ThemeData(colorSchemeSeed: Colors.teal),
      routes: {
        HomeScreen.routeName: (_) => const HomeScreen(),
        MoodEntryScreen.routeName: (_) => const MoodEntryScreen(),
        CrisisScreen.routeName: (_) => const CrisisScreen(),
      },
      initialRoute: HomeScreen.routeName,
    );
  }
}
