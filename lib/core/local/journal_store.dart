import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

class JournalEntry {
  JournalEntry({
    required this.dateKey,
    required this.text,
    this.emotionLabel,
  });

  final String dateKey;
  final String text;
  final String? emotionLabel;

  Map<String, dynamic> toJson() {
    return {
      'date_key': dateKey,
      'text': text,
      if (emotionLabel != null) 'emotion_label': emotionLabel,
    };
  }

  factory JournalEntry.fromJson(Map<String, dynamic> json) {
    return JournalEntry(
      dateKey: json['date_key'] as String? ?? '',
      text: json['text'] as String? ?? '',
      emotionLabel: json['emotion_label'] as String?,
    );
  }
}

class JournalStore {
  static const storageKey = 'journal_entries_v1';
  static const maxEntries = 60;
  static const maxLength = 500;

  static Future<List<JournalEntry>> loadEntries({
    SharedPreferences? prefs,
  }) async {
    final storage = prefs ?? await SharedPreferences.getInstance();
    final raw = storage.getString(storageKey);
    if (raw == null || raw.isEmpty) {
      return [];
    }
    final decoded = jsonDecode(raw);
    if (decoded is! List) {
      return [];
    }
    return decoded
        .whereType<Map<String, dynamic>>()
        .map(JournalEntry.fromJson)
        .toList();
  }

  static Future<bool> saveTodayEntry(
    String text, {
    String? emotionLabel,
    DateTime? now,
    String? dateKeyOverride,
    SharedPreferences? prefs,
  }) async {
    final timestamp = (now ?? DateTime.now().toUtc());
    final todayKey = _dateKey(timestamp);
    final targetKey = dateKeyOverride ?? todayKey;
    if (targetKey != todayKey) {
      return false;
    }
    final trimmed = text.trim();
    final safeText = trimmed.length > maxLength
        ? trimmed.substring(0, maxLength)
        : trimmed;
    final entry = JournalEntry(
      dateKey: todayKey,
      text: safeText,
      emotionLabel: emotionLabel,
    );
    final storage = prefs ?? await SharedPreferences.getInstance();
    final existing = await loadEntries(prefs: storage);
    final updated = [
      entry,
      ...existing.where((item) => item.dateKey != todayKey),
    ];
    final trimmedList = updated.take(maxEntries).toList();
    await storage.setString(storageKey, jsonEncode(_encode(trimmedList)));
    return true;
  }

  static Future<void> deleteEntry(
    String dateKey, {
    SharedPreferences? prefs,
  }) async {
    final storage = prefs ?? await SharedPreferences.getInstance();
    final existing = await loadEntries(prefs: storage);
    final updated = existing.where((item) => item.dateKey != dateKey).toList();
    await storage.setString(storageKey, jsonEncode(_encode(updated)));
  }

  static List<Map<String, dynamic>> _encode(List<JournalEntry> entries) {
    return entries.map((entry) => entry.toJson()).toList();
  }

  static String _dateKey(DateTime value) {
    final utc = value.toUtc();
    return '${utc.year.toString().padLeft(4, '0')}-'
        '${utc.month.toString().padLeft(2, '0')}-'
        '${utc.day.toString().padLeft(2, '0')}';
  }
}
