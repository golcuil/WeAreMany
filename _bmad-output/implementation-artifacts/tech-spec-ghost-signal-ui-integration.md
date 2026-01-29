---
title: 'Ghost Signal UI Integration'
slug: 'ghost-signal-ui-integration'
created: '2026-01-29'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Flutter', 'Riverpod']
files_to_modify: [
  'lib/app/main_tabs.dart',
  'lib/features/inbox/inbox_controller.dart',
  'lib/features/inbox/inbox_screen.dart',
  'lib/core/network/models.dart',
  'lib/core/network/api_client.dart',
  'lib/app/app.dart',
  'lib/features/profile/about_safety_screen.dart',
  'lib/core/utils/time_utils.dart (new)',
  'lib/core/theme/app_colors.dart (new)',
  'test/inbox_widget_test.dart'
]
code_patterns: [
  'Riverpod StateNotifier + provider',
  'IndexedStack + BottomNavigationBar in MainTabs',
  'Inbox UI formatting in InboxScreen',
  'ApiClient fetchInbox uses models.dart mapping',
  'Widget tests use FakeInboxApiClient'
]
test_patterns: [
  'Widget tests (test/inbox_widget_test.dart)',
  'Provider override with FakeInboxApiClient',
  'Timestamp formatting assertions'
]
---

# Tech-Spec: Ghost Signal UI Integration

**Created:** 2026-01-29

## Overview

### Problem Statement

We need a calm, non-intrusive UI that surfaces asynchronous “Ghost Signal” messages without badges or addictive affordances, while keeping inbox content anonymized and timestamps coarsened.

### Solution

Add a Riverpod-driven inbox polling cadence, a soft “Ghost Glow” animation on the Messages tab icon for unread signals, and a privacy-safe inbox list/reading view that emphasizes themes and time windows over exact timestamps.

### Scope

**In Scope:**
- Inbox polling provider (2‑minute interval) for new messages.
- Ghost Glow animation on the Messages tab icon (soft pulse, no badges).
- Anonymized inbox list showing Theme/Emotion and time windows (coarsened).
- Simple reading view for supportive messages.

**Out of Scope:**
- Badges, “new” labels, or attention-grabbing notifications.
- Real-time presence (typing/online indicators).

## Context for Development

### Codebase Patterns

- Flutter + Riverpod (StateNotifier) for inbox state (`InboxController`).
- Bottom navigation is an `IndexedStack` in `MainTabs`.
- Inbox UI formatting and read state lives in `InboxScreen`.
- No polling or app lifecycle handling exists yet.
- About/Safety tab already uses `CrisisSupportContent` for safety copy.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `lib/app/main_tabs.dart` | Bottom nav; Messages icon slot for glow |
| `lib/features/inbox/inbox_controller.dart` | Inbox load/refresh + read/ack |
| `lib/features/inbox/inbox_screen.dart` | Inbox list UI + timestamp formatting |
| `lib/core/network/models.dart` | Inbox item model fields (add theme/emotion) |
| `lib/core/network/api_client.dart` | Inbox fetch call |
| `lib/app/app.dart` | Theme seed; add AppColors |
| `lib/features/profile/about_safety_screen.dart` | Safety palette/copy consistency |
| `test/inbox_widget_test.dart` | Inbox widget tests |

### Technical Decisions

- Polling should be low-frequency (2 minutes) and safe; no push or realtime.
- Polling must pause when app is backgrounded and resume on foreground.
- Glow should be subtle and performance‑safe; avoid heavy animations.
- Use a dedicated AppColors.ghostSignal (soft mint/amber).
- Timestamp display should remain coarsened to time windows (no exact times).
*** End Patch code

## Implementation Plan

### Tasks

- [ ] Task 1: Add ghost signal palette and glow widget
  - File: `lib/core/theme/app_colors.dart` (new)
  - Action: Define `AppColors.ghostSignal` (soft mint/amber) and any needed helper constants
  - Notes: Keep colors soothing; avoid primary/alert hues
- [ ] Task 2: Add TimeUtils for coarsened time windows
  - File: `lib/core/utils/time_utils.dart` (new)
  - Action: Implement `formatSignalWindow(DateTime nowUtc, DateTime receivedAtUtc)` using buckets:
    - Today: `Midnight`, `Morning`, `Afternoon`, `Evening`
    - Yesterday: `Yesterday`
    - Older: `Earlier this week` (<= 7 days), otherwise `Earlier`
  - Notes: Never expose exact time or date in UI string
- [ ] Task 3: Extend InboxItem model for theme/emotion
  - File: `lib/core/network/models.dart`
  - Action: Add `themeTags` (List<String>) and `emotion` (String?) to `InboxItem`
  - Notes: Map from `theme_tags` and `emotion` JSON fields directly; no derivation from text
- [ ] Task 4: Lifecycle-aware polling in InboxController
  - File: `lib/features/inbox/inbox_controller.dart`
  - Action: Add periodic polling (2 min) with pause/resume using `WidgetsBindingObserver`
  - Notes: Stop timer on `AppLifecycleState.paused`, resume and immediately fetch on `resumed`
- [ ] Task 5: Ghost Glow animation on Messages tab icon
  - File: `lib/app/main_tabs.dart`
  - Action: Wrap Messages icon in a Glow widget using `AnimationController` and opacity tween (0.2 → 0.7)
  - Notes: 2000–3000ms pulse; no badges; glow only when unread messages exist
- [ ] Task 6: Focused reading modal
  - File: `lib/features/inbox/inbox_screen.dart`
  - Action: On message tap, open a focused modal (e.g., `showModalBottomSheet`) with supportive text only
  - Notes: Hide main nav, reduce UI noise, mark read on open
- [ ] Task 7: Update inbox list UI with anonymized labels
  - File: `lib/features/inbox/inbox_screen.dart`
  - Action: Show theme/emotion labels and time windows via `TimeUtils`
  - Notes: Keep text calm and non-identifying
- [ ] Task 8: Update widget tests
  - File: `test/inbox_widget_test.dart`
  - Action: Add tests for glow trigger, time window labels, and reading modal
  - Notes: Use FakeInboxApiClient with theme/emotion fields

### Acceptance Criteria

- [ ] AC1: Given unread messages exist, when the Messages tab is visible, then the icon shows a gentle pulse (opacity 0.2–0.7, ~2–3s).
- [ ] AC2: Given the app is backgrounded, when AppLifecycleState becomes paused, then inbox polling stops.
- [ ] AC3: Given the app resumes, when AppLifecycleState becomes resumed, then an immediate fetch occurs.
- [ ] AC4: Given a message is received today, when rendered in Inbox, then a time window label (Midnight/Morning/Afternoon/Evening) is shown instead of exact time.
- [ ] AC5: Given a message from yesterday, when rendered, then label reads “Yesterday.”
- [ ] AC6: Given a message older than 1 day but within 7, when rendered, then label reads “Earlier this week.”
- [ ] AC7: Given a message tile is tapped, when the modal opens, then the nav is hidden and the message is shown in a focused reading view.
- [ ] AC8: Given theme_tags/emotion are present, when rendered, then those labels appear without derivation from text.

## Additional Context

### Dependencies

- T‑107 Ghost Signal backend delivery (already merged).
- Backend must include `theme_tags` and `emotion` in `/inbox` items.

### Testing Strategy

- Widget tests for glow trigger and modal presentation.
- Widget tests for time window labels.
- Widget test for lifecycle polling pause/resume (simulate lifecycle state changes).

### Notes

- Maintain non‑addictive UX (no badges, no urgency copy).
- `--json`/logging rules unchanged; no PII in UI labels.
