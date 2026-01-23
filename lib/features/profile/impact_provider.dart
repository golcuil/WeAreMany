import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';

final impactCountProvider = FutureProvider<int>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final response = await apiClient.fetchImpact();
  return response.helpedCount;
});
