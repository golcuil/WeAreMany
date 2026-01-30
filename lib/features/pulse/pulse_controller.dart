import 'dart:async';

import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/network/models.dart';

class PulseState {
  const PulseState({
    this.isLoading = false,
    this.error,
    this.distribution = const {},
    this.updatedAtBucket,
  });

  final bool isLoading;
  final String? error;
  final Map<String, int> distribution;
  final DateTime? updatedAtBucket;

  PulseState copyWith({
    bool? isLoading,
    String? error,
    Map<String, int>? distribution,
    DateTime? updatedAtBucket,
  }) {
    return PulseState(
      isLoading: isLoading ?? this.isLoading,
      error: error,
      distribution: distribution ?? this.distribution,
      updatedAtBucket: updatedAtBucket ?? this.updatedAtBucket,
    );
  }
}

class PulseController extends StateNotifier<PulseState>
    with WidgetsBindingObserver {
  PulseController({
    required this.apiClient,
    bool autoStart = true,
  }) : super(const PulseState()) {
    if (autoStart) {
      _observerAttached = true;
      WidgetsBinding.instance.addObserver(this);
      _startPolling();
    }
  }

  final ApiClient apiClient;
  Timer? _timer;
  bool _observerAttached = false;

  Future<void> load({int windowHours = 24}) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final summary = await apiClient.fetchPulseSummary(
        windowHours: windowHours,
      );
      state = state.copyWith(
        isLoading: false,
        distribution: summary.distribution,
        updatedAtBucket: summary.updatedAtBucket,
      );
    } on ApiError catch (error) {
      state = state.copyWith(isLoading: false, error: error.message);
    }
  }

  void _startPolling() {
    _timer?.cancel();
    _timer = Timer.periodic(
      const Duration(minutes: 10),
      (_) => load(),
    );
    unawaited(load());
  }

  void _stopPolling() {
    _timer?.cancel();
    _timer = null;
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused) {
      _stopPolling();
    } else if (state == AppLifecycleState.resumed) {
      _startPolling();
    }
  }

  @override
  void dispose() {
    if (_observerAttached) {
      WidgetsBinding.instance.removeObserver(this);
      _observerAttached = false;
    }
    _stopPolling();
    super.dispose();
  }
}

final pulseControllerProvider =
    StateNotifierProvider<PulseController, PulseState>((ref) {
      final apiClient = ref.watch(apiClientProvider);
      return PulseController(apiClient: apiClient);
    });
