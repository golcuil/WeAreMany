import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:we_are_many/app/app.dart';
import 'package:we_are_many/core/local/mood_history_store.dart';
import 'package:we_are_many/core/local/profile_store.dart';
import 'package:we_are_many/core/network/api_client.dart';
import 'package:we_are_many/core/network/models.dart';

class FakePrivacyApiClient extends ApiClient {
  FakePrivacyApiClient()
    : super(
        baseUrl: 'http://localhost',
        token: 'dev_test',
        httpClient: MockClient((_) async {
          throw StateError('Unexpected HTTP call in privacy test.');
        }),
      );

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
  testWidgets('Privacy controls clear local data', (tester) async {
    final entries = [
      {
        'date_key': '2026-01-10',
        'emotion_label': 'calm',
        'valence': 'positive',
        'intensity': 'low',
      },
    ];
    SharedPreferences.setMockInitialValues({
      MoodHistoryStore.storageKey: jsonEncode(entries),
      ProfileStore.displayNameKey: 'Nova',
    });

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(FakePrivacyApiClient()),
        ],
        child: const WeAreManyApp(),
      ),
    );

    await tester.tap(find.byKey(const Key('tab_profile')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('profile_settings')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Privacy'));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('privacy_clear_mood_history')));
    await tester.pump();
    await tester.tap(find.byKey(const Key('privacy_reset_display_name')));
    await tester.pump();

    final storedEntries = await MoodHistoryStore.loadEntries();
    expect(storedEntries, isEmpty);
    final displayName = await ProfileStore.loadDisplayName();
    expect(displayName, isEmpty);
  });
}
