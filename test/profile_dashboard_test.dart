import 'dart:convert';

import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';

import 'package:shared_preferences/shared_preferences.dart';
import 'package:we_are_many/app/app.dart';
import 'package:we_are_many/core/local/mood_history_store.dart';
import 'package:we_are_many/core/network/api_client.dart';
import 'package:we_are_many/core/network/models.dart';

class FakeDashboardApiClient extends ApiClient {
  FakeDashboardApiClient()
    : super(
        baseUrl: 'http://localhost',
        token: 'dev_test',
        httpClient: MockClient((_) async {
          throw StateError('Unexpected HTTP call in dashboard test.');
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
}

void main() {
  testWidgets('Profile dashboard shows counts and updates on toggle', (
    tester,
  ) async {
    final now = DateTime.now().toUtc();
    final today = _dateKey(now);
    final tenDaysAgo = _dateKey(now.subtract(const Duration(days: 10)));
    final entries = [
      {
        'date_key': today,
        'emotion_label': 'calm',
        'valence': 'positive',
        'intensity': 'low',
      },
      {
        'date_key': tenDaysAgo,
        'emotion_label': 'sad',
        'valence': 'negative',
        'intensity': 'medium',
      },
    ];
    SharedPreferences.setMockInitialValues({
      MoodHistoryStore.storageKey: jsonEncode(entries),
    });

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(FakeDashboardApiClient()),
        ],
        child: const WeAreManyApp(),
      ),
    );

    await tester.tap(find.byKey(const Key('tab_profile')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Dashboard'), findsOneWidget);
    expect(
      find.textContaining('You marked your mood 1 times (last 7 days)'),
      findsOneWidget,
    );

    await tester.tap(find.byKey(const Key('dashboard_toggle_30')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(
      find.textContaining('You marked your mood 2 times (last 30 days)'),
      findsOneWidget,
    );
  });
}

String _dateKey(DateTime value) {
  return '${value.year.toString().padLeft(4, '0')}-'
      '${value.month.toString().padLeft(2, '0')}-'
      '${value.day.toString().padLeft(2, '0')}';
}
