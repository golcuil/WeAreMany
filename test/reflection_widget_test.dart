import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';

import 'package:we_are_many/core/network/api_client.dart';
import 'package:we_are_many/core/network/models.dart';
import 'package:we_are_many/features/reflection/reflection_screen.dart';

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
      trend: 'up',
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

  @override
  Future<ImpactResponse> fetchImpact() async {
    return ImpactResponse(helpedCount: 0);
  }
}

class EmptyReflectionApiClient extends FakeReflectionApiClient {
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
  testWidgets('Reflection screen shows empty state', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(EmptyReflectionApiClient()),
        ],
        child: const MaterialApp(home: ReflectionScreen()),
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byKey(const Key('reflection_screen')), findsOneWidget);
    expect(find.text('Start your journey'), findsOneWidget);
  });

  testWidgets('Reflection screen renders summary', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(FakeReflectionApiClient()),
        ],
        child: const MaterialApp(home: ReflectionScreen()),
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byKey(const Key('reflection_screen')), findsOneWidget);
    expect(find.text('Feeling lighter overall'), findsOneWidget);
    expect(find.byKey(const Key('mood_ring')), findsOneWidget);
  });
}
