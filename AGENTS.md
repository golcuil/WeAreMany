# AGENTS.md — Project operating rules for Codex + Team

## Primary commands (Flutter)
- Install deps: flutter pub get
- Format: dart format .
- Analyze: dart analyze
- Tests: flutter test

## Workflow
- Work in small slices.
- All work must be tracked in /tasks/tasks.yaml.
- Task state must follow: BACKLOG -> TODO -> IN_PROGRESS -> REVIEW -> DONE
- Do not mark DONE unless tests pass and acceptance criteria are met.

## Product guardrails (hard blocks)
- Do not add: feed, chat threads, profiles, streaks, social graph.
- Do not expose sender identity in UI or API.
- If risk_level == 2: block peer messaging and do not persist free text.

## Engineering constraints
- Flutter + Riverpod.
- Keep business logic out of Widgets; use use-cases/services.
- No raw message text in logs/analytics.

## Definition of Done (minimum)
- flutter test passes
- dart analyze passes
- No red-line violations introduced
- Progress files updated: /progress/STATUS.md and (if needed) DECISIONS/RISKS/RELEASE_NOTES
