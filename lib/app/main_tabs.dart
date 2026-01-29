import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/theme/app_colors.dart';
import '../features/home/home_screen.dart';
import '../features/inbox/inbox_controller.dart';
import '../features/inbox/inbox_screen.dart';
import '../features/profile/profile_screen.dart';
import '../features/reflection/reflection_screen.dart';

class MainTabs extends ConsumerStatefulWidget {
  const MainTabs({super.key});

  @override
  ConsumerState<MainTabs> createState() => _MainTabsState();
}

class _MainTabsState extends ConsumerState<MainTabs>
    with SingleTickerProviderStateMixin {
  int _index = 0;
  late final AnimationController _glowController;
  late final Animation<double> _glowAnimation;

  final List<Widget> _screens = const [
    HomeScreen(),
    InboxScreen(),
    ReflectionScreen(),
    ProfileScreen(),
  ];

  @override
  void initState() {
    super.initState();
    _glowController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2400),
    );
    _glowAnimation = CurvedAnimation(
      parent: _glowController,
      curve: Curves.easeInOut,
    );
  }

  @override
  void dispose() {
    _glowController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final inboxState = ref.watch(inboxControllerProvider);
    final hasUnread = inboxState.items.any((item) {
      if (item.itemType == 'second_touch_offer') {
        return false;
      }
      if (item.ackStatus != null) {
        return false;
      }
      return !inboxState.readIds.contains(item.inboxItemId);
    });
    if (hasUnread && !_glowController.isAnimating) {
      _glowController.repeat(reverse: true);
    } else if (!hasUnread && _glowController.isAnimating) {
      _glowController.stop();
      _glowController.value = 0.0;
    }
    return Scaffold(
      body: IndexedStack(index: _index, children: _screens),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _index,
        onTap: (value) => setState(() => _index = value),
        items: [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined, key: Key('tab_home')),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: _GlowIcon(
              active: hasUnread,
              animation: _glowAnimation,
              child: const Icon(Icons.mail_outline, key: Key('tab_messages')),
            ),
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

class _GlowIcon extends StatelessWidget {
  const _GlowIcon({
    required this.active,
    required this.animation,
    required this.child,
  });

  final bool active;
  final Animation<double> animation;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    if (!active) {
      return child;
    }
    return AnimatedBuilder(
      animation: animation,
      child: child,
      builder: (context, icon) {
        final opacity = 0.2 + (0.5 * animation.value);
        return Container(
          key: const Key('ghost_glow'),
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: AppColors.ghostSignal.withValues(alpha: opacity),
                blurRadius: 12,
                spreadRadius: 4,
              ),
            ],
          ),
          child: icon,
        );
      },
    );
  }
}
