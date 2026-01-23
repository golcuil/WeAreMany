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
  static const int inboxLockDays = 7;

  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(inboxControllerProvider.notifier).load());
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(inboxControllerProvider);
    return Scaffold(
      key: const Key('inbox_screen'),
      appBar: AppBar(
        title: const Text('Inbox'),
        actions: [
          IconButton(
            onPressed: () =>
                ref.read(inboxControllerProvider.notifier).refresh(),
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
              child: Text(
                state.error!,
                style: const TextStyle(color: Colors.red),
              ),
            ),
          Expanded(
            child: ListView.separated(
              itemCount: state.items.length,
              separatorBuilder: (context, index) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final item = state.items[index];
                final isResponded = item.ackStatus != null;
                final isLocked = _isLocked(item.receivedAt);
                final isRead =
                    isResponded || state.readIds.contains(item.inboxItemId);
                final status = isLocked
                    ? 'Locked'
                    : isResponded
                    ? 'Responded'
                    : null;
                final timestamp = _formatTimestamp(item.receivedAt);
                final subtitle = status == null
                    ? timestamp
                    : '$timestamp \u00b7 $status';
                return ListTile(
                  onTap: () => ref
                      .read(inboxControllerProvider.notifier)
                      .markRead(item.inboxItemId),
                  leading: isRead
                      ? const SizedBox(width: 8)
                      : Container(
                          key: Key('inbox_unread_dot_${item.inboxItemId}'),
                          width: 8,
                          height: 8,
                          decoration: const BoxDecoration(
                            shape: BoxShape.circle,
                            color: Colors.blueAccent,
                          ),
                        ),
                  title: Text(item.text),
                  subtitle: Text(subtitle),
                  trailing: Wrap(
                    spacing: 8,
                    children: [
                      _AckButton(
                        label: 'Thanks',
                        enabled: !isResponded && !isLocked,
                        onPressed: () => ref
                            .read(inboxControllerProvider.notifier)
                            .acknowledge(
                              inboxItemId: item.inboxItemId,
                              reaction: 'thanks',
                            ),
                      ),
                      _AckButton(
                        label: 'I relate',
                        enabled: !isResponded && !isLocked,
                        onPressed: () => ref
                            .read(inboxControllerProvider.notifier)
                            .acknowledge(
                              inboxItemId: item.inboxItemId,
                              reaction: 'relate',
                            ),
                      ),
                      _AckButton(
                        label: 'Helpful',
                        enabled: !isResponded && !isLocked,
                        onPressed: () => ref
                            .read(inboxControllerProvider.notifier)
                            .acknowledge(
                              inboxItemId: item.inboxItemId,
                              reaction: 'helpful',
                            ),
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

  String _formatTimestamp(String value) {
    if (value.isEmpty) {
      return 'Recently';
    }
    final parsed = DateTime.tryParse(value);
    if (parsed == null) {
      return value;
    }
    final day = DateTime.utc(parsed.year, parsed.month, parsed.day);
    final now = DateTime.now().toUtc();
    final today = DateTime.utc(now.year, now.month, now.day);
    final diffDays = today.difference(day).inDays;
    if (diffDays == 0) {
      return 'Today';
    }
    if (diffDays == 1) {
      return 'Yesterday';
    }
    return day.toIso8601String().split('T').first;
  }

  bool _isLocked(String value) {
    final parsed = DateTime.tryParse(value);
    if (parsed == null) {
      return false;
    }
    final day = DateTime.utc(parsed.year, parsed.month, parsed.day);
    final now = DateTime.now().toUtc();
    final today = DateTime.utc(now.year, now.month, now.day);
    final diffDays = today.difference(day).inDays;
    return diffDays >= inboxLockDays;
  }
}

class _AckButton extends StatelessWidget {
  const _AckButton({
    required this.label,
    required this.enabled,
    required this.onPressed,
  });

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
