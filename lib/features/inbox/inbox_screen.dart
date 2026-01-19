import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'inbox_controller.dart';

class InboxScreen extends ConsumerStatefulWidget {
  const InboxScreen({super.key});

  static const routeName = '/inbox';

  @override
  ConsumerState<InboxScreen> createState() => _InboxScreenState();
}

class _InboxScreenState extends ConsumerState<InboxScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(inboxControllerProvider.notifier).load());
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(inboxControllerProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Inbox'),
        actions: [
          IconButton(
            onPressed: () => ref.read(inboxControllerProvider.notifier).refresh(),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: Column(
        children: [
          if (state.isLoading) const LinearProgressIndicator(),
          if (state.error != null)
            Padding(
              padding: const EdgeInsets.all(12),
              child: Text(state.error!, style: const TextStyle(color: Colors.red)),
            ),
          Expanded(
            child: ListView.separated(
              itemCount: state.items.length,
              separatorBuilder: (context, index) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final item = state.items[index];
                final isResponded = item.ackStatus != null;
                return ListTile(
                  title: Text(item.text),
                  subtitle: Text(item.receivedAt.isEmpty ? 'Recently' : item.receivedAt),
                  trailing: Wrap(
                    spacing: 8,
                    children: [
                      _AckButton(
                        label: 'Thanks',
                        enabled: !isResponded,
                        onPressed: () => ref
                            .read(inboxControllerProvider.notifier)
                            .acknowledge(inboxItemId: item.inboxItemId, reaction: 'thanks'),
                      ),
                      _AckButton(
                        label: 'I relate',
                        enabled: !isResponded,
                        onPressed: () => ref
                            .read(inboxControllerProvider.notifier)
                            .acknowledge(inboxItemId: item.inboxItemId, reaction: 'relate'),
                      ),
                      _AckButton(
                        label: 'Helpful',
                        enabled: !isResponded,
                        onPressed: () => ref
                            .read(inboxControllerProvider.notifier)
                            .acknowledge(inboxItemId: item.inboxItemId, reaction: 'helpful'),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _AckButton extends StatelessWidget {
  const _AckButton({required this.label, required this.enabled, required this.onPressed});

  final String label;
  final bool enabled;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return TextButton(
      onPressed: enabled ? onPressed : null,
      child: Text(label),
    );
  }
}
