import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/app_config.dart';

class SessionState {
  const SessionState({required this.token});

  final String token;
}

final sessionProvider = Provider<SessionState>((ref) {
  final config = ref.watch(appConfigProvider);
  return SessionState(token: config.devBearerToken);
});
