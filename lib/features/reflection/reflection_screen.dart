import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_colors.dart';
import 'reflection_controller.dart';
import 'widgets/impact_card.dart';
import 'widgets/mood_ring_painter.dart';

class ReflectionScreen extends ConsumerStatefulWidget {
  const ReflectionScreen({super.key});

  static const routeName = '/reflection';

  @override
  ConsumerState<ReflectionScreen> createState() => _ReflectionScreenState();
}

class _ReflectionScreenState extends ConsumerState<ReflectionScreen> {
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
    final isEmpty = summary == null || summary.totalEntries == 0;

    return Scaffold(
      key: const Key('reflection_screen'),
      appBar: AppBar(title: const Text('Reflection')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (state.isLoading) const LinearProgressIndicator(),
          if (state.error != null) ...[
            const SizedBox(height: 12),
            Text(state.error!, style: const TextStyle(color: Colors.red)),
          ],
          if (!state.isLoading && state.error == null && isEmpty)
            const _EmptyReflectionState(),
          if (!state.isLoading && state.error == null && !isEmpty) ...[
            const SizedBox(height: 12),
            Text(
              'Your week in feelings',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 6),
            Text(
              _trendLabel(summary.trend),
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(
                  context,
                ).colorScheme.onSurface.withValues(alpha: 0.7),
              ),
            ),
            const SizedBox(height: 20),
            Center(
              child: SizedBox(
                height: 180,
                width: 180,
                child: TweenAnimationBuilder<double>(
                  tween: Tween<double>(begin: 0, end: 1),
                  duration: const Duration(seconds: 1),
                  builder: (context, value, child) {
                    return CustomPaint(
                      key: const Key('mood_ring'),
                      painter: MoodRingPainter(
                        distribution: summary.distribution,
                        colors: const [
                          AppColors.reflectionSage,
                          AppColors.reflectionAmber,
                          AppColors.reflectionDustyRose,
                          AppColors.reflectionMistyBlue,
                        ],
                        progress: value,
                      ),
                    );
                  },
                ),
              ),
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: ImpactCard(
                    title: 'Entries',
                    value: summary.totalEntries.toString(),
                    icon: Icons.auto_graph_outlined,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ImpactCard(
                    title: 'Volatility days',
                    value: summary.volatilityDays.toString(),
                    icon: Icons.water_drop_outlined,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

String _trendLabel(String rawTrend) {
  switch (rawTrend.toLowerCase()) {
    case 'up':
      return 'Feeling lighter overall';
    case 'down':
      return 'Carrying more weight lately';
    case 'mixed':
      return 'A mix of highs and lows';
    default:
      return 'Holding steady';
  }
}

class _EmptyReflectionState extends StatelessWidget {
  const _EmptyReflectionState();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 12),
        Text(
          'Start your journey',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Check in with how you feel. Your reflection stays private and '
          'builds a gentle weekly summary.',
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
          ),
        ),
        const SizedBox(height: 16),
        ElevatedButton(
          onPressed: () => Navigator.of(context).pushNamed('/mood'),
          child: const Text('Share how you feel'),
        ),
      ],
    );
  }
}
