import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../session/session_provider.dart';
import 'models.dart';

class ApiClient {
  ApiClient({
    required this.baseUrl,
    required this.token,
    required this.httpClient,
  });

  final String baseUrl;
  final String token;
  final http.Client httpClient;

  Future<MoodResponse> submitMood(MoodRequest request) async {
    final response = await httpClient.post(
      Uri.parse('$baseUrl/mood'),
      headers: _headers(),
      body: jsonEncode(request.toJson()),
    );
    return _parseResponse(response, MoodResponse.fromJson);
  }

  Future<MatchSimulateResponse> simulateMatch(
    MatchSimulateRequest request,
  ) async {
    final response = await httpClient.post(
      Uri.parse('$baseUrl/match/simulate'),
      headers: _headers(),
      body: jsonEncode(request.toJson()),
    );
    return _parseResponse(response, MatchSimulateResponse.fromJson);
  }

  Future<InboxResponse> fetchInbox() async {
    final response = await httpClient.get(
      Uri.parse('$baseUrl/inbox'),
      headers: _headers(),
    );
    return _parseResponse(response, InboxResponse.fromJson);
  }

  Future<AcknowledgementResponse> acknowledge(
    AcknowledgementRequest request,
  ) async {
    final response = await httpClient.post(
      Uri.parse('$baseUrl/acknowledgements'),
      headers: _headers(),
      body: jsonEncode(request.toJson()),
    );
    return _parseResponse(response, AcknowledgementResponse.fromJson);
  }

  Map<String, String> _headers() {
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  T _parseResponse<T>(
    http.Response response,
    T Function(Map<String, dynamic>) parser,
  ) {
    final decoded = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode >= 400) {
      final error = decoded['error'] as Map<String, dynamic>? ?? {};
      throw ApiError(
        code: error['code']?.toString() ?? 'unknown_error',
        message: error['message']?.toString() ?? 'Request failed',
        requestId: error['request_id']?.toString() ?? 'unknown',
      );
    }
    return parser(decoded);
  }
}

final apiClientProvider = Provider<ApiClient>((ref) {
  final config = ref.watch(appConfigProvider);
  final session = ref.watch(sessionProvider);
  return ApiClient(
    baseUrl: config.apiBaseUrl,
    token: session.token,
    httpClient: http.Client(),
  );
});
