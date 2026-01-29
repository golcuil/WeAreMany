---
title: 'Crisis Screen + risk_level==2 hard block'
slug: 'crisis-screen-risk-level-2-hard-block'
created: '2026-01-29T14:24:08Z'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Flutter', 'Riverpod', 'FastAPI', 'Postgres']
files_to_modify: ['backend/app/main.py', 'backend/app/matching.py', 'backend/app/repository.py', 'backend/app/hold_reasons.py', 'backend/tests/test_mood_crisis.py', 'backend/tests/test_end_to_end.py', 'backend/tests/test_matching.py', 'backend/tests/test_moderation.py', 'backend/tests/test_inbox_crisis.py', 'lib/features/crisis/crisis_screen.dart', 'lib/features/crisis/crisis_support_content.dart', 'lib/features/profile/about_safety_screen.dart', 'lib/features/mood/mood_entry_screen.dart', 'lib/core/network/models.dart', 'lib/core/network/api_client.dart', 'lib/app/app.dart', 'test/']
code_patterns: ['FastAPI dependency injection + Pydantic models', 'Repository pattern with Postgres/InMemory implementations', 'Riverpod StateNotifier controllers', 'Navigator routing via routeName constants', 'Single-line, tokenized logging policies']
test_patterns: ['pytest + FastAPI TestClient', 'InMemoryRepository for backend tests', 'Flutter widget tests in test/', 'No raw text in logs assertions']
---

# Tech-Spec: Crisis Screen + risk_level==2 hard block

**Created:** 2026-01-29T14:24:08Z

## Overview

### Problem Statement

Crisis handling must be enforced end-to-end: if any response signals risk_level==2 or crisis_action=="show_crisis_screen", the client must route to the Crisis Screen and the server must hard-block peer messaging and ensure free_text is never persisted, queued, or logged.

### Solution

Define a single crisis trigger contract (risk_level==2 or crisis_action token), enforce hard-blocking and no-persist guarantees server-side across /mood, /messages, /inbox, and route immediately to Crisis Screen in Flutter; reuse Crisis Screen content verbatim in About/Safety per Navigation 1.1 and Bible 14.1; add tests and gates.

### Scope

**In Scope:**
- Crisis trigger SSOT (risk_level==2 or crisis_action)
- Server hard-block + no-persist guarantees
- Crisis Screen UI + About/Safety resources (verbatim reuse)
- Routing guard across mood/messages/resume
- Tests and gates

**Out of Scope:**
- Feed/chat/profiles/streaks/social graph
- Region-specific hotline localization
- Any new social features

## Context for Development

### Codebase Patterns

- Backend crisis handling in FastAPI endpoints (`backend/app/main.py`) with repo dependency injection and event emission.
- Matching crisis decision in `backend/app/matching.py` returns crisis_action token.
- Persistence paths in `backend/app/repository.py` with InMemory/Postgres parity.
- Frontend uses Riverpod StateNotifier controllers; routing via `Navigator.pushNamed` and routeName constants.
- Existing crisis UI at `lib/features/crisis/crisis_screen.dart` and About/Safety surface at `lib/features/profile/about_safety_screen.dart`.
- Crisis action tokens are inconsistent (`show_resources` vs `show_crisis`) and must be standardized to `show_crisis_screen`.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| backend/app/main.py | API handlers, crisis action tokens, response shaping |
| backend/app/matching.py | risk_level==2 gating + crisis_action |
| backend/app/repository.py | persistence paths + crisis window state |
| backend/app/hold_reasons.py | hold reason constants (crisis) |
| backend/tests/test_mood_crisis.py | no-persist + crisis_action tests (mood) |
| backend/tests/test_end_to_end.py | message crisis block + no-persist |
| backend/tests/test_matching.py | match simulate crisis action |
| lib/features/crisis/crisis_screen.dart | Crisis UI content (reuse verbatim) |
| lib/features/profile/about_safety_screen.dart | About/Safety tab content |
| lib/features/mood/mood_entry_screen.dart | mood flow routing on crisis |
| lib/core/network/models.dart | risk_level + crisis_action mapping |
| lib/core/network/api_client.dart | response parsing + future hook for crisis guard |
| lib/app/app.dart | app routes (crisis screen) |

### Technical Decisions

- Standardize crisis_action token to `show_crisis_screen` across backend + frontend.
- Treat SSOT trigger as: risk_level==2 OR crisis_action==show_crisis_screen.
- Reuse Crisis Screen copy verbatim in About/Safety.
- Server-side enforcement is the source of truth; client routes immediately on trigger.
- Back navigation must not allow bypassing Crisis Screen (route replacement + back disabled).
- No-persist hard gate lives at repository boundary (rejects text writes when risk_level==2).

