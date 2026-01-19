import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;

import 'package:we_are_many/app/app.dart';
import 'package:we_are_many/core/network/api_client.dart';
import 'package:we_are_many/core/network/models.dart';

class FakeInboxApiClient extends ApiClient {
  FakeInboxApiClient()
      : super(baseUrl: 'http://localhost', token: 'dev_test', httpClient: http.Client());

  int ackCalls = 0;
  String? lastReaction;

  @override
  Future<InboxResponse> fetchInbox() async {
    return InboxResponse(
      items: [
        InboxItem(
          inboxItemId: 'i1',
          text: 'A supportive note',
          receivedAt: 'today',
          ackStatus: null,
        ),
      ],
      nextCursor: null,
    );
  }

  @override
  Future<AcknowledgementResponse> acknowledge(AcknowledgementRequest request) async {
    ackCalls += 1;
    lastReaction = request.reaction;
    return AcknowledgementResponse(status: 'recorded');
  }
}

void main() {
  testWidgets('Inbox loads and renders list', (tester) async {
    final client = FakeInboxApiClient();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(client)],
        child: const WeAreManyApp(),
      ),
    );

    await tester.tap(find.text('Inbox'));
    await tester.pumpAndSettle();

    expect(find.text('A supportive note'), findsOneWidget);
    expect(find.text('today'), findsOneWidget);
  });

  testWidgets('Ack button triggers call and updates UI', (tester) async {
    final client = FakeInboxApiClient();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(client)],
        child: const WeAreManyApp(),
      ),
    );

    await tester.tap(find.text('Inbox'));
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
}
