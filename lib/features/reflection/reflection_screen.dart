import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'reflection_controller.dart';

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

    return Scaffold(
      key: const Key('reflection_screen'),
      appBar: AppBar(title: const Text('Reflection')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
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
          ],
        ),
      ),
    );
  }
}
