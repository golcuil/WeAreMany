import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AppConfig {
  const AppConfig({required this.apiBaseUrl, required this.simulateEnabled});

  final String apiBaseUrl;
  final bool simulateEnabled;
}

final appConfigProvider = Provider<AppConfig>((ref) {
  return AppConfig(
    apiBaseUrl: const String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://localhost:8000',
    ),
    simulateEnabled: kDebugMode,
  );
});
