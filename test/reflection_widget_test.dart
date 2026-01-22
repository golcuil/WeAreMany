import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';

import 'package:we_are_many/app/app.dart';
import 'package:we_are_many/core/network/api_client.dart';
import 'package:we_are_many/core/network/models.dart';

class FakeReflectionApiClient extends ApiClient {
  FakeReflectionApiClient()
    : super(
        baseUrl: 'http://localhost',
        token: 'dev_test',
        httpClient: MockClient((_) async {
          throw StateError('Unexpected HTTP call in reflection test.');
        }),
      );

  @override
  Future<ReflectionSummary> fetchReflectionSummary({int windowDays = 7}) async {
    return ReflectionSummary(
      windowDays: windowDays,
      totalEntries: 3,
      distribution: const {'calm': 1, 'sad': 2},
      trend: 'down',
      volatilityDays: 2,
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
  testWidgets('Reflection screen renders summary', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(FakeReflectionApiClient()),
        ],
        child: const WeAreManyApp(),
      ),
    );

    await tester.tap(find.byKey(const Key('tab_reflection')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byKey(const Key('reflection_screen')), findsOneWidget);
    expect(find.textContaining('Entries:'), findsOneWidget);
    expect(find.text('calm: 1'), findsOneWidget);
    expect(find.text('sad: 2'), findsOneWidget);
  });
}
