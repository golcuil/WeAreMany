import 'package:flutter_riverpod/flutter_riverpod.dart';

class SessionState {
  const SessionState({required this.token});

  final String token;
}

final sessionProvider = Provider<SessionState>((ref) {
  return const SessionState(token: 'dev_test');
});
