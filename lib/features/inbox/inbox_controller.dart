import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/network/models.dart';
import '../../core/local/inbox_read_store.dart';

class InboxState {
  const InboxState({
    this.items = const [],
    this.readIds = const {},
    this.isLoading = false,
    this.error,
  });

  final List<InboxItem> items;
  final Set<String> readIds;
  final bool isLoading;
  final String? error;

  InboxState copyWith({
    List<InboxItem>? items,
    Set<String>? readIds,
    bool? isLoading,
    String? error,
  }) {
    return InboxState(
      items: items ?? this.items,
      readIds: readIds ?? this.readIds,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

class InboxController extends StateNotifier<InboxState> {
  InboxController({required this.apiClient}) : super(const InboxState());

  final ApiClient apiClient;

  Future<void> load() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final readIds = await InboxReadStore.loadReadIds();
      final response = await apiClient.fetchInbox();
      state = state.copyWith(
        items: response.items,
        readIds: readIds,
        isLoading: false,
      );
    } on ApiError catch (error) {
      state = state.copyWith(isLoading: false, error: error.message);
    }
  }

  Future<void> refresh() async {
    await load();
  }

  Future<void> acknowledge({
    required String inboxItemId,
    required String reaction,
  }) async {
    final previous = state.items;
    final previousRead = state.readIds;
    final updatedRead = {...state.readIds, inboxItemId};
    final updated = state.items
        .map(
          (item) => item.inboxItemId == inboxItemId
              ? InboxItem(
                  inboxItemId: item.inboxItemId,
                  text: item.text,
                  receivedAt: item.receivedAt,
                  ackStatus: reaction,
                )
              : item,
        )
        .toList();
    state = state.copyWith(items: updated, readIds: updatedRead, error: null);
    await InboxReadStore.markRead(inboxItemId);

    try {
      await apiClient.acknowledge(
        AcknowledgementRequest(inboxItemId: inboxItemId, reaction: reaction),
      );
    } on ApiError catch (error) {
      state = state.copyWith(
        items: previous,
        readIds: previousRead,
        error: error.message,
      );
    }
  }

  Future<void> markRead(String inboxItemId) async {
    if (state.readIds.contains(inboxItemId)) {
      return;
    }
    final updatedRead = {...state.readIds, inboxItemId};
    state = state.copyWith(readIds: updatedRead);
    await InboxReadStore.markRead(inboxItemId);
  }
}

final inboxControllerProvider =
    StateNotifierProvider<InboxController, InboxState>((ref) {
      final apiClient = ref.watch(apiClientProvider);
      return InboxController(apiClient: apiClient);
    });
