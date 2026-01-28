# Decisions

## D-001 (2026-01-19) — Backend choice
- Decision: Use FastAPI (Python) with Postgres + Redis for the MVP API.
- Context: Fits the locked stack options and supports fast iteration with clear typing at the contract layer.
- Consequences: Backend scaffolding, tooling, and contracts will target FastAPI + Postgres + Redis.

## D-002 (2026-01-26) — Privacy-first inbox timestamps
- Decision: Coarsen inbox timestamps to day-level UTC in responses and UI.
- Context: Reduce correlation risk from precise timestamps while keeping UX readable.
- Consequences: Day-level labels only (Today/Yesterday/Date), no minute/second precision.

## D-003 (2026-01-26) — Cold-start bridge via system-origin content
- Decision: When anonymity density is insufficient (N < K), deliver a system-origin inbox item and surface finite content.
- Context: Avoid peer delivery in low-density scenarios; provide value without identity exposure.
- Consequences: No peer delivery on low density; system-origin messages use finite templates.

## D-004 (2026-01-26) — Matching optimization via aggregate signals
- Decision: Use aggregate acknowledgement health, affinity weights, and canonical theme tags to bias matching.
- Context: Improve delivery quality without social graphs or identity exposure.
- Consequences: Matching remains privacy-safe; tuning is bounded and applies only to peer delivery.

## D-005 (2026-01-26) — Ops safety tooling as privacy-safe CLIs
- Decision: Add daily aggregates, watchdog, and unified ops runner with aggregate-only outputs.
- Context: Need monitoring without logging identifiers or raw text.
- Consequences: Ops runs are cron/CI-friendly and fail closed on unhealthy signals.

## D-006 (2026-01-26) — Second-touch offer as one-shot system prompt
- Decision: Offer a one-time “second-touch” note as a system-origin inbox card with opaque offer_id.
- Context: Allow deeper support without chat, identity surfaces, or threads.
- Consequences: One-shot enforcement, cooldowns, and strict abuse guardrails.

## D-007 (2026-01-26) — Inbox lifecycle is client-only
- Decision: Unread/read state is client-only; responded and locked states are derived from ack_status and age.
- Context: Avoid server state for read receipts; keep privacy posture strong.
- Consequences: Local read store; backend schema unchanged.

## D-008 (2026-01-26) — Crisis window safety gate
- Decision: Block peer delivery and shield inbox during crisis window; allow system-only content.
- Context: Avoid harm amplification during crisis; keep behavior server-side only.
- Consequences: Crisis window check in matching and inbox eligibility; no client schema changes.

## D-009 (2026-01-26) — Security events are privacy-safe, hashed
- Decision: Log identity leak and throttle events with actor_hash (HMAC) and aggregate-only meta.
- Context: Need observability without identifiers or raw text.
- Consequences: Security events retention and pruning; no raw text stored.

## D-010 (2026-01-26) — Canonical taxonomies are single-source
- Decision: Centralize hold_reason values, security event types, and theme tags in canonical modules.
- Context: Prevent drift across code paths and tests.
- Consequences: Tests enforce uniqueness and naming conventions; reduced analytics ambiguity.

## D-011 (2026-01-26) — Deterministic sampling + seeded ordering
- Decision: Replace nondeterministic candidate sampling with seeded ordering for parity across stores.
- Context: Reduce test flakiness and improve debuggability.
- Consequences: Same inputs yield same candidate ordering; limit clamping enforced.

## D-012 (2026-01-27) — Second-touch guardrails enforced server-side
- Decision: Enforce second-touch caps/cooldowns/disable windows on the server, not just UI.
- Context: Prevent abuse if clients bypass UI; keep one-shot guarantees.
- Consequences: More “held” outcomes (rate_limited/cooldown_active); identity-leak permanently disables pairs; no raw text persisted on flagged path.

## D-013 (2026-01-27) — ops_daily schedule is smoke unless prod configured
- Decision: Scheduled ops_daily runs in smoke mode unless prod secrets are present; strict prod only when configured.
- Context: Avoid daily red runs in non-prod while preserving real prod alerting.
- Consequences: Scheduled runs are non-noisy; strict mode requires `POSTGRES_DSN_PROD` secret; logs print only non-sensitive mode reason.

## D-014 (2026-01-27) — Second-touch offer generation parity
- Decision: Apply the same guardrails at offer generation as send-time enforcement (shared predicate).
- Context: Prevent “dead offers” that would immediately be held at send; keep UX truthful and privacy-safe.
- Consequences: Offers appear only when actionable (cap/cooldown/disable/crisis cleared); send path remains authoritative.

## D-015 (2026-01-27) — Second-touch aggregate metrics are daily and privacy-safe
- Decision: Store second_touch observability as daily aggregate counters (no identifiers, no raw text).
- Context: Need tuning/health signals without privacy risk or scanning large tables.
- Consequences: New aggregates table + CI migration parity; ops_daily reports 7d/30d windows with reason breakdowns.

## D-016 (2026-01-27) — Second-touch health thresholds in ops_daily
- Decision: Add a deterministic second_touch health evaluator with low-volume gating.
- Context: Need actionable signals without alert fatigue in low-volume environments.
- Consequences: Insufficient_data gate returns healthy when volume is low; identity-leak disables are treated as high-signal and fail even at low volume; ops_daily prints a single aggregate-only line with status/reason.

## D-017 (2026-01-27) — ops_daily strict prod enablement
- Decision: Scheduled ops_daily runs strict only when prod secrets are present; smoke otherwise.
- Context: Avoid false alarms when prod data is not configured while preserving real prod alerting.
- Consequences: Non-sensitive mode logs only (no secret echo) and explicit README enablement documentation.

