import 'package:flutter/material.dart';

import '../features/home/home_screen.dart';
import '../features/inbox/inbox_screen.dart';
import '../features/profile/profile_screen.dart';
import '../features/reflection/reflection_screen.dart';

class MainTabs extends StatefulWidget {
  const MainTabs({super.key});

  @override
  State<MainTabs> createState() => _MainTabsState();
}

class _MainTabsState extends State<MainTabs> {
  int _index = 0;

  final List<Widget> _screens = const [
    HomeScreen(),
    InboxScreen(),
    ReflectionScreen(),
    ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _index, children: _screens),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _index,
        onTap: (value) => setState(() => _index = value),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined, key: Key('tab_home')),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.mail_outline, key: Key('tab_messages')),
            label: 'Messages',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.insights_outlined, key: Key('tab_reflection')),
            label: 'Reflection',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person_outline, key: Key('tab_profile')),
            label: 'Profile',
          ),
        ],
      ),
    );
  }
}
