import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:we_are_many/app/app.dart';
import 'package:we_are_many/core/network/api_client.dart';
import 'package:we_are_many/core/network/models.dart';
import 'package:we_are_many/features/crisis/crisis_screen.dart';
import 'package:we_are_many/features/mood/mood_entry_screen.dart';

class FakeApiClient extends ApiClient {
  FakeApiClient()
      : super(baseUrl: 'http://localhost', token: 'dev_test', httpClient: http.Client());

  @override
  Future<MoodResponse> submitMood(MoodRequest request) async {
    return MoodResponse(
      sanitizedText: 'ok',
      riskLevel: 2,
      reidRisk: 0,
      identityLeak: false,
      leakTypes: const [],
      crisisAction: 'show_crisis',
    );
  }

  @override
  Future<MatchSimulateResponse> simulateMatch(MatchSimulateRequest request) async {
    return MatchSimulateResponse(
      decision: 'HOLD',
      reason: 'insufficient_pool',
      systemGeneratedEmpathy: 'ok',
      finiteContentBridge: 'reflection',
    );
  }
}

void main() {
  testWidgets('Navigates to CrisisScreen when crisis_action is set', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(FakeApiClient())],
        child: const WeAreManyApp(),
      ),
    );

    await tester.tap(find.text('Share a mood'));
    await tester.pumpAndSettle();
    expect(find.byType(MoodEntryScreen), findsOneWidget);

    await tester.tap(find.text('Submit mood'));
    await tester.pumpAndSettle();

    expect(find.byType(CrisisScreen), findsOneWidget);
  });
}
