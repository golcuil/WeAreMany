import 'package:flutter/material.dart';

import '../features/crisis/crisis_screen.dart';
import '../features/home/home_screen.dart';
import '../features/inbox/inbox_screen.dart';
import '../features/mood/mood_entry_screen.dart';
import '../features/reflection/reflection_screen.dart';
import '../features/profile/about_safety_screen.dart';
import '../features/profile/profile_screen.dart';
import 'main_tabs.dart';

class WeAreManyApp extends StatelessWidget {
  const WeAreManyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'We Are Many',
      theme: ThemeData(colorSchemeSeed: Colors.teal),
      routes: {
        HomeScreen.routeName: (_) => const MainTabs(),
        MoodEntryScreen.routeName: (_) => const MoodEntryScreen(),
        CrisisScreen.routeName: (_) => const CrisisScreen(),
        InboxScreen.routeName: (_) => const InboxScreen(),
        ReflectionScreen.routeName: (_) => const ReflectionScreen(),
        ProfileScreen.routeName: (_) => const ProfileScreen(),
        AboutSafetyScreen.routeName: (_) => const AboutSafetyScreen(),
      },
      initialRoute: HomeScreen.routeName,
    );
  }
}
