import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

class MoodHistoryEntry {
  MoodHistoryEntry({
    required this.dateKey,
    required this.emotionLabel,
    required this.valence,
    required this.intensity,
  });

  final String dateKey;
  final String emotionLabel;
  final String valence;
  final String intensity;

  Map<String, dynamic> toJson() {
    return {
      'date_key': dateKey,
      'emotion_label': emotionLabel,
      'valence': valence,
      'intensity': intensity,
    };
  }

  factory MoodHistoryEntry.fromJson(Map<String, dynamic> json) {
    return MoodHistoryEntry(
      dateKey: json['date_key'] as String? ?? '',
      emotionLabel: json['emotion_label'] as String? ?? '',
      valence: json['valence'] as String? ?? '',
      intensity: json['intensity'] as String? ?? '',
    );
  }
}

class MoodHistoryDay {
  MoodHistoryDay({required this.dateKey, required this.emotionLabel});

  final String dateKey;
  final String emotionLabel;
}

class MoodHistorySnapshot {
  MoodHistorySnapshot({
    required this.days,
    required this.frequency,
    required this.volatilityDays,
    required this.countsByEmotion,
    required this.timeline,
  });

  final int days;
  final int frequency;
  final int volatilityDays;
  final Map<String, int> countsByEmotion;
  final List<MoodHistoryDay> timeline;
}

class MoodHistoryStore {
  static const storageKey = 'mood_history_v1';
  static const maxEntries = 60;

  static Future<void> recordEntry({
    required String emotionLabel,
    required String valence,
    required String intensity,
    DateTime? now,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final existing = await loadEntries(prefs: prefs);
    final timestamp = now ?? DateTime.now().toUtc();
    final entry = MoodHistoryEntry(
      dateKey: _dateKey(timestamp),
      emotionLabel: emotionLabel,
      valence: valence,
      intensity: intensity,
    );
    final updated = [
      entry,
      ...existing.where((item) => item.dateKey != entry.dateKey),
    ];
    final trimmed = updated.take(maxEntries).toList();
    await prefs.setString(storageKey, jsonEncode(_encode(trimmed)));
  }

  static Future<List<MoodHistoryEntry>> loadEntries({
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
        .map(MoodHistoryEntry.fromJson)
        .toList();
  }

  static MoodHistorySnapshot computeSnapshot(
    List<MoodHistoryEntry> entries,
    int days, {
    DateTime? now,
  }) {
    final anchor = (now ?? DateTime.now().toUtc());
    final start = DateTime.utc(
      anchor.year,
      anchor.month,
      anchor.day,
    ).subtract(Duration(days: days - 1));
    final filtered = entries.where((entry) {
      final parsed = _parseDate(entry.dateKey);
      if (parsed == null) {
        return false;
      }
      return !parsed.isBefore(start) && !parsed.isAfter(anchor);
    }).toList();

    final counts = <String, int>{};
    for (final entry in filtered) {
      counts.update(entry.emotionLabel, (value) => value + 1, ifAbsent: () => 1);
    }

    final dayMap = <String, MoodHistoryEntry>{};
    for (final entry in filtered) {
      dayMap[entry.dateKey] = entry;
    }
    final orderedDays = dayMap.keys.toList()..sort();
    final timeline = orderedDays
        .map(
          (dateKey) => MoodHistoryDay(
            dateKey: dateKey,
            emotionLabel: dayMap[dateKey]?.emotionLabel ?? '',
          ),
        )
        .toList();

    var volatility = 0;
    String? previous;
    for (final day in timeline) {
      if (previous != null && day.emotionLabel != previous) {
        volatility += 1;
      }
      previous = day.emotionLabel;
    }

    return MoodHistorySnapshot(
      days: days,
      frequency: filtered.length,
      volatilityDays: volatility,
      countsByEmotion: counts,
      timeline: timeline,
    );
  }

  static List<Map<String, dynamic>> _encode(List<MoodHistoryEntry> entries) {
    return entries.map((entry) => entry.toJson()).toList();
  }

  static String _dateKey(DateTime value) {
    final utc = value.toUtc();
    return '${utc.year.toString().padLeft(4, '0')}-'
        '${utc.month.toString().padLeft(2, '0')}-'
        '${utc.day.toString().padLeft(2, '0')}';
  }

  static DateTime? _parseDate(String dateKey) {
    try {
      return DateTime.parse(dateKey);
    } on FormatException {
      return null;
    }
  }
}
