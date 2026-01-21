import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/network/models.dart';

class InboxState {
  const InboxState({this.items = const [], this.isLoading = false, this.error});

  final List<InboxItem> items;
  final bool isLoading;
  final String? error;

  InboxState copyWith({
    List<InboxItem>? items,
    bool? isLoading,
    String? error,
  }) {
    return InboxState(
      items: items ?? this.items,
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
      final response = await apiClient.fetchInbox();
      state = state.copyWith(items: response.items, isLoading: false);
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
    state = state.copyWith(items: updated, error: null);

    try {
      await apiClient.acknowledge(
        AcknowledgementRequest(inboxItemId: inboxItemId, reaction: reaction),
      );
    } on ApiError catch (error) {
      state = state.copyWith(items: previous, error: error.message);
    }
  }
}

final inboxControllerProvider =
    StateNotifierProvider<InboxController, InboxState>((ref) {
      final apiClient = ref.watch(apiClientProvider);
      return InboxController(apiClient: apiClient);
    });
