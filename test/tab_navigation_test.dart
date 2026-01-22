import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'package:we_are_many/app/app.dart';
import 'package:we_are_many/core/network/api_client.dart';
import 'package:we_are_many/core/network/models.dart';
import 'package:we_are_many/features/home/home_screen.dart';
import 'package:we_are_many/features/profile/about_safety_screen.dart';
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
  testWidgets('Bottom nav switches between four tabs', (tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(FakeTabsApiClient())],
        child: const WeAreManyApp(),
      ),
    );

    expect(find.byType(HomeScreen), findsOneWidget);
    expect(find.byKey(const Key('home_screen')), findsOneWidget);
    expect(find.byKey(const Key('tab_home')), findsOneWidget);
    expect(find.byKey(const Key('tab_messages')), findsOneWidget);
    expect(find.byKey(const Key('tab_reflection')), findsOneWidget);
    expect(find.byKey(const Key('tab_profile')), findsOneWidget);
    await tester.tap(find.byKey(const Key('tab_messages')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('inbox_screen')), findsOneWidget);
    await tester.tap(find.byKey(const Key('tab_reflection')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('reflection_screen')), findsOneWidget);
    await tester.tap(find.byKey(const Key('tab_profile')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('profile_screen')), findsOneWidget);
  });

  testWidgets('Profile shows display name and settings entry', (tester) async {
    SharedPreferences.setMockInitialValues({'display_name': 'Ava'});
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(FakeTabsApiClient())],
        child: const WeAreManyApp(),
      ),
    );

    await tester.tap(find.byKey(const Key('tab_profile')));
    await tester.pumpAndSettle();

    expect(find.text('Ava'), findsOneWidget);
    expect(find.byKey(const Key('profile_settings')), findsOneWidget);
  });

  testWidgets('Settings includes About & Safety last', (tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(FakeTabsApiClient())],
        child: const WeAreManyApp(),
      ),
    );

    await tester.tap(find.byKey(const Key('tab_profile')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('profile_settings')));
    await tester.pumpAndSettle();

    expect(find.text('Account'), findsOneWidget);
    expect(find.text('Privacy'), findsOneWidget);
    expect(find.text('Notifications'), findsOneWidget);
    expect(find.text('About & Safety'), findsOneWidget);

    final aboutPosition = tester.getTopLeft(find.text('About & Safety')).dy;
    final privacyPosition = tester.getTopLeft(find.text('Privacy')).dy;
    final notificationsPosition = tester
        .getTopLeft(find.text('Notifications'))
        .dy;
    expect(aboutPosition, greaterThan(privacyPosition));
    expect(aboutPosition, greaterThan(notificationsPosition));
  });

  testWidgets('About & Safety opens and can reach Crisis', (tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(FakeTabsApiClient())],
        child: const WeAreManyApp(),
      ),
    );

    await tester.tap(find.byKey(const Key('tab_profile')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('profile_settings')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('About & Safety'));
    await tester.pumpAndSettle();

    expect(find.byType(AboutSafetyScreen), findsOneWidget);
    await tester.tap(find.text('View crisis resources'));
    await tester.pumpAndSettle();
    expect(find.byType(CrisisScreen), findsOneWidget);
  });
}
