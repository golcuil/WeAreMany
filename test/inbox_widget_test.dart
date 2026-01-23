import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'package:we_are_many/features/inbox/inbox_screen.dart';
import 'package:we_are_many/core/network/api_client.dart';
import 'package:we_are_many/core/network/models.dart';

class FakeInboxApiClient extends ApiClient {
  FakeInboxApiClient(this.items)
    : super(
        baseUrl: 'http://localhost',
        token: 'dev_test',
        httpClient: http.Client(),
      );

  final List<InboxItem> items;
  int ackCalls = 0;
  String? lastReaction;

  @override
  Future<InboxResponse> fetchInbox() async {
    return InboxResponse(
      items: items,
      nextCursor: null,
    );
  }

  @override
  Future<AcknowledgementResponse> acknowledge(
    AcknowledgementRequest request,
  ) async {
    ackCalls += 1;
    lastReaction = request.reaction;
    return AcknowledgementResponse(status: 'already_recorded');
  }

  @override
  Future<ImpactResponse> fetchImpact() async {
    return ImpactResponse(helpedCount: 0);
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
}

void main() {
  testWidgets('Inbox loads and renders list', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final now = DateTime.now().toUtc();
    final today = DateTime.utc(now.year, now.month, now.day);
    final client = FakeInboxApiClient([
      InboxItem(
        inboxItemId: 'i1',
        text: 'A supportive note',
        receivedAt: today.toIso8601String(),
        ackStatus: null,
      ),
    ]);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(client)],
        child: const MaterialApp(home: InboxScreen()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('A supportive note'), findsOneWidget);
    expect(find.text('Today'), findsOneWidget);
  });

  testWidgets('Ack button triggers call and updates UI', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final now = DateTime.now().toUtc();
    final today = DateTime.utc(now.year, now.month, now.day);
    final client = FakeInboxApiClient([
      InboxItem(
        inboxItemId: 'i1',
        text: 'A supportive note',
        receivedAt: today.toIso8601String(),
        ackStatus: null,
      ),
    ]);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(client)],
        child: const MaterialApp(home: InboxScreen()),
      ),
    );
    await tester.pumpAndSettle();

    final thanksButton = find.widgetWithText(TextButton, 'Thanks');
    expect(thanksButton, findsOneWidget);
    await tester.tap(thanksButton);
    await tester.pumpAndSettle();

    expect(client.ackCalls, 1);
    expect(client.lastReaction, 'thanks');
    final buttonWidget = tester.widget<TextButton>(thanksButton);
    expect(buttonWidget.onPressed, isNull);
  });

  testWidgets('Unread indicator clears after tap', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final now = DateTime.now().toUtc();
    final today = DateTime.utc(now.year, now.month, now.day);
    final client = FakeInboxApiClient([
      InboxItem(
        inboxItemId: 'i1',
        text: 'A supportive note',
        receivedAt: today.toIso8601String(),
        ackStatus: null,
      ),
    ]);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(client)],
        child: const MaterialApp(home: InboxScreen()),
      ),
    );
    await tester.pumpAndSettle();

    final unreadDot = find.byKey(const Key('inbox_unread_dot_i1'));
    expect(unreadDot, findsOneWidget);
    await tester.tap(find.text('A supportive note'));
    await tester.pumpAndSettle();
    expect(unreadDot, findsNothing);
  });

  testWidgets('Locked items disable acknowledgements', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final now = DateTime.now().toUtc();
    final day = DateTime.utc(now.year, now.month, now.day)
        .subtract(const Duration(days: 8));
    final client = FakeInboxApiClient([
      InboxItem(
        inboxItemId: 'i1',
        text: 'An older note',
        receivedAt: day.toIso8601String(),
        ackStatus: null,
      ),
    ]);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(client)],
        child: const MaterialApp(home: InboxScreen()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.textContaining('Locked'), findsOneWidget);
    final thanksButton = tester.widget<TextButton>(
      find.widgetWithText(TextButton, 'Thanks'),
    );
    expect(thanksButton.onPressed, isNull);
  });

  testWidgets('Timestamp uses Today and Yesterday labels', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final now = DateTime.now().toUtc();
    final today = DateTime.utc(now.year, now.month, now.day);
    final yesterday = today.subtract(const Duration(days: 1));
    final client = FakeInboxApiClient([
      InboxItem(
        inboxItemId: 'i1',
        text: 'Today note',
        receivedAt: today.toIso8601String(),
        ackStatus: null,
      ),
      InboxItem(
        inboxItemId: 'i2',
        text: 'Yesterday note',
        receivedAt: yesterday.toIso8601String(),
        ackStatus: null,
      ),
    ]);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(client)],
        child: const MaterialApp(home: InboxScreen()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Today'), findsOneWidget);
    expect(find.text('Yesterday'), findsOneWidget);
  });
}
