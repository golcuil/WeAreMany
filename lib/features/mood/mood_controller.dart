import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/config/app_config.dart';
import '../../core/network/api_client.dart';
import '../../core/network/models.dart';

class MoodState {
  const MoodState({
    this.isLoading = false,
    this.response,
    this.error,
    this.simulateDecision,
    this.simulateEnabled = false,
  });

  final bool isLoading;
  final MoodResponse? response;
  final String? error;
  final MatchSimulateResponse? simulateDecision;
  final bool simulateEnabled;

  MoodState copyWith({
    bool? isLoading,
    MoodResponse? response,
    String? error,
    MatchSimulateResponse? simulateDecision,
    bool? simulateEnabled,
  }) {
    return MoodState(
      isLoading: isLoading ?? this.isLoading,
      response: response ?? this.response,
      error: error,
      simulateDecision: simulateDecision ?? this.simulateDecision,
      simulateEnabled: simulateEnabled ?? this.simulateEnabled,
    );
  }
}

class MoodController extends StateNotifier<MoodState> {
  MoodController({required this.apiClient, required this.simulateEnabled})
    : super(MoodState(simulateEnabled: simulateEnabled));

  final ApiClient apiClient;
  final bool simulateEnabled;

  Future<MoodResponse> submitMood(MoodRequest request) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final response = await apiClient.submitMood(request);
      state = state.copyWith(isLoading: false, response: response);
      return response;
    } on ApiError catch (error) {
      state = state.copyWith(isLoading: false, error: error.message);
      rethrow;
    }
  }

  Future<void> simulateMatch(MatchSimulateRequest request) async {
    if (!simulateEnabled) {
      return;
    }
    state = state.copyWith(isLoading: true, error: null);
    try {
      final response = await apiClient.simulateMatch(request);
      state = state.copyWith(isLoading: false, simulateDecision: response);
    } on ApiError catch (error) {
      state = state.copyWith(isLoading: false, error: error.message);
    }
  }
}

final moodControllerProvider = StateNotifierProvider<MoodController, MoodState>(
  (ref) {
    final config = ref.watch(appConfigProvider);
    final apiClient = ref.watch(apiClientProvider);
    return MoodController(
      apiClient: apiClient,
      simulateEnabled: config.simulateEnabled,
    );
  },
);
