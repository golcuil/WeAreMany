import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

class InboxReadStore {
  static const storageKey = 'inbox_read_v1';

  static Future<Set<String>> loadReadIds({SharedPreferences? prefs}) async {
    final storage = prefs ?? await SharedPreferences.getInstance();
    final raw = storage.getString(storageKey);
    if (raw == null || raw.isEmpty) {
      return {};
    }
    final decoded = jsonDecode(raw);
    if (decoded is! List) {
      return {};
    }
    return decoded.whereType<String>().toSet();
  }

  static Future<void> markRead(
    String inboxItemId, {
    SharedPreferences? prefs,
  }) async {
    final storage = prefs ?? await SharedPreferences.getInstance();
    final ids = await loadReadIds(prefs: storage);
    if (!ids.add(inboxItemId)) {
      return;
    }
    final sorted = ids.toList()..sort();
    await storage.setString(storageKey, jsonEncode(sorted));
  }
}
