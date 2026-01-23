import '../core/local/mood_history_store.dart';

class HelpfulCard {
  const HelpfulCard({
    required this.id,
    required this.title,
    required this.bullets,
    required this.why,
    required this.themes,
    required this.intensityBuckets,
  });

  final String id;
  final String title;
  final List<String> bullets;
  final String why;
  final List<String> themes;
  final List<String> intensityBuckets;
}

const helpfulSeriesCards = <HelpfulCard>[
  HelpfulCard(
    id: 'calm_reset',
    title: 'Helpful Series: Small calm reset',
    bullets: [
      'Name one thing you can see, hear, and feel.',
      'Take three slow breaths, longer on the exhale.',
    ],
    why: 'Brief grounding can lower immediate stress signals.',
    themes: ['calm', 'overwhelm'],
    intensityBuckets: ['low', 'medium'],
  ),
  HelpfulCard(
    id: 'anxiety_anchor',
    title: 'Helpful Series: Anxiety anchor',
    bullets: [
      'Place both feet on the floor and notice contact points.',
      'Pick a simple next step you can do in under 5 minutes.',
    ],
    why: 'Anchoring the body can reduce racing thoughts.',
    themes: ['anxiety'],
    intensityBuckets: ['medium', 'high'],
  ),
  HelpfulCard(
    id: 'overwhelm_sort',
    title: 'Helpful Series: Overwhelm sorter',
    bullets: [
      'Write down everything on your mind in a short list.',
      'Circle just one item to address today.',
    ],
    why: 'Reducing the list can make the next step clearer.',
    themes: ['overwhelm', 'work_stress'],
    intensityBuckets: ['high'],
  ),
  HelpfulCard(
    id: 'self_worth_reframe',
    title: 'Helpful Series: Self-worth reframe',
    bullets: [
      'Name one thing you did well this week.',
      'Speak to yourself as you would to a friend.',
    ],
    why: 'Self-kindness can ease harsh inner narratives.',
    themes: ['self_worth'],
    intensityBuckets: ['low', 'medium'],
  ),
  HelpfulCard(
    id: 'loneliness_gentle',
    title: 'Helpful Series: Gentle connection',
    bullets: [
      'Send a simple check-in to someone you trust.',
      'Step outside or open a window for fresh air.',
    ],
    why: 'Small connections can soften isolation.',
    themes: ['loneliness', 'relationship'],
    intensityBuckets: ['low', 'medium'],
  ),
  HelpfulCard(
    id: 'grief_soften',
    title: 'Helpful Series: Grief softener',
    bullets: [
      'Give yourself permission to feel what is present.',
      'Pick one comforting ritual for today.',
    ],
    why: 'Gentle rituals can offer steadiness in grief.',
    themes: ['grief'],
    intensityBuckets: ['medium', 'high'],
  ),
  HelpfulCard(
    id: 'anger_pause',
    title: 'Helpful Series: Anger pause',
    bullets: [
      'Pause before responding and count to five.',
      'Move your body for one minute to release tension.',
    ],
    why: 'A short pause can prevent regretful reactions.',
    themes: ['anger'],
    intensityBuckets: ['medium', 'high'],
  ),
  HelpfulCard(
    id: 'hope_seed',
    title: 'Helpful Series: Hope seed',
    bullets: [
      'Name a small thing you are looking forward to.',
      'List one resource that has helped before.',
    ],
    why: 'Small future anchors can lift mood gently.',
    themes: ['hope', 'motivation'],
    intensityBuckets: ['low', 'medium'],
  ),
  HelpfulCard(
    id: 'motivation_nudge',
    title: 'Helpful Series: Motivation nudge',
    bullets: [
      'Break the task into a 2-minute starter step.',
      'Set a timer and stop when it ends.',
    ],
    why: 'Tiny starts can build momentum without pressure.',
    themes: ['motivation', 'work_stress'],
    intensityBuckets: ['low', 'medium'],
  ),
  HelpfulCard(
    id: 'relationship_boundaries',
    title: 'Helpful Series: Relationship boundaries',
    bullets: [
      'Name one boundary that protects your energy.',
      'Practice a short, respectful phrase to use it.',
    ],
    why: 'Clear boundaries can reduce recurring friction.',
    themes: ['relationship'],
    intensityBuckets: ['medium'],
  ),
  HelpfulCard(
    id: 'work_reset',
    title: 'Helpful Series: Work reset',
    bullets: [
      'Sort tasks into: now, later, delegate.',
      'Block a 15-minute focus window.',
    ],
    why: 'Structured blocks can reduce work stress.',
    themes: ['work_stress', 'overwhelm'],
    intensityBuckets: ['medium', 'high'],
  ),
  HelpfulCard(
    id: 'calm_hold',
    title: 'Helpful Series: Calm hold',
    bullets: [
      'Notice the calm and name where you feel it.',
      'Take a moment to appreciate the quiet.',
    ],
    why: 'Savoring calm can extend it.',
    themes: ['calm'],
    intensityBuckets: ['low'],
  ),
];

HelpfulCard? pickHelpfulCard(List<MoodHistoryEntry> entries) {
  if (entries.isEmpty) {
    return null;
  }
  final sorted = [...entries]..sort((a, b) => a.dateKey.compareTo(b.dateKey));
  final latest = sorted.last;
  final themes = _mapMoodToThemes(latest);
  final intensity = latest.intensity;

  HelpfulCard? best;
  var bestScore = -1;
  for (final card in helpfulSeriesCards) {
    final overlap = themes.where(card.themes.contains).length;
    final intensityMatch = card.intensityBuckets.contains(intensity) ? 1 : 0;
    final score = overlap * 2 + intensityMatch;
    if (score > bestScore) {
      bestScore = score;
      best = card;
    }
  }
  return best ?? helpfulSeriesCards.first;
}

List<String> _mapMoodToThemes(MoodHistoryEntry entry) {
  final emotion = entry.emotionLabel;
  final mapped = _emotionToThemes[emotion];
  if (mapped != null && mapped.isNotEmpty) {
    return mapped;
  }
  return _valenceFallback[entry.valence] ?? const ['calm'];
}

const _emotionToThemes = {
  'calm': ['calm'],
  'content': ['calm'],
  'hopeful': ['hope', 'motivation'],
  'happy': ['hope'],
  'anxious': ['anxiety'],
  'sad': ['grief', 'loneliness'],
  'disappointed': ['self_worth'],
  'angry': ['anger'],
  'overwhelmed': ['overwhelm', 'work_stress'],
  'numb': ['overwhelm', 'loneliness'],
};

const _valenceFallback = {
  'positive': ['hope'],
  'neutral': ['calm'],
  'negative': ['self_worth'],
};
