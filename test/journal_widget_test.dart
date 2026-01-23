import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:we_are_many/app/app.dart';
import 'package:we_are_many/core/local/journal_store.dart';
import 'package:we_are_many/core/network/api_client.dart';
import 'package:we_are_many/core/network/models.dart';
import 'package:we_are_many/features/reflection/journal_entry_screen.dart';

class FakeJournalApiClient extends ApiClient {
  FakeJournalApiClient()
    : super(
        baseUrl: 'http://localhost',
        token: 'dev_test',
        httpClient: MockClient((_) async {
          throw StateError('Unexpected HTTP call in journal test.');
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
  testWidgets('Today entry can be created and edited', (tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(FakeJournalApiClient()),
        ],
        child: MaterialApp(
          home: JournalEntryScreen(now: DateTime.utc(2026, 1, 20)),
        ),
      ),
    );

    expect(find.byKey(const Key('journal_text_field')), findsOneWidget);
    await tester.enterText(
      find.byKey(const Key('journal_text_field')),
      'Hello',
    );
    await tester.tap(find.byKey(const Key('journal_save')));
    await tester.pump();

    final entries = await JournalStore.loadEntries();
    expect(entries.length, 1);
    expect(entries.first.text, 'Hello');
  });

  testWidgets('Past entry is read-only and can be deleted', (tester) async {
    final entries = [
      {'date_key': '2026-01-19', 'text': 'Past entry'},
    ];
    SharedPreferences.setMockInitialValues({
      JournalStore.storageKey: jsonEncode(entries),
    });

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(FakeJournalApiClient()),
        ],
        child: MaterialApp(
          home: JournalEntryScreen(
            entry: JournalEntry(dateKey: '2026-01-19', text: 'Past entry'),
            now: DateTime.utc(2026, 1, 20),
          ),
        ),
      ),
    );

    expect(find.byKey(const Key('journal_text_field')), findsNothing);
    expect(find.byKey(const Key('journal_read_only')), findsOneWidget);
    await tester.tap(find.byKey(const Key('journal_delete')));
    await tester.pump();

    final stored = await JournalStore.loadEntries();
    expect(stored, isEmpty);
  });

  testWidgets('Reflection list updates on 7/30 toggle', (tester) async {
    final now = DateTime.now().toUtc();
    final todayKey = _dateKey(now);
    final tenDaysAgoKey = _dateKey(now.subtract(const Duration(days: 10)));
    final entries = [
      {'date_key': todayKey, 'text': 'Today'},
      {'date_key': tenDaysAgoKey, 'text': 'Older'},
    ];
    SharedPreferences.setMockInitialValues({
      JournalStore.storageKey: jsonEncode(entries),
    });

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(FakeJournalApiClient()),
        ],
        child: const WeAreManyApp(),
      ),
    );

    await tester.tap(find.byKey(const Key('tab_reflection')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text(todayKey), findsOneWidget);
    expect(find.text(tenDaysAgoKey), findsNothing);

    await tester.tap(find.text('30 days'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text(tenDaysAgoKey), findsOneWidget);
  });
}

String _dateKey(DateTime value) {
  return '${value.year.toString().padLeft(4, '0')}-'
      '${value.month.toString().padLeft(2, '0')}-'
      '${value.day.toString().padLeft(2, '0')}';
}
