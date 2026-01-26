import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'package:we_are_many/features/inbox/inbox_screen.dart';
import 'package:we_are_many/core/network/api_client.dart';
import 'package:we_are_many/core/network/models.dart';

class FakeInboxApiClient extends ApiClient {
  FakeInboxApiClient(this.items, {this.sendResponse})
    : super(
        baseUrl: 'http://localhost',
        token: 'dev_test',
        httpClient: http.Client(),
      );

  final List<InboxItem> items;
  final SecondTouchSendResponse? sendResponse;
  int ackCalls = 0;
  String? lastReaction;
  int sendCalls = 0;
  String? lastOfferId;
  String? lastText;

  @override
  Future<InboxResponse> fetchInbox() async {
    return InboxResponse(items: items, nextCursor: null);
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

  @override
  Future<SecondTouchSendResponse> sendSecondTouch(
    SecondTouchSendRequest request,
  ) async {
    sendCalls += 1;
    lastOfferId = request.offerId;
    lastText = request.freeText;
    return sendResponse ?? SecondTouchSendResponse(status: 'queued');
  }
}

void main() {
  testWidgets('Inbox loads and renders list', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final fixedNow = DateTime.utc(2026, 1, 23, 12);
    final today = DateTime.utc(fixedNow.year, fixedNow.month, fixedNow.day);
    final client = FakeInboxApiClient([
      InboxItem(
        itemType: 'message',
        inboxItemId: 'i1',
        text: 'A supportive note',
        receivedAt: today.toIso8601String(),
        ackStatus: null,
        offerId: null,
        offerState: null,
      ),
    ]);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(client)],
        child: MaterialApp(home: InboxScreen(nowUtc: fixedNow)),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('A supportive note'), findsOneWidget);
    expect(find.text('Today'), findsOneWidget);
  });

  testWidgets('Ack button triggers call and updates UI', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final fixedNow = DateTime.utc(2026, 1, 23, 12);
    final today = DateTime.utc(fixedNow.year, fixedNow.month, fixedNow.day);
    final client = FakeInboxApiClient([
      InboxItem(
        itemType: 'message',
        inboxItemId: 'i1',
        text: 'A supportive note',
        receivedAt: today.toIso8601String(),
        ackStatus: null,
        offerId: null,
        offerState: null,
      ),
    ]);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(client)],
        child: MaterialApp(home: InboxScreen(nowUtc: fixedNow)),
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
    final fixedNow = DateTime.utc(2026, 1, 23, 12);
    final today = DateTime.utc(fixedNow.year, fixedNow.month, fixedNow.day);
    final client = FakeInboxApiClient([
      InboxItem(
        itemType: 'message',
        inboxItemId: 'i1',
        text: 'A supportive note',
        receivedAt: today.toIso8601String(),
        ackStatus: null,
        offerId: null,
        offerState: null,
      ),
    ]);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(client)],
        child: MaterialApp(home: InboxScreen(nowUtc: fixedNow)),
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
    final fixedNow = DateTime.utc(2026, 1, 23, 12);
    final day = DateTime.utc(
      fixedNow.year,
      fixedNow.month,
      fixedNow.day,
    ).subtract(const Duration(days: 8));
    final client = FakeInboxApiClient([
      InboxItem(
        itemType: 'message',
        inboxItemId: 'i1',
        text: 'An older note',
        receivedAt: day.toIso8601String(),
        ackStatus: null,
        offerId: null,
        offerState: null,
      ),
    ]);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(client)],
        child: MaterialApp(home: InboxScreen(nowUtc: fixedNow)),
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
    final fixedNow = DateTime.utc(2026, 1, 23, 12);
    final today = DateTime.utc(fixedNow.year, fixedNow.month, fixedNow.day);
    final yesterday = today.subtract(const Duration(days: 1));
    final client = FakeInboxApiClient([
      InboxItem(
        itemType: 'message',
        inboxItemId: 'i1',
        text: 'Today note',
        receivedAt: today.toIso8601String(),
        ackStatus: null,
        offerId: null,
        offerState: null,
      ),
      InboxItem(
        itemType: 'message',
        inboxItemId: 'i2',
        text: 'Yesterday note',
        receivedAt: yesterday.toIso8601String(),
        ackStatus: null,
        offerId: null,
        offerState: null,
      ),
    ]);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(client)],
        child: MaterialApp(home: InboxScreen(nowUtc: fixedNow)),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Today'), findsOneWidget);
    expect(find.text('Yesterday'), findsOneWidget);
  });

  testWidgets('Second touch offer renders and opens composer', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final fixedNow = DateTime.utc(2026, 1, 23, 12);
    final today = DateTime.utc(fixedNow.year, fixedNow.month, fixedNow.day);
    final client = FakeInboxApiClient([
      InboxItem(
        itemType: 'second_touch_offer',
        inboxItemId: '',
        text: '',
        receivedAt: today.toIso8601String(),
        ackStatus: null,
        offerId: 'offer_1',
        offerState: 'available',
      ),
    ]);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(client)],
        child: MaterialApp(home: InboxScreen(nowUtc: fixedNow)),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('second_touch_offer_offer_1')), findsOneWidget);
    await tester.tap(find.byKey(const Key('second_touch_send_offer_1')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('second_touch_text_field')), findsOneWidget);
  });

  testWidgets('Second touch send triggers API and locks offer', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final fixedNow = DateTime.utc(2026, 1, 23, 12);
    final today = DateTime.utc(fixedNow.year, fixedNow.month, fixedNow.day);
    final client = FakeInboxApiClient([
      InboxItem(
        itemType: 'second_touch_offer',
        inboxItemId: '',
        text: '',
        receivedAt: today.toIso8601String(),
        ackStatus: null,
        offerId: 'offer_1',
        offerState: 'available',
      ),
    ], sendResponse: SecondTouchSendResponse(status: 'queued'));
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(client)],
        child: MaterialApp(home: InboxScreen(nowUtc: fixedNow)),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('second_touch_send_offer_1')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('second_touch_text_field')),
      'One more note',
    );
    await tester.tap(find.byKey(const Key('second_touch_send_confirm')));
    await tester.pumpAndSettle();

    expect(client.sendCalls, 1);
    expect(client.lastOfferId, 'offer_1');
    expect(client.lastText, 'One more note');

    final button = tester.widget<ElevatedButton>(
      find.byKey(const Key('second_touch_send_offer_1')),
    );
    expect(button.onPressed, isNull);
  });
}
