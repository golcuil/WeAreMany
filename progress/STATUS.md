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
- [T-021] Coarsen inbox timestamps to day-level UTC to reduce correlation risk
- [T-023] Keep Dart format gate strict while printing git status+diff on mismatch
- [T-024] Enforce one-shot acknowledgements via idempotent repository writes (already_recorded on duplicates)
- [T-025] Ship Profile MVP (private identity) with Settings entry; keep About & Safety as last item in Settings; stabilize Reflection widget test
- [T-026] Profile dashboard: local mood history (7/30) with frequency + volatility at day-level (UTC), private-only
- [T-027] Profile dashboard: private impact counter via /impact (distinct recipients for positive acknowledgements)
- [T-028] Add Privacy Controls screen (truthful copy + local clear/reset controls) linked from Settings/Profile
- [T-029] Reflection: local-only journal with day-lock (edit today only), 7/30 list, prompts, tests
- [T-030] Backend matching: Progressive Delivery v1 driven by acknowledgement health (H)
- [T-031] Backend matching: affinity learning v1 (theme scores from positive acks) biases candidate ordering
- [T-032] Backend: canonical theme normalization + stored message theme_tags wired through matching and affinity
- [T-033] Cold start bridge: system-origin inbox message on low density + Home “Helpful Series” finite content card
- [T-034] Home: k-anon similar_count insight (shown only when >=K) via /mood optional field
- [T-035] Backend: crisis-aware delivery gate + inbox shielding (system-only during crisis window)
- [T-036] Inbox lifecycle: unread (local), responded, locked-after-7d + day-level relative timestamps
- [T-037] Stabilize inbox lifecycle tests with fixed UTC now injection
- [T-038] Harden identity-leak detection (PII) in moderation with tests
- [T-039] Add identity leak shadow throttling (hold on repeated PII attempts)

## In progress
- [T-022] CI format diff visibility (print formatter diff on failure)
- [T-040] Add privacy-safe security event logging for identity leak and throttle events

## Next

## Iteration update routine
- Move tasks: BACKLOG -> TODO -> IN_PROGRESS -> REVIEW -> DONE (no skips)
- Keep DONE empty until tests pass and acceptance criteria met
- Add 3-5 new BACKLOG tasks per iteration; keep policy_check passing
- Update Current iteration goal and Next list each iteration

## Risks / Decisions needed
- ...
