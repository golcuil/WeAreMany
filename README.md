# We Are Many

## How to run on iOS Simulator / Android Emulator

Set the backend URL with `--dart-define=API_BASE_URL=...`. Use the simulator
host mapping for your target:

- iOS Simulator:
  ```bash
  flutter run --dart-define=API_BASE_URL=http://localhost:8000
  ```
- Android Emulator:
  ```bash
  flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
  ```

Optional (debug/profile only): pass a dev bearer token:

```bash
flutter run \
  --dart-define=API_BASE_URL=http://localhost:8000 \
  --dart-define=DEV_BEARER_TOKEN=your-dev-token
```

In release builds, `DEV_BEARER_TOKEN` is ignored.

For a stable simulator target without hardcoding device IDs (IDs can change; use
`flutter devices` to inspect):

```bash
flutter run -d ios \
  --dart-define=API_BASE_URL=http://127.0.0.1:8000 \
  --dart-define=DEV_BEARER_TOKEN=tokenA
```

## Local backend + Flutter dev tokens

Backend (accepts dev tokens only when allowlisted):

```bash
export DEV_BEARER_TOKENS=tokenA,tokenB
uvicorn backend.app.main:app --reload --port 8000
```

Backend tests (from repo root):

```bash
python3 -m pip install -r backend/requirements.txt
PYTHONPATH=backend python3 -m pytest -q
```

## Ops: ops_daily workflow (prod strict vs smoke)

The scheduled `ops_daily` GitHub Actions workflow runs in **strict** mode only
when production is configured. Otherwise it runs in **smoke** mode to avoid
noisy failures in environments without data.

Canonical operator runbook:
- `docs/operator_runbook.md`
Ops metrics snapshot + regression check are described there (aggregate-only).
Secret rotation checklist:
- `docs/secret_rotation.md`

Enable strict prod monitoring by setting the required secret:

- `POSTGRES_DSN_PROD`

Behavior:
- **With** `POSTGRES_DSN_PROD`: scheduled runs execute `tools.ops_daily all`
  and fail the workflow on unhealthy signals.
- **Without** `POSTGRES_DSN_PROD`: scheduled runs execute `tools.ops_daily smoke`
  and stay green.
- Scheduled runs normalize **only** when the output includes:
  - `status=insufficient_data reason=delivered_total_0`
  - All other exit-2 cases remain failures.
- Cron runs require the prod config contract; missing env names fail fast (names only, no values).

## Production wiring runbook (ops + DB)

### Required secrets (names only)
- `POSTGRES_DSN_PROD`

### Required env vars
- `APP_ENV=prod` (if used by your deployment)

### Config verification checklist (non-sensitive)
1) Verify DSN secret is set (do not print it):
   - GitHub Actions → Secrets → `POSTGRES_DSN_PROD` is present.
2) Verify DB connectivity + required tables (aggregate-only output):
   ```bash
   POSTGRES_DSN_PROD=... PYTHONPATH=backend:. python3 tools/db_verify.py
   ```
   Expected: `db_verify status=ok`

### Migrations (canonical path)
- Migrations live in `db/migrations/` and are applied in order.
- Apply migrations using the same order as `.github/workflows/ci.yml`.
- Verify required tables using `tools/db_verify.py` after migration.

### DB bootstrap (first-time)
1) Configure secret: `POSTGRES_DSN_PROD` (names only; do not print values).
2) Run Actions → `db_bootstrap` → `dry_run`.
   - Expected: `db_bootstrap_dry_run status=ok migrations=<n>`.
3) Run Actions → `db_bootstrap` → `all`.
   - Expected: `db_bootstrap status=ok mode=all`.
4) Run Actions → `ops_daily` → `mode=prod` to validate strict monitoring.

### CI migration integration gate
- CI runs `db_migrations_integration` to apply migrations + verify against ephemeral Postgres and re-apply for idempotency.
- Summary: `db_migrations_smoke status=ok` (single-line, non-sensitive).

### ops_daily strict validation (prod)
1) Trigger Actions → `ops_daily` → Run workflow with `mode=prod`.
2) Expected log line: `mode=strict reason=prod_configured`.
3) Expected output: aggregate-only metrics + health lines; non-zero exit indicates unhealthy.

### Cleanup cadence (optional guidance)
- To prune second_touch aggregates explicitly:
  ```bash
  PYTHONPATH=backend:. python3 -m tools.ops_daily cleanup_second_touch_aggregates
  ```
- Suggested cadence: monthly (only if desired).

Flutter (debug/profile only, uses a dev bearer token if provided):

```bash
flutter run \
  --dart-define=API_BASE_URL=http://localhost:8000 \
  --dart-define=DEV_BEARER_TOKEN=tokenA
```
