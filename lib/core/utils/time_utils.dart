class TimeUtils {
  static String formatSignalWindow({
    required DateTime nowUtc,
    required DateTime receivedAtUtc,
  }) {
    final nowDay = DateTime.utc(nowUtc.year, nowUtc.month, nowUtc.day);
    final receivedDay = DateTime.utc(
      receivedAtUtc.year,
      receivedAtUtc.month,
      receivedAtUtc.day,
    );
    final diffDays = nowDay.difference(receivedDay).inDays;
    if (diffDays == 0) {
      return _todayWindow(receivedAtUtc);
    }
    if (diffDays == 1) {
      return 'Yesterday';
    }
    if (diffDays <= 7) {
      return 'Earlier this week';
    }
    return 'Earlier';
  }

  static String _todayWindow(DateTime receivedAtUtc) {
    final hour = receivedAtUtc.hour;
    if (hour < 6) {
      return 'Midnight';
    }
    if (hour < 12) {
      return 'Morning';
    }
    if (hour < 18) {
      return 'Afternoon';
    }
    return 'Evening';
  }
}
