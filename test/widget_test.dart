import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:we_are_many/app/app.dart';
import 'package:we_are_many/core/network/api_client.dart';
import 'package:we_are_many/core/network/models.dart';
import 'package:we_are_many/features/mood/mood_entry_screen.dart';

class FakeApiClient extends ApiClient {
  FakeApiClient()
    : super(
        baseUrl: 'http://localhost',
        token: 'dev_test',
        httpClient: MockClient((_) async {
          throw StateError('Unexpected HTTP call in widget test.');
        }),
      );

  @override
  Future<MoodResponse> submitMood(MoodRequest request) async {
    return MoodResponse(
      status: 'blocked',
      sanitizedText: 'ok',
      riskLevel: 2,
      reidRisk: 0,
      identityLeak: false,
      leakTypes: const [],
      crisisAction: 'show_resources',
    );
  }

  @override
  Future<MatchSimulateResponse> simulateMatch(
    MatchSimulateRequest request,
  ) async {
    return MatchSimulateResponse(
      decision: 'HOLD',
      reason: 'insufficient_pool',
      systemGeneratedEmpathy: 'ok',
      finiteContentBridge: 'reflection',
    );
  }

  @override
  Future<ReflectionSummary> fetchReflectionSummary({int windowDays = 7}) async {
    return ReflectionSummary(
      windowDays: windowDays,
      totalEntries: 0,
      distribution: const {},
      trend: 'stable',
      volatilityDays: 0,
    );
  }

  @override
  Future<InboxResponse> fetchInbox() async {
    return InboxResponse(items: const [], nextCursor: null);
  }

  @override
  Future<AcknowledgementResponse> acknowledge(
    AcknowledgementRequest request,
  ) async {
    return AcknowledgementResponse(status: 'recorded');
  }

  @override
  Future<ImpactResponse> fetchImpact() async {
    return ImpactResponse(helpedCount: 0);
  }
}

class NonCrisisApiClient extends ApiClient {
  NonCrisisApiClient()
    : super(
        baseUrl: 'http://localhost',
        token: 'dev_test',
        httpClient: MockClient((_) async {
          throw StateError('Unexpected HTTP call in widget test.');
        }),
      );

  @override
  Future<MoodResponse> submitMood(MoodRequest request) async {
    return MoodResponse(
      status: 'ok',
      sanitizedText: 'sanitized',
      riskLevel: 0,
      reidRisk: 0.1,
      identityLeak: false,
      leakTypes: const [],
      crisisAction: null,
    );
  }

  @override
  Future<MatchSimulateResponse> simulateMatch(
    MatchSimulateRequest request,
  ) async {
    return MatchSimulateResponse(
      decision: 'HOLD',
      reason: 'insufficient_pool',
      systemGeneratedEmpathy: 'ok',
      finiteContentBridge: 'reflection',
    );
  }

  @override
  Future<ReflectionSummary> fetchReflectionSummary({int windowDays = 7}) async {
    return ReflectionSummary(
      windowDays: windowDays,
      totalEntries: 0,
      distribution: const {},
      trend: 'stable',
      volatilityDays: 0,
    );
  }

  @override
  Future<InboxResponse> fetchInbox() async {
    return InboxResponse(items: const [], nextCursor: null);
  }

  @override
  Future<AcknowledgementResponse> acknowledge(
    AcknowledgementRequest request,
  ) async {
    return AcknowledgementResponse(status: 'recorded');
  }

  @override
  Future<ImpactResponse> fetchImpact() async {
    return ImpactResponse(helpedCount: 0);
  }
}

void main() {
  testWidgets('Navigates to CrisisScreen when crisis_action is set', (
    tester,
  ) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(FakeApiClient())],
        child: const WeAreManyApp(),
      ),
    );

    await tester.tap(find.text('Share a mood'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.byType(MoodEntryScreen), findsOneWidget);

    await tester.tap(find.text('Submit mood'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byKey(const Key('crisis_screen')), findsOneWidget);
  });

  testWidgets('Non-crisis response shows sanitized text only', (tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(NonCrisisApiClient())],
        child: const WeAreManyApp(),
      ),
    );

    await tester.tap(find.text('Share a mood'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    await tester.enterText(find.byType(TextField), 'raw secret text');
    await tester.tap(find.text('Submit mood'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.textContaining('Sanitized:'), findsOneWidget);
    expect(find.text('raw secret text'), findsNothing);
  });
}
