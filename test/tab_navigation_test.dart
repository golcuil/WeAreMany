import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;

import 'package:we_are_many/app/app.dart';
import 'package:we_are_many/core/network/api_client.dart';
import 'package:we_are_many/core/network/models.dart';
import 'package:we_are_many/features/home/home_screen.dart';
import 'package:we_are_many/features/inbox/inbox_screen.dart';
import 'package:we_are_many/features/profile/about_safety_screen.dart';
import 'package:we_are_many/features/profile/profile_screen.dart';
import 'package:we_are_many/features/reflection/reflection_screen.dart';
import 'package:we_are_many/features/crisis/crisis_screen.dart';

class FakeTabsApiClient extends ApiClient {
  FakeTabsApiClient()
    : super(
        baseUrl: 'http://localhost',
        token: 'dev_test',
        httpClient: http.Client(),
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
}

void main() {
  testWidgets('Bottom nav switches between four tabs', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(FakeTabsApiClient())],
        child: const WeAreManyApp(),
      ),
    );

    expect(find.byType(HomeScreen), findsOneWidget);
    await tester.tap(find.text('Messages'));
    await tester.pumpAndSettle();
    expect(find.byType(InboxScreen), findsOneWidget);
    await tester.tap(find.text('Reflection'));
    await tester.pumpAndSettle();
    expect(find.byType(ReflectionScreen), findsOneWidget);
    await tester.tap(find.text('Profile'));
    await tester.pumpAndSettle();
    expect(find.byType(ProfileScreen), findsOneWidget);
  });

  testWidgets('Profile items include About & Safety last', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(FakeTabsApiClient())],
        child: const WeAreManyApp(),
      ),
    );

    await tester.tap(find.text('Profile'));
    await tester.pumpAndSettle();

    expect(find.text('Account'), findsOneWidget);
    expect(find.text('Privacy'), findsOneWidget);
    expect(find.text('Notifications'), findsOneWidget);
    expect(find.text('About & Safety'), findsOneWidget);

    final aboutPosition = tester.getTopLeft(find.text('About & Safety')).dy;
    final privacyPosition = tester.getTopLeft(find.text('Privacy')).dy;
    final notificationsPosition = tester.getTopLeft(find.text('Notifications')).dy;
    expect(aboutPosition, greaterThan(privacyPosition));
    expect(aboutPosition, greaterThan(notificationsPosition));
  });

  testWidgets('About & Safety opens and can reach Crisis', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(FakeTabsApiClient())],
        child: const WeAreManyApp(),
      ),
    );

    await tester.tap(find.text('Profile'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('About & Safety'));
    await tester.pumpAndSettle();

    expect(find.byType(AboutSafetyScreen), findsOneWidget);
    await tester.tap(find.text('View crisis resources'));
    await tester.pumpAndSettle();
    expect(find.byType(CrisisScreen), findsOneWidget);
  });
}
