import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/models.dart';
import '../../core/utils/time_utils.dart';
import 'inbox_controller.dart';

class InboxScreen extends ConsumerStatefulWidget {
  const InboxScreen({super.key, this.nowUtc});

  static const routeName = '/inbox';

  final DateTime? nowUtc;

  @override
  ConsumerState<InboxScreen> createState() => _InboxScreenState();
}

class _InboxScreenState extends ConsumerState<InboxScreen>
    with WidgetsBindingObserver {
  static const int inboxLockDays = 7;
  late final InboxController _controller;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _controller = ref.read(inboxControllerProvider.notifier);
    Future.microtask(() => _controller.startPolling());
  }

  @override
  void dispose() {
    _controller.stopPolling();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _controller.startPolling();
    } else if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.inactive) {
      _controller.stopPolling();
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(inboxControllerProvider);
    final nowUtc = (widget.nowUtc ?? DateTime.now()).toUtc();
    return Scaffold(
      key: const Key('inbox_screen'),
      appBar: AppBar(
        title: const Text('Inbox'),
        actions: [
          IconButton(
            onPressed: () => _controller.refresh(),
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
                if (item.itemType == 'second_touch_offer') {
                  return _SecondTouchOfferCard(
                    offerId: item.offerId ?? '',
                    createdAt: item.receivedAt,
                    offerState: item.offerState ?? 'available',
                    nowUtc: nowUtc,
                    onSend: (text) => _controller.sendSecondTouch(
                      offerId: item.offerId ?? '',
                      freeText: text,
                    ),
                  );
                }
                final isResponded = item.ackStatus != null;
                final isLocked = _isLocked(item.receivedAt, nowUtc);
                final isRead =
                    isResponded || state.readIds.contains(item.inboxItemId);
                final status = isLocked
                    ? 'Locked'
                    : isResponded
                    ? 'Responded'
                    : null;
                final timestamp = _formatTimestamp(item.receivedAt, nowUtc);
                final subtitle = status == null
                    ? timestamp
                    : '$timestamp \u00b7 $status';
                return ListTile(
                  onTap: () => _openReadingModal(
                    context: context,
                    controller: _controller,
                    item: item,
                    nowUtc: nowUtc,
                    isLocked: isLocked,
                    isResponded: isResponded,
                  ),
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
                  title: Text(
                    _formatThemeEmotion(item),
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(subtitle),
                      if (item.text.isNotEmpty)
                        Text(
                          item.text,
                          style: const TextStyle(color: Colors.black54),
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

  String _formatTimestamp(String value, DateTime nowUtc) {
    if (value.isEmpty) {
      return 'Recently';
    }
    final parsed = DateTime.tryParse(value);
    if (parsed == null) {
      return value;
    }
    return TimeUtils.formatSignalWindow(
      nowUtc: nowUtc,
      receivedAtUtc: parsed.toUtc(),
    );
  }

  String _formatThemeEmotion(InboxItem item) {
    final themeLabel = item.themeTags.isEmpty
        ? 'Support'
        : item.themeTags.join(', ');
    final emotion = item.emotion?.trim();
    if (emotion == null || emotion.isEmpty) {
      return themeLabel;
    }
    return '$themeLabel \u00b7 $emotion';
  }

  bool _isLocked(String value, DateTime nowUtc) {
    final parsed = DateTime.tryParse(value);
    if (parsed == null) {
      return false;
    }
    final day = DateTime.utc(parsed.year, parsed.month, parsed.day);
    final today = DateTime.utc(nowUtc.year, nowUtc.month, nowUtc.day);
    final diffDays = today.difference(day).inDays;
    return diffDays >= inboxLockDays;
  }

  Future<void> _openReadingModal({
    required BuildContext context,
    required InboxController controller,
    required InboxItem item,
    required DateTime nowUtc,
    required bool isLocked,
    required bool isResponded,
  }) async {
    await controller.markRead(item.inboxItemId);
    if (!context.mounted) {
      return;
    }
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useRootNavigator: true,
      backgroundColor: Colors.white,
      builder: (sheetContext) {
        final window = _formatTimestamp(item.receivedAt, nowUtc);
        return SafeArea(
          child: Container(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
            height: MediaQuery.of(sheetContext).size.height * 0.92,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Supportive note',
                      style: TextStyle(fontWeight: FontWeight.w600),
                    ),
                    IconButton(
                      onPressed: () => Navigator.of(sheetContext).pop(),
                      icon: const Icon(Icons.close),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  _formatThemeEmotion(item),
                  style: const TextStyle(fontWeight: FontWeight.w500),
                ),
                const SizedBox(height: 4),
                Text(window, style: const TextStyle(color: Colors.black54)),
                const SizedBox(height: 16),
                Expanded(
                  child: SingleChildScrollView(
                    child: Text(
                      item.text,
                      style: const TextStyle(fontSize: 16),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                if (!isResponded && !isLocked)
                  Wrap(
                    spacing: 8,
                    children: [
                      _AckButton(
                        label: 'Thanks',
                        enabled: true,
                        onPressed: () => controller.acknowledge(
                          inboxItemId: item.inboxItemId,
                          reaction: 'thanks',
                        ),
                      ),
                      _AckButton(
                        label: 'I relate',
                        enabled: true,
                        onPressed: () => controller.acknowledge(
                          inboxItemId: item.inboxItemId,
                          reaction: 'relate',
                        ),
                      ),
                      _AckButton(
                        label: 'Helpful',
                        enabled: true,
                        onPressed: () => controller.acknowledge(
                          inboxItemId: item.inboxItemId,
                          reaction: 'helpful',
                        ),
                      ),
                    ],
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _SecondTouchOfferCard extends StatefulWidget {
  const _SecondTouchOfferCard({
    required this.offerId,
    required this.createdAt,
    required this.offerState,
    required this.nowUtc,
    required this.onSend,
  });

  final String offerId;
  final String createdAt;
  final String offerState;
  final DateTime nowUtc;
  final Future<SecondTouchSendResponse> Function(String text) onSend;

  @override
  State<_SecondTouchOfferCard> createState() => _SecondTouchOfferCardState();
}

class _SecondTouchOfferCardState extends State<_SecondTouchOfferCard> {
  bool _isSending = false;

  @override
  Widget build(BuildContext context) {
    final isAvailable = widget.offerState == 'available' && !_isSending;
    final timestamp = _formatOfferTimestamp(widget.createdAt, widget.nowUtc);
    return Card(
      key: Key('second_touch_offer_${widget.offerId}'),
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'One more note?',
              style: TextStyle(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 6),
            const Text(
              'You\'ve often crossed paths positively. Would you like one more note?',
            ),
            const SizedBox(height: 6),
            Text('One-time only \u00b7 $timestamp'),
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerLeft,
              child: ElevatedButton(
                key: Key('second_touch_send_${widget.offerId}'),
                onPressed: isAvailable ? () => _openComposer(context) : null,
                child: const Text('Send one more note'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _openComposer(BuildContext context) async {
    final text = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      builder: (context) => const _SecondTouchComposer(),
    );
    if (text == null || text.trim().isEmpty) {
      return;
    }
    setState(() => _isSending = true);
    try {
      final response = await widget.onSend(text.trim());
      if (!context.mounted) {
        return;
      }
      if (response.status == 'queued') {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('One-time note sent.')));
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not send right now.')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSending = false);
      }
    }
  }

  String _formatOfferTimestamp(String value, DateTime nowUtc) {
    if (value.isEmpty) {
      return 'Recently';
    }
    final parsed = DateTime.tryParse(value);
    if (parsed == null) {
      return value;
    }
    final day = DateTime.utc(parsed.year, parsed.month, parsed.day);
    final today = DateTime.utc(nowUtc.year, nowUtc.month, nowUtc.day);
    final diffDays = today.difference(day).inDays;
    if (diffDays == 0) {
      return 'Today';
    }
    if (diffDays == 1) {
      return 'Yesterday';
    }
    return day.toIso8601String().split('T').first;
  }
}

class _SecondTouchComposer extends StatefulWidget {
  const _SecondTouchComposer();

  @override
  State<_SecondTouchComposer> createState() => _SecondTouchComposerState();
}

class _SecondTouchComposerState extends State<_SecondTouchComposer> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.of(context).viewInsets.bottom;
    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: bottom + 16,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'One-time note',
            style: TextStyle(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          const Text('This is a one-time note. No replies or threads.'),
          const SizedBox(height: 12),
          TextField(
            key: const Key('second_touch_text_field'),
            controller: _controller,
            maxLength: 280,
            maxLines: 4,
            decoration: const InputDecoration(
              labelText: 'Your note',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerLeft,
            child: ElevatedButton(
              key: const Key('second_touch_send_confirm'),
              onPressed: () => Navigator.of(context).pop(_controller.text),
              child: const Text('Send'),
            ),
          ),
        ],
      ),
    );
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