## Implementation Plan

### Tasks

- [ ] Task 1: Standardize crisis_action SSOT token
  - File: `backend/app/main.py`
  - Action: Replace `show_resources`/`show_crisis` with `show_crisis_screen` for risk_level==2 responses.
  - Notes: Update response fields for /mood, /messages, /second_touch/send as applicable.

- [ ] Task 2: Enforce server-side hard-block + no-persist for risk_level==2
  - File: `backend/app/main.py`
  - Action: Ensure /mood, /messages, /inbox return blocked/safe responses when crisis trigger applies; do not enqueue or create inbox items.
  - Notes: Preserve existing crisis window logic; add inbox crisis guard via `repo.is_in_crisis_window` if needed.

- [ ] Task 3: Add repository-level no-persist hard gate
  - File: `backend/app/repository.py`
  - Action: Guard any message/mood persistence that could include text; if risk_level==2, skip and/or raise a safe exception that upstream handles.
  - Notes: Apply to both Postgres and InMemory; ensure no DB write or queue payload contains text.

- [ ] Task 4: Ensure no-log guarantee for risk_level==2
  - File: `backend/app/main.py`
  - Action: Confirm request logging middleware never logs request bodies; add tokenized `crisis_enforced` log line only.

- [ ] Task 5: Update frontend crisis routing guard
  - File: `lib/core/network/models.dart`
  - Action: Add helper (e.g., `isCrisisTrigger`) to centralize SSOT check.
  - File: `lib/features/mood/mood_entry_screen.dart`
  - Action: Route immediately to Crisis Screen using `pushNamedAndRemoveUntil` when trigger detected.
  - Notes: Block back navigation; prevent bypass via back button.

- [ ] Task 6: Reuse Crisis Screen content in About/Safety
  - File: `lib/features/crisis/crisis_support_content.dart` (new)
  - Action: Extract Crisis Screen body content into reusable widget.
  - File: `lib/features/crisis/crisis_screen.dart`
  - Action: Use shared content + disable back via `WillPopScope`.
  - File: `lib/features/profile/about_safety_screen.dart`
  - Action: Render the shared content verbatim; keep anonymity copy.

- [ ] Task 7: Update tests for standardized token and hard-block
  - File: `backend/tests/test_mood_crisis.py`
  - Action: Expect `crisis_action == show_crisis_screen`; assert no persistence.
  - File: `backend/tests/test_end_to_end.py`
  - Action: Expect show_crisis_screen; no messages/inbox persisted.
  - File: `backend/tests/test_matching.py`
  - Action: Expect show_crisis_screen in simulate.
  - File: `backend/tests/test_inbox_crisis.py` (new)
  - Action: In crisis window, /inbox returns empty/safe response.

- [ ] Task 8: Add frontend widget tests
  - File: `test/crisis_routing_test.dart`
  - Action: Crisis trigger routes to Crisis Screen and back is disabled.
  - File: `test/about_safety_test.dart`
  - Action: About/Safety renders crisis content verbatim.

### Acceptance Criteria

- [ ] AC 1: Given a response with risk_level==2, when the client receives it, then it immediately routes to Crisis Screen and disables back navigation.
- [ ] AC 2: Given a response with crisis_action=="show_crisis_screen", when the client receives it, then it routes to Crisis Screen (even if risk_level is absent).
- [ ] AC 3: Given risk_level==2 on /mood, when the request is processed, then repository-level no-persist gate prevents any text persistence and response status is blocked.
- [ ] AC 4: Given risk_level==2 on /messages, when the request is processed, then no message or inbox item is persisted/queued and response status is blocked.
- [ ] AC 5: Given a user in crisis window, when /inbox is fetched, then the response contains no peer messages (safe empty list or tokenized blocked response).
- [ ] AC 6: Given crisis trigger, when logging occurs, then no raw text is logged and only tokenized crisis_enforced entries appear.
- [ ] AC 7: Given About/Safety tab, when rendered, then it displays the Crisis Screen content verbatim with anonymity guarantees.

## Additional Context

### Dependencies

- T-002, T-003

### Testing Strategy

- Backend unit tests for repository no-persist gate and hard-block paths.
- Integration tests for /mood, /messages, /inbox crisis behavior.
- Frontend widget tests for routing guard and About/Safety rendering.
- Gates: policy_check, docs_consistency_check, pytest, dart analyze, flutter test, secret_echo_guard.

### Notes

- Keep copy non-alarmist per Bible 14.1.
- Avoid localization in this slice.
- Back navigation must not allow bypass of Crisis Screen.
