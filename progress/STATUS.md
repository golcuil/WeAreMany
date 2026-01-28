# Status

V1 Complete: Operational readiness, tooling, and documentation are complete for launch.

## Current iteration goal
- V1 sign-off bundle and doc alignment complete.

## Done
- [T-096] Canary drill rehearsal: HOLD-first semantics with manual workflow and summary artifact.
- [T-095] Baseline ops discipline: latest pointer is sole source of truth; validation enforces schema; retention-days explicit.
- [T-094] Regression baseline lifecycle: deterministic baseline + latest pointer, runtime schema allowlist, HOLD semantics for not_configured/insufficient_data.
- [T-093] Staged rollout canary gate: thin wrapper over existing contracts with regression as primary signal.
- [T-092] V1 completion sweep: docs aligned, canonical bundle added, and status/tasks finalized.
- [T-091] Launch readiness: launch checklist + go/no-go decision record template with docs consistency gating.
- [T-090] Release discipline v1: manual pre_release_gate workflow + versioned release/rollback checklist.
- [T-089] Secret echo guard + logging policy: CI scans captured logs for unmasked secrets; outputs remain single-line and privacy-safe.
- [T-088] prod_rehearsal CI gate: bootstrap → verify → restore → verify → ops smoke with safe summary artifact.
- [T-087] DR playbook + restore_dry_run CI gate (sanitized fixture, strict dsn-env, privacy-safe outputs).
- [T-086] Retention enforcement: TTL cleanup + aggregate-only retention_report with ttl_drift detection.
- [T-083] Ops metrics snapshot + regression gate (ops_metrics_snapshot + metrics_regression_check with MIN_N guardrail).
- [T-082] Operator runbook v1 + docs consistency gate (canonical ops guide + CI check).
- [T-081] DB migrations integration CI gate: apply + verify against ephemeral Postgres with idempotency check.
- [T-080] Prod config contract: cron ops fail-fast on missing env names (names-only), PR runs remain CI-safe.
- [T-079] ops_daily de-noise: insufficient_data token + scheduled-run normalization helper (exit-2 normalized only with token).
- [T-078] Production bootstrap dry-run + operator checklist (db_bootstrap --dry-run migration plan validation; db_verify not_configured; CI dry-run job).
- [T-077] Security scanning + threat model: pip-audit dependency scan + gitleaks secrets scan (CLI); threat model in docs/threat_model.md; dependency remediation for Starlette advisories.
- [T-076] Second-touch recompute full: minimal event logging (day/type/reason/created_at only), full recompute from events, and cleanup tooling.
- [T-075] Recompute second_touch aggregates: operator-driven tool for last N days (max 30); partial recompute flagged when source events are missing.
- [T-074] Ops playbook + prod_verify: deploy/rollback/incident triage checklist; manual prod_verify workflow with non-sensitive output and skip when prod not configured.
- [T-073] ops_daily strict failure alerting: GitHub Issue dedupe + optional Slack on strict failures; aggregate-only outputs.
- [T-072] DB bootstrap workflow + tool: manual workflow_dispatch with dry_run; apply_migrations + db_verify sequence; README bootstrap steps documented.
- [T-071] Prod wiring runbook + db_verify: documented secret-only config, non-sensitive verification steps, deterministic reason codes.
- [T-070] Second-touch aggregates retention cleanup: 180d retention constant; cleanup CLI + ops_daily subcommand; tests added.
- [T-069] ops_daily strict prod enablement: scheduled runs strict when prod secret present; smoke otherwise; README enablement docs added.
- [T-068] Second-touch health thresholds: hold/suppression + identity-leak high-signal checks with insufficient_data gate; ops_daily subcommand + included in all.
- [T-067] Second-touch aggregate metrics: daily counters for offers/suppression/sends/holds/disable; ops_daily prints 7d/30d summaries; migration + CI step added.
- [T-066] Second-touch offer gating parity: offer generation now enforces cap/cooldown/disabled/permanent/crisis guardrails; offer suppression tests added.
- [T-065] ops_daily schedule hardened: smoke when prod secrets missing; strict when configured.
- [T-064] Second-touch guardrails: one-shot enforced; monthly cap (rate_limited); per-pair cooldown (cooldown_active); negative-ack disable window; identity-leak permanent disable; crisis gating unchanged.
- [T-063] Inbox UI support for second-touch offer (render + one-shot send) — Inbox renders second_touch_offer + one-shot send flow; tests green.
- [T-062] Second-touch prompt (Frequent Positive Encounters) v1 in Inbox — fixed offer materialization; CI green.
- [T-060] Scheduled ops_daily GitHub Actions workflow (privacy-safe)
- [T-061] Fix ops_daily workflow deps (install PyYAML + backend requirements)
- [T-059] Unified ops runner (metrics + watchdog + tuning)
- [T-058] Matching Health watchdog CLI (exit-code alerting)
- [T-057] Daily privacy-safe acknowledgement aggregates for monitoring (counts only)
- [T-056] Deterministic candidate sampling (seeded) with parity across stores
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
- [T-040] Add privacy-safe security event logging for identity leak and throttle events
- [T-041] Deterministic shadow throttle window semantics (TTL reset) with tests
- [T-042] Canonicalize hold_reason taxonomy and update usages/tests
- [T-043] Add retention (prune) for security_events with tests
- [T-044] Canonicalize security_events event_type taxonomy and update usages/tests
- [T-045] Matching Health (H) feedback loop for auto-tuning matching parameters
- [T-046] Add finite content catalog + deterministic selection (backend)
- [T-047] Cold-start bridge: system inbox message + finite content selection
- [T-048] Standardize inbox item origin (system vs peer) and test invariants
- [T-049] Harden Home finite-content data path (persist + determinism)
- [T-051] Centralize bridge decision logic (crisis/holds > low density > peer)
- [T-050] Deterministic reflective mirror templates (finite + safe)
- [T-052] Ops-safe minimum density K config + unified low-density check
- [T-053] Canonical theme normalization (variants -> canonical IDs)
- [T-054] Affinity learning from acknowledgements (theme-level bias, bounded + decay)
- [T-055] Affinity metrics + guardrails (aggregate-only) and invariants

## In progress
- [T-022] CI format diff visibility (print formatter diff on failure)
- [T-084] Secret rotation checklist + post-rotation validation workflow (manual).
- [T-085] Release checklist + pre-release gate workflow (manual).
- [T-084] Secret rotation checklist + post-rotation validation workflow (manual).

## Next

## Iteration update routine
- Move tasks: BACKLOG -> TODO -> IN_PROGRESS -> REVIEW -> DONE (no skips)
- Keep DONE empty until tests pass and acceptance criteria met
- Add 3-5 new BACKLOG tasks per iteration; keep policy_check passing
- Update Current iteration goal and Next list each iteration

## Risks / Decisions needed
- ...
