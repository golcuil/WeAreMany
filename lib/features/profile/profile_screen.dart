import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/local/mood_history_store.dart';
import '../../core/local/profile_store.dart';
import 'impact_provider.dart';
import 'privacy_screen.dart';
import 'profile_providers.dart';
import 'settings_screen.dart';

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  static const routeName = '/profile';

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  final TextEditingController _nameController = TextEditingController();
  String _displayName = '';
  bool _isEditing = false;
  bool _loading = true;
  int _dashboardDays = 7;

  @override
  void initState() {
    super.initState();
    _loadDisplayName();
    ref.listenManual<int>(displayNameRefreshProvider, (previous, next) {
      _loadDisplayName();
    });
  }

  Future<void> _loadDisplayName() async {
    final stored = await ProfileStore.loadDisplayName();
    if (!mounted) {
      return;
    }
    setState(() {
      _displayName = stored;
      _nameController.text = stored;
      _loading = false;
    });
  }

  Future<void> _saveDisplayName() async {
    final nextName = _nameController.text.trim();
    await ProfileStore.saveDisplayName(nextName);
    if (!mounted) {
      return;
    }
    setState(() {
      _displayName = nextName;
      _isEditing = false;
    });
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final impact = ref.watch(impactCountProvider);
    final historyAsync = ref.watch(moodHistoryEntriesProvider);
    return Scaffold(
      key: const Key('profile_screen'),
      appBar: AppBar(title: const Text('Profile')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Identity (private)',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 12),
          if (_loading)
            const Center(child: CircularProgressIndicator())
          else ...[
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Display Name:'),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _displayName.isEmpty ? 'Not set' : _displayName,
                    key: const Key('profile_display_name'),
                  ),
                ),
                TextButton(
                  onPressed: () => setState(() => _isEditing = !_isEditing),
                  child: Text(_isEditing ? 'Cancel' : 'Edit'),
                ),
              ],
            ),
            if (_isEditing) ...[
              TextField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Display name',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 8),
              Align(
                alignment: Alignment.centerLeft,
                child: ElevatedButton(
                  onPressed: _saveDisplayName,
                  child: const Text('Save'),
                ),
              ),
            ],
          ],
          const SizedBox(height: 16),
          ListTile(
            key: const Key('profile_settings'),
            leading: const Icon(Icons.settings_outlined),
            title: const Text('Settings'),
            subtitle: const Text('Privacy, notifications, About & Safety'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () =>
                Navigator.of(context).pushNamed(SettingsScreen.routeName),
          ),
          const SizedBox(height: 16),
          const Text(
            'Dashboard',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              ChoiceChip(
                key: const Key('dashboard_toggle_7'),
                label: const Text('7 days'),
                selected: _dashboardDays == 7,
                onSelected: (_) => setState(() => _dashboardDays = 7),
              ),
              const SizedBox(width: 8),
              ChoiceChip(
                key: const Key('dashboard_toggle_30'),
                label: const Text('30 days'),
                selected: _dashboardDays == 30,
                onSelected: (_) => setState(() => _dashboardDays = 30),
              ),
            ],
          ),
          const SizedBox(height: 12),
          historyAsync.when(
            data: (entries) =>
                _DashboardSummary(entries: entries, days: _dashboardDays),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, stackTrace) =>
                const Text('Unable to load mood history.'),
          ),
          const SizedBox(height: 12),
          impact.when(
            data: (count) => Text('Your messages helped $count people'),
            loading: () => const Text('Your messages helped — people'),
            error: (error, stackTrace) =>
                const Text('Your messages helped — people'),
          ),
          const SizedBox(height: 16),
          Align(
            alignment: Alignment.centerLeft,
            child: TextButton(
              key: const Key('profile_privacy'),
              onPressed: () =>
                  Navigator.of(context).pushNamed(PrivacyScreen.routeName),
              child: const Text('Privacy'),
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Profile summary',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          const Text(
            'A private space to keep your identity and preferences organized.',
          ),
          const SizedBox(height: 16),
          const Text(
            'This profile is private and not visible to others.',
            style: TextStyle(color: Colors.black54),
          ),
        ],
      ),
    );
  }
}

class _DashboardSummary extends StatelessWidget {
  const _DashboardSummary({required this.entries, required this.days});

  final List<MoodHistoryEntry> entries;
  final int days;

  @override
  Widget build(BuildContext context) {
    final snapshot = MoodHistoryStore.computeSnapshot(entries, days);
    final counts = snapshot.countsByEmotion.entries.toList()
      ..sort((a, b) => a.key.compareTo(b.key));
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'You marked your mood ${snapshot.frequency} times (last $days days)',
        ),
        const SizedBox(height: 4),
        Text(
          'Your mood changed on ${snapshot.volatilityDays} days (last $days days)',
        ),
        const SizedBox(height: 12),
        const Text(
          'Mood history (day-level)',
          style: TextStyle(fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 8),
        if (snapshot.timeline.isEmpty)
          const Text('No mood history yet.')
        else
          Column(
            children: snapshot.timeline
                .map(
                  (day) => Row(
                    children: [
                      Text(day.dateKey),
                      const SizedBox(width: 8),
                      Text(day.emotionLabel),
                    ],
                  ),
                )
                .toList(),
          ),
        const SizedBox(height: 12),
        const Text(
          'Counts by emotion',
          style: TextStyle(fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 8),
        if (counts.isEmpty)
          const Text('No entries yet.')
        else
          Column(
            children: counts
                .map((entry) => Text('${entry.key}: ${entry.value}'))
                .toList(),
          ),
      ],
    );
  }
}
