import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/network/models.dart';

class ReflectionState {
  const ReflectionState({this.isLoading = false, this.summary, this.error});

  final bool isLoading;
  final ReflectionSummary? summary;
  final String? error;

  ReflectionState copyWith({
    bool? isLoading,
    ReflectionSummary? summary,
    String? error,
  }) {
    return ReflectionState(
      isLoading: isLoading ?? this.isLoading,
      summary: summary ?? this.summary,
      error: error,
    );
  }
}

class ReflectionController extends StateNotifier<ReflectionState> {
  ReflectionController({required this.apiClient})
    : super(const ReflectionState());

  final ApiClient apiClient;

  Future<void> load({int windowDays = 7}) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final summary = await apiClient.fetchReflectionSummary(
        windowDays: windowDays,
      );
      state = state.copyWith(isLoading: false, summary: summary);
    } on ApiError catch (error) {
      state = state.copyWith(isLoading: false, error: error.message);
    }
  }
}

final reflectionControllerProvider =
    StateNotifierProvider<ReflectionController, ReflectionState>((ref) {
      final apiClient = ref.watch(apiClientProvider);
      return ReflectionController(apiClient: apiClient);
    });