## D-018 (2026-01-27) — Second-touch aggregates retention cleanup
- Decision: Retain second_touch daily aggregates for 180 days and prune older rows via an explicit cleanup command.
- Context: Prevent unbounded growth while keeping a reasonable operational history for tuning.
- Consequences: Cleanup is operator-controlled (ops_daily subcommand) and outputs aggregate-only deleted counts.

## D-019 (2026-01-27) — Production wiring runbook + db_verify
- Decision: Document prod wiring with secret names only and a non-sensitive verification checklist.
- Context: Provide deterministic, safe signals even when no active DB exists yet.
- Consequences: db_verify emits stable reason codes (psycopg_missing, missing_dsn, db_connect_failed) without echoing secrets.

## D-020 (2026-01-27) — Manual DB bootstrap workflow + dry_run first
- Decision: Add a manual-only db_bootstrap workflow (no schedule) with dry_run and apply_migrations → verify sequence.
- Context: Need a repeatable, idempotent bootstrap path before production DB exists.
- Consequences: Operators can validate config without touching DB, then apply migrations and verify schema with non-sensitive outputs.

## D-021 (2026-01-27) — ops_daily strict failure alerting
- Decision: Use GitHub Issues as the default alert channel for strict ops_daily failures (deduped by title).
- Context: Strict failures were only visible as red workflow runs; need actionable alerts without new infra.
- Consequences: Optional Slack notifications behind secret presence; alerts are aggregate-only and fire only in strict mode.

## D-022 (2026-01-27) — Ops playbook + manual prod verification
- Decision: Add an operator-grade playbook to standardize deploy, rollback, and incident triage.
- Context: Production readiness needs repeatable procedures without leaking secrets.
- Consequences: prod_verify is manual-only to avoid accidental prod touches; outputs remain aggregate-only and non-sensitive.

## D-023 (2026-01-27) — Second-touch aggregates recompute tool
- Decision: Add an operator-driven recompute tool for last N days (default 7, max 30) to recover from aggregate drift.
- Context: Counters can drift or miss increments; full-table scans are undesirable.
- Consequences: Recompute is partial when source events are not persisted (offers/suppression/held may be incomplete); tool must emit recompute_partial with a reason.

## D-024 (2026-01-27) — Minimal second_touch events for full recompute
- Decision: Persist minimal second_touch events solely to enable deterministic aggregate recompute.
- Context: Partial recompute was insufficient for recovery after counter drift.
- Consequences: Store only event_day_utc, event_type, reason, created_at; explicitly no user IDs, offer IDs, message IDs, raw text, or DSNs. Add event retention cleanup and make recompute full when events exist.

## D-025 (2026-01-27) — Security scanning + dependency remediation
- Decision: Add pip-audit and gitleaks scanning in CI with pinned versions.
- Context: Need automated hygiene for dependencies and secrets as we approach prod.
- Consequences: Gitleaks runs via CLI with best-effort SARIF upload to avoid CI flakiness; dependency pins updated (fastapi==0.128.0, starlette==0.49.1). Scanning uses requirements.txt (no lockfile).

## D-026 (2026-01-27) — Production bootstrap dry-run validation
- Decision: Add `db_bootstrap --dry-run` to validate migration plan without DB connectivity or secrets.
- Context: Operators need a CI-safe bootstrap check even before the prod DB exists.
- Consequences: Dry-run validates migration existence, duplicates, and ordering with a stable single-line summary; `db_verify` returns `status=not_configured` (exit 0) when DSN is missing to keep CI green. CI now includes a `prod_bootstrap_dry_run` job that does not require prod secrets.

## D-027 (2026-01-27) — ops_daily insufficient_data token gating
- Decision: Scheduled ops_daily normalizes only when (exit_code == 2 AND stdout contains `status=insufficient_data`).
- Context: Zero-traffic environments can legitimately return exit 2; we must avoid masking real unhealthy exit 2 signals.
- Consequences: Added stdlib-only helper `tools/ops_ci_normalize.py` to enforce token gating; watchdog outputs `status=insufficient_data reason=delivered_total_0` as an explicit contract.

## D-028 (2026-01-27) — Production config contract enforcement
- Decision: Introduce stdlib-only `prod_config_contract` as the single source of truth for required prod env **names**.
- Context: Scheduled ops could silently degrade into smoke mode if secrets are missing/misnamed.
- Consequences: Cron runs fail-fast on `prod_config status=fail reason=missing_env`; PR/CI runs remain secretless and CI-safe.

## D-029 (2026-01-27) — DB migrations integration gate
- Decision: Add an ephemeral-Postgres CI job to apply migrations, verify required tables, and re-apply for idempotency.
- Context: Dry-run validates ordering but cannot catch SQL/runtime migration failures.
- Consequences: Introduce `db_migrations_smoke` helper with stable single-line output; `schema_migrations` ledger enforces idempotent applies and checksum mismatch detection.

## D-030 (2026-01-27) — Operator runbook + docs consistency gate
- Decision: Add `docs/operator_runbook.md` as the canonical ops source of truth.
- Context: Ops guidance was spread across multiple files and at risk of drift.
- Consequences: Add `tools/docs_consistency_check.py` (stdlib) to enforce required tokens and prevent credential-like strings in docs.

## D-031 (2026-01-27) — Ops metrics snapshot + regression gate
- Decision: Emit a single-line `ops_metrics_snapshot` JSON as the canonical daily KPI output.
- Context: We need a stable, machine-readable snapshot to detect regressions early.
- Consequences: Add `metrics_regression_check` with MIN_N guardrail; cron runs fail only when thresholds are breached above MIN_N.
