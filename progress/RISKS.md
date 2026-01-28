# RISKS — Active risks & mitigations

## R-001 Identity leak attempts in user text
- Risk: Users share phone/email/@handles leading to re-identification.
- Mitigation: detect -> strip -> rewrite; block repeated attempts; shadow throttling; safety event logging without raw text.
- Owner: SecurityEngineer
- Status: OPEN

## R-002 Social graph inference via metadata
- Risk: timestamps/IDs/ordering reveal relationships.
- Mitigation: non-guessable IDs, day-level timestamps, k-anon aggregate insights only, no sender info/logs.
- Owner: CTO + DataEngineer
- Status: OPEN

## R-003 Abuse / spam flood
- Risk: bots hammer submit endpoints or attempt scraping.
- Mitigation: per-user/IP/device throttles in Redis; anomaly alerts; penalties.
- Owner: Backend + SecurityEngineer
- Status: OPEN

## R-004 Dependency version drift
- Risk: lockfile constraints diverge from upstream, increasing upgrade risk later.
- Mitigation: add a future task to review `flutter pub outdated` and plan a staged upgrade.
- Owner: CTO
- Status: OPEN

## R-005 Candidate pool sourcing in-memory
- Risk: matching candidate pool is in-memory and requires POSTGRES_DSN for production, risking empty delivery.
- Mitigation: add a follow-up task for DB-backed candidate selection without social graph signals.
- Owner: Backend + CTO
- Status: OPEN

## R-006 DB-backed candidate pool follow-up
- Risk: eligible pool remains in-memory without DB-backed sampling, limiting delivery and consistency.
- Mitigation: T-012 adds Postgres-backed candidate pool sampling without social graph signals.
- Owner: Backend + DataEngineer
- Status: OPEN

## R-007 CI/local parity gap for backend tests
- Risk: backend pytest runs in CI but fails locally due to dependency/import path drift.
- Mitigation: T-013 standardizes install command and import paths for local parity.
- Owner: Backend
- Status: OPEN

## R-008 Second-touch abuse or overuse
- Risk: repeated “second-touch” offers could be spammy or coercive.
- Mitigation: strict eligibility, cooldowns, monthly caps, negative-ack disable, identity-leak permanent block; offer generation gated by the same guardrails to avoid dead offers.
- Owner: CTO + SecurityEngineer
- Status: OPEN

## R-012 False positives in identity-leak detection
- Risk: false positives could permanently disable healthy second-touch pairs.
- Mitigation: monitor hold_reason rates; add review/tuning of patterns; keep logs aggregate-only.
- Owner: SecurityEngineer
- Status: OPEN

## R-013 Guardrail tuning drift
- Risk: cap/cooldown values may be too strict or too lenient over time.
- Mitigation: monitor aggregate hold_reason rates; tune constants via config.
- Owner: CTO
- Status: OPEN

## R-009 Ops false positives in empty environments
- Risk: watchdog runs in CI without data and fails noisily.
- Mitigation: ops_daily supports CI-safe mode; production runs remain strict.
- Owner: CTO
- Status: OPEN

## R-014 Prod secret misconfiguration
- Risk: missing or misnamed prod secrets cause schedule to run smoke unintentionally.
- Mitigation: require `POSTGRES_DSN_PROD` for strict mode; document secret name and verify in CI logs (mode message only).
- Owner: CTO
- Status: OPEN

## R-015 Second-touch metrics interpretation
- Risk: low volume can distort rates; taxonomy drift in suppression/hold keys can mislead ops.
- Mitigation: aggregate-only counters with 7d/30d windows; document keys; monitor for drift.
- Owner: DataEngineer + CTO
- Status: OPEN

## R-016 Second-touch health threshold tuning
- Risk: thresholds may be too strict or too lenient, causing false positives/negatives.
- Mitigation: insufficient_data gate; re-evaluate thresholds using 30d aggregates; adjust only with aggregate evidence.
- Owner: DataEngineer + CTO
- Status: OPEN

## R-017 ops_daily prod enablement drift
- Risk: secret naming/config changes could leave schedule in smoke mode unintentionally.
- Mitigation: document required secret in README; periodic verification that strict schedule runs in prod-configured env.
- Owner: CTO
- Status: OPEN

## R-018 Second-touch aggregates retention trade-off
- Risk: retention window may be too short for long-baseline analysis or too long for storage costs.
- Mitigation: 180d default with explicit cleanup; adjust via config after reviewing aggregate trends.
- Owner: DataEngineer + CTO
- Status: OPEN

## R-019 Prod wiring verification gap
- Risk: without an active DB, strict prod monitoring cannot be fully validated.
- Mitigation: db_verify emits deterministic non-sensitive failure reasons; run strict mode after DB is provisioned and record baseline.
- Owner: CTO
- Status: OPEN

## R-020 Prod bootstrap operator error
- Risk: manual DB bootstrap may be misrun (wrong secret/env, partial migrations).
- Mitigation: db_bootstrap dry_run first; apply_migrations → verify sequence; non-sensitive reason codes; document steps in README.
- Owner: CTO + DataEngineer
- Status: OPEN

## R-021 ops_daily alert fatigue
- Risk: strict thresholds could generate frequent alerts before baseline is established.
- Mitigation: strict-only alerting, aggregate-only outputs, revisit thresholds after baseline.
- Owner: CTO + DataEngineer
- Status: OPEN

