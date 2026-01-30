import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:we_are_many/core/network/api_client.dart';
import 'package:we_are_many/features/pulse/pulse_controller.dart';

class _NoopApiClient implements ApiClient {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class TestPulseController extends PulseController {
  TestPulseController({Map<String, int> distribution = const {}})
    : super(apiClient: _NoopApiClient(), autoStart: false) {
    state = PulseState(distribution: distribution);
  }
}

Override pulseOverride({Map<String, int> distribution = const {}}) {
  return pulseControllerProvider.overrideWith(
    (ref) => TestPulseController(distribution: distribution),
  );
}
