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
- Mitigation: strict eligibility, cooldowns, monthly caps, negative-ack disable, identity-leak permanent block.
- Owner: CTO + SecurityEngineer
- Status: OPEN

## R-009 Ops false positives in empty environments
- Risk: watchdog runs in CI without data and fails noisily.
- Mitigation: ops_daily supports CI-safe mode; production runs remain strict.
- Owner: CTO
- Status: OPEN
