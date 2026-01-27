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
