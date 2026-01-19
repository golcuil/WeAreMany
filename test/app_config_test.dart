import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:we_are_many/core/config/app_config.dart';

void main() {
  test('AppConfig reads dart-define values with defaults', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    final config = container.read(appConfigProvider);
    expect(
      config.apiBaseUrl,
      const String.fromEnvironment(
        'API_BASE_URL',
        defaultValue: 'http://localhost:8000',
      ),
    );
    final expectedToken = kReleaseMode
        ? ''
        : const String.fromEnvironment(
            'DEV_BEARER_TOKEN',
            defaultValue: '',
          );
    expect(config.devBearerToken, expectedToken);
  });
}