## R-022 Prod deploy playbook gaps
- Risk: platform-specific deploy steps remain TBD, increasing rollout risk.
- Mitigation: generic playbook + manual verification workflow; add concrete commands once infra is finalized.
- Owner: CTO
- Status: OPEN

## R-023 Second-touch recompute gaps
- Risk: recompute is partial due to missing source-of-truth events (missing_source_events).
- Mitigation: operator-facing partial flag + reason; consider minimal event logging if full recompute is required.
- Owner: DataEngineer + CTO
- Status: OPEN

## R-024 Second-touch event volume growth
- Risk: event table may grow if cleanup is not run regularly.
- Mitigation: 90-day retention + cleanup tool; run periodically in prod.
- Owner: DataEngineer + CTO
- Status: OPEN

## R-025 Security scanning maintenance
- Risk: scanner false positives or tool/version drift could break CI or hide issues; SARIF upload may fail during external outages.
- Mitigation: pin pip-audit and gitleaks versions; keep scans strict; make SARIF upload best-effort; review and adjust allowlists sparingly.
- Owner: SecurityEngineer + CTO
- Status: OPEN

## R-026 Bootstrap verification drift
- Risk: incorrect env/credentials or missing migrations could reach prod without a reliable preflight check.
- Mitigation: db_bootstrap dry-run validates migration plan; db_verify emits non-sensitive, stable reason codes; operator checklist documents the order of operations.
- Owner: CTO + DataEngineer
- Status: OPEN

## R-027 ops_daily insufficient_data persistence
- Risk: sustained `status=insufficient_data` after expected traffic could mask a delivery regression.
- Mitigation: token-gated normalization only for scheduled runs; operator playbook calls out this case explicitly.
- Owner: CTO + DataEngineer
- Status: OPEN

## R-028 Prod config drift
- Risk: secret rotation or misnaming could break scheduled monitoring or force fail-fast.
- Mitigation: prod_config_contract enforces required env names; document verification steps and re-run after rotations.
- Owner: CTO + SecurityEngineer
- Status: OPEN

## R-029 Migration runtime failures
- Risk: SQL/runtime migration failures could slip past dry-run validation.
- Mitigation: db_migrations_integration CI gate applies migrations against ephemeral Postgres and verifies idempotency.
- Owner: CTO + DataEngineer
- Status: OPEN

## R-030 Ops docs drift
- Risk: scattered operational guidance can drift and cause operator error.
- Mitigation: canonical operator runbook + CI docs consistency check with token/heuristic validation.
- Owner: CTO + SecurityEngineer
- Status: OPEN

## R-031 Ops metrics regression tuning
- Risk: thresholds may be too strict or too lenient, causing false positives/negatives.
- Mitigation: MIN_N guardrail; adjust thresholds only after baseline volume is established.
- Owner: DataEngineer + CTO
- Status: OPEN

## R-032 Retention cleanup performance
- Risk: large TTL deletes could cause table locks or slow cron runs.
- Mitigation: retention scope limited to ops tables with bounded growth; monitor cron duration and consider batching if needed.
- Owner: DataEngineer + CTO
- Status: OPEN

## R-033 DR restore dependencies
- Risk: real-world restores depend on external backup storage and access controls.
- Mitigation: DR playbook + restore_dry_run gate; schedule periodic operator drills.
- Owner: CTO + DataEngineer
- Status: OPEN

## R-034 Rehearsal coverage limits
- Risk: prod_rehearsal cannot validate external integrations or real backup systems.
- Mitigation: keep rehearsal as a fast CI gate; schedule periodic operator drills for external dependencies.
- Owner: CTO + DataEngineer
- Status: OPEN

## R-035 Secret echo guard tuning
- Risk: guard heuristics may trigger false positives or allowlists may be too permissive.
- Mitigation: keep rules narrow, pin tool versions, and adjust allowlists only with review; no matched secrets echoed.
- Owner: SecurityEngineer + CTO
- Status: OPEN

## R-036 Release execution drift
- Risk: releases may proceed without validating prod readiness or rollback steps.
- Mitigation: manual pre_release_gate workflow + versioned release checklist and rollback guidance.
- Owner: CTO
- Status: OPEN

## R-037 Launch readiness drift
- Risk: launching without explicit, versioned readiness criteria and sign-off.
- Mitigation: launch checklist + go/no-go template + docs consistency gate.
- Owner: CTO + PM
- Status: OPEN

## R-038 V1 sign-off drift
- Risk: final operator docs drift at launch time, causing inconsistent execution.
- Mitigation: V1 completion bundle + docs consistency gate.
- Owner: CTO
- Status: OPEN

## R-010 System messages misinterpreted as human-written
- Risk: system-origin empathy could be perceived as peer content.
- Mitigation: system-origin only, templated copy, no identity cues, no human claims.
- Owner: UX + Safety
- Status: OPEN

## R-011 Offer misuse / coercion via repeated acknowledgements
- Risk: users may attempt to force “second-touch” offers via manipulation.
- Mitigation: pair thresholds + day span, cooldown, monthly cap, negative-ack disable window.
- Owner: CTO + SecurityEngineer
- Status: OPEN
