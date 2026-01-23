import 'package:shared_preferences/shared_preferences.dart';

class ProfileStore {
  static const displayNameKey = 'display_name';

  static Future<String> loadDisplayName({
    SharedPreferences? prefs,
  }) async {
    final storage = prefs ?? await SharedPreferences.getInstance();
    return storage.getString(displayNameKey) ?? '';
  }

  static Future<void> saveDisplayName(
    String name, {
    SharedPreferences? prefs,
  }) async {
    final storage = prefs ?? await SharedPreferences.getInstance();
    await storage.setString(displayNameKey, name);
  }

  static Future<void> clearDisplayName({
    SharedPreferences? prefs,
  }) async {
    final storage = prefs ?? await SharedPreferences.getInstance();
    await storage.remove(displayNameKey);
  }
}
