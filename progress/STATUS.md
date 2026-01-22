# Status

MVP Core Complete: The core end-to-end flow is complete for mood, message delivery, inbox, and acknowledgements.

## Current iteration goal
- Bootstrap MVP workflow and define the first safe, sequential backlog.

## Done
- [T-001] Wire policy_check into CI gate
- [T-002] Define backend API contract skeleton
- [T-003] Create MVP data model and migrations
- [T-004] Implement authn/authz and rate limiting middleware
- [T-005] Build moderation pipeline skeleton
- [T-006] Implement matching gate and sampling skeleton
- [T-007] Define privacy-safe event taxonomy
- [T-008] Build Flutter app skeleton with Riverpod
- [T-009] Implement mood entry flow and crisis UX
- [T-010] Implement inbox UI and acknowledgement flow
- [T-011] Deliver end-to-end happy path
- [T-012] DB-backed eligible recipient pool sampling (theme/intensity buckets)
- [T-014] Dev-safe rate limiting fallback (no Redis required) + stable iOS Simulator run docs
- [T-015] Restore CI green on main (deps + import path + psycopg pin)
- [T-016] CI hygiene cleanup (single source of truth + stable triggers)
- [T-018] Reflection (Tab 3) MVP: Weekly distribution + trend + volatility
- [T-019] 4-tab bottom nav: Home / Messages / Reflection / Settings (About & Safety inside Settings)
- [T-020] Align PRD + UX_SPEC with shipped nav and About & Safety placement

## In progress

## Next

## Iteration update routine
- Move tasks: BACKLOG -> TODO -> IN_PROGRESS -> REVIEW -> DONE (no skips)
- Keep DONE empty until tests pass and acceptance criteria met
- Add 3-5 new BACKLOG tasks per iteration; keep policy_check passing
- Update Current iteration goal and Next list each iteration

## Risks / Decisions needed
- ...
