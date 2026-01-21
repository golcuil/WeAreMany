import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/models.dart';
import '../crisis/crisis_screen.dart';
import 'mood_controller.dart';

class MoodEntryScreen extends ConsumerStatefulWidget {
  const MoodEntryScreen({super.key});

  static const routeName = '/mood';

  @override
  ConsumerState<MoodEntryScreen> createState() => _MoodEntryScreenState();
}

class _MoodEntryScreenState extends ConsumerState<MoodEntryScreen> {
  final _textController = TextEditingController();
  String _valence = 'neutral';
  String _intensity = 'low';

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final controller = ref.read(moodControllerProvider.notifier);
    final response = await controller.submitMood(
      MoodRequest(
        valence: _valence,
        intensity: _intensity,
        freeText: _textController.text,
      ),
    );
    _textController.clear();
    if (response.crisisAction == 'show_resources' && mounted) {
      Navigator.of(context).pushNamed(CrisisScreen.routeName);
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(moodControllerProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Mood Entry')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          DropdownButtonFormField<String>(
            initialValue: _valence,
            items: const [
              DropdownMenuItem(value: 'positive', child: Text('Positive')),
              DropdownMenuItem(value: 'neutral', child: Text('Neutral')),
              DropdownMenuItem(value: 'negative', child: Text('Negative')),
            ],
            onChanged: (value) => setState(() => _valence = value ?? _valence),
            decoration: const InputDecoration(labelText: 'Valence'),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: _intensity,
            items: const [
              DropdownMenuItem(value: 'low', child: Text('Low')),
              DropdownMenuItem(value: 'medium', child: Text('Medium')),
              DropdownMenuItem(value: 'high', child: Text('High')),
            ],
            onChanged: (value) =>
                setState(() => _intensity = value ?? _intensity),
            decoration: const InputDecoration(labelText: 'Intensity'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _textController,
            maxLines: 4,
            maxLength: 1000,
            decoration: const InputDecoration(
              labelText: 'Optional text',
              alignLabelWithHint: true,
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: state.isLoading ? null : _submit,
            child: const Text('Submit mood'),
          ),
          const SizedBox(height: 16),
          if (state.response != null &&
              state.response!.crisisAction != 'show_resources') ...[
            const SizedBox(height: 12),
            Text(
              state.response!.status == 'ok'
                  ? 'Mood submitted.'
                  : 'Submission blocked.',
            ),
            Text('Sanitized: ${state.response!.sanitizedText ?? '-'}'),
            Text('Identity leak: ${state.response!.identityLeak}'),
            Text('Leak types: ${state.response!.leakTypes.length}'),
            Text('Re-id risk: ${state.response!.reidRisk.toStringAsFixed(2)}'),
            Text('Risk level: ${state.response!.riskLevel}'),
          ],
          if (state.error != null) ...[
            const SizedBox(height: 12),
            Text(state.error!, style: const TextStyle(color: Colors.red)),
          ],
        ],
      ),
    );
  }
}
