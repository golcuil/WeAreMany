---
title: 'Ghost Signal Notification Engine'
slug: 'ghost-signal-notification-engine'
created: '2026-01-29T15:18:56Z'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['FastAPI', 'Pydantic', 'Postgres', 'Flutter', 'Riverpod', 'pytest']
files_to_modify: [
  'backend/app/main.py',
  'backend/app/repository.py',
  'backend/app/config.py',
  'backend/app/events.py',
  'db/migrations/0001_init.sql',
  'db/migrations/0002_eligible_principals.sql',
  'db/migrations/0004_message_origin.sql',
  'db/migrations/0007_messages_theme_tags.sql',
  'db/migrations/*_ghost_signal.sql (new)',
  'backend/tests/* (new/updated)',
  'lib/core/network/models.dart',
  'lib/core/network/api_client.dart',
  'lib/features/* (notification hook, if any)'
]
code_patterns: [
  'FastAPI endpoints + Pydantic models in backend/app/main.py',
  'Repository pattern with in-memory + Postgres implementations',
  'SQL migrations in db/migrations/*.sql',
  'Config/env constants in backend/app/config.py',
  'Event emitter schema in backend/app/events.py',
  'Flutter Riverpod + Navigator routing'
]
test_patterns: [
  'pytest unit tests in backend/tests',
  'in-memory repository for deterministic tests',
  'Flutter widget tests in test/'
]
---

# Tech-Spec: Ghost Signal Notification Engine

**Created:** 2026-01-29T15:18:56Z

## Overview

### Problem Statement

We need a non-addictive, privacy-safe notification system that delays peer message delivery by 5–15 minutes, enforces silent hours (22:00–09:00 local), and sends zero-PII push notifications, while respecting crisis hard-blocks (risk_level==2).

### Solution

Introduce a server-side delivery-delay gate and silent-hours scheduler for peer messages, emit zero-PII notification signals to the client, and add frontend notification handling using a generic title only. Enforce crisis window suppression and verify behavior with unit/integration tests.

### Scope

**In Scope:**
- Randomized 5–15 min delivery delay for peer messages
- Silent Hours gate (22:00–09:00 local time)
- Zero-PII push notification handling on frontend
- Crisis window suppression (risk_level==2)

**Out of Scope:**
- Typing indicators
- Addictive/streak notifications
- Social features

## Context for Development

### Codebase Patterns

- Backend message flow is in `backend/app/main.py` and uses repository methods to save messages and create inbox items; no background job/queue system found.
- Crisis gating uses `risk_level==2` and `crisis_action` tokens; crisis window stored via repository methods.
- Frontend uses Riverpod controllers and Navigator routing; no notification subsystem found yet.
- Repository has both InMemory and Postgres implementations; tests frequently monkeypatch repo methods.
- DB schema is defined via SQL migrations under `db/migrations/`.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| backend/app/main.py | message submission and delivery flow |
| backend/app/repository.py | persistence and inbox creation |
| backend/app/delivery_decision.py | delivery mode decisions |
| backend/app/config.py | environment-configured constants |
| backend/app/events.py | event schema + emitter |
| db/migrations/0001_init.sql | messages + inbox schema baseline |
| db/migrations/0002_eligible_principals.sql | eligible pool schema |
| db/migrations/0004_message_origin.sql | messages table extensions |
| db/migrations/0007_messages_theme_tags.sql | theme tags schema |
| lib/core/network/api_client.dart | API calls |
| lib/core/network/models.dart | request/response models |
| lib/features/inbox/ | message list UI |
| backend/tests/test_* | message/crisis/moderation test patterns |

### Technical Decisions

- Delay/silent hours must be enforced server-side (source of truth).
- Notifications must be zero-PII (generic title only).
- No new social surfaces or addictive mechanisms.
- Delivery delay uses DB `deliver_at` + `delivery_status`, and a lightweight polling runner (no new infra).
- Silent Hours computed from client-provided `timezone_offset_minutes`; default UTC if missing.
- Store transient `last_known_timezone_offset_minutes` (anonymized; no PII) for recipient silent-hours enforcement.
- Notification intents stored as DB events (allowlisted, no content, no message IDs).
- risk_level==2 hard-block: no scheduling, no delivery, no notification intents (double-check at enqueue + intent creation).
- Runner concurrency safety: claim deliveries with row-level locking (`SELECT ... FOR UPDATE SKIP LOCKED`) and update `delivery_status` at end of a single transaction to prevent double-delivery.
- Intent idempotency: use an opaque `intent_key` (HMAC of message_id) to dedupe without storing message IDs.
- Silent hours deferral: if computed delivery time falls within 22:00–09:00 local, set `deliver_at` to next local 09:00 to avoid loop.
- Runner resilience: asyncio task wraps each tick in try/except; a single failure must not stop the loop.
- Restart recovery: pending messages remain in DB and are picked up on next runner tick.

## Implementation Plan

### Tasks

- [ ] Task 1: Add DB schema for delayed delivery + notification intents
  - File: `db/migrations/0017_ghost_signal.sql` (new)
  - Action: Add columns and tables (see DDL below)
  - Notes: Use allowlisted schema; no message text or IDs in notification_intents

- [ ] Task 2: Extend repository data model + methods
  - File: `backend/app/repository.py`
  - Action: Add message fields `deliver_at`, `delivery_status`; add notification intent record + persistence methods; add last_known_timezone_offset storage on eligible_principals
  - Notes: InMemory + Postgres parity required; delivery + inbox + intent creation must be transactional

- [ ] Task 3: Update message submission flow (delay + timezone capture)
  - File: `backend/app/main.py`
  - Action: Accept `timezone_offset_minutes`; compute `deliver_at = now + rand(5–15m)`; store `last_known_timezone_offset_minutes`; set `delivery_status='pending'`; do not deliver immediately
  - Notes: Hard-block on risk_level==2 (no scheduling, no intent)

- [ ] Task 4: Implement background polling runner (asyncio lifecycle)
  - File: `backend/app/main.py` (or new `backend/app/ghost_signal_runner.py`)
  - Action: Add FastAPI lifespan background task polling every 60s; deliver pending messages with `deliver_at <= now()` and not in silent hours; create inbox items and notification intents
  - Notes: Non-blocking; stop on shutdown; guard against overlapping ticks; handle exceptions per tick

- [ ] Task 5: Enforce Silent Hours for recipient
  - File: `backend/app/main.py` + `backend/app/repository.py`
  - Action: Use `last_known_timezone_offset_minutes` to compute recipient local time; if within 22:00–09:00, defer delivery until next 09:00 local
  - Notes: If missing, default UTC offset 0

- [ ] Task 6: Double-check crisis hard-block before intent creation
  - File: `backend/app/main.py`
  - Action: In runner, re-check `risk_level==2` and crisis window before delivery/intent; skip if triggered and mark status blocked
  - Notes: Must happen even if message was previously scheduled

- [ ] Task 7: Frontend request payload updates
  - File: `lib/core/network/models.dart`
  - Action: Add `timezone_offset_minutes` to relevant requests (mood + message)
  - Notes: Client sends local offset; default if unavailable

- [ ] Task 8: Tests (backend + frontend)
  - File: `backend/tests/*`, `test/*`
  - Action: Unit + integration tests for delay window, silent hours boundaries, crisis block, notification intent schema (no content), and runner delivery
  - Notes: No new infra; use InMemory repo and time control

### Acceptance Criteria

- [ ] AC1: Given a message is submitted with risk_level < 2, when it is accepted, then `deliver_at` is set between 5–15 minutes in the future and `delivery_status=pending`.
- [ ] AC2: Given recipient local time is between 22:00–09:00, when the runner evaluates pending delivery, then delivery is deferred to the next 09:00 local time.
- [ ] AC2a: Given a message scheduled for 21:55 with a 10-minute delay, when the runner evaluates delivery at 22:05 local, then deliver_at is moved to next 09:00 local (no loop).
- [ ] AC3: Given `risk_level==2` at submit time, when `/messages` is called, then the response is `status=blocked` and no message/intent is persisted.
- [ ] AC4: Given a message is pending, when the runner is about to deliver, then it re-checks crisis conditions and does not deliver or create intents if risk_level==2.
- [ ] AC5: Given a delivery occurs, when a notification intent is created, then it contains no message text or message IDs.
- [ ] AC6: Given `timezone_offset_minutes` is missing, when silent hours are computed, then UTC is used deterministically.
- [ ] AC7: Given the runner takes longer than the polling interval, when multiple ticks overlap, then each message is delivered at most once (no duplicate inbox items or intents).
- [ ] AC8: Given the server restarts, when the runner resumes, then all pending messages are eventually processed.

## Additional Context

### Dependencies

- No new external services (no Redis/Celery). Uses Postgres only.
- Client must send `timezone_offset_minutes` for local-time enforcement.

### Testing Strategy

- Unit tests:
  - delay randomness within [5m, 15m]
  - silent hours boundary (21:59 vs 22:01 local)
  - crisis hard-block at submit + at runner stage
  - notification intents schema has no content or message IDs
- Integration tests:
  - submit → pending → runner delivers → inbox item + notification intent created
  - silent hours defers delivery
- Flutter widget tests:
  - request payload includes timezone_offset_minutes (serialization)

### Notes

- Background runner: asyncio task in FastAPI lifespan; poll interval 60s; per-tick try/except; do not terminate on single failure.
- Notification intents are DB-only stubs; provider integration deferred.
- Use allowlisted, tokenized logs only; no raw text or identifiers.

### Notification Intents DDL (spec)

```
CREATE TABLE IF NOT EXISTS notification_intents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  intent_key text NOT NULL,
  recipient_hash text NOT NULL,
  kind text NOT NULL CHECK (kind IN ('inbox_message')),
  status text NOT NULL CHECK (status IN ('created', 'sent', 'failed')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS notification_intents_intent_key_idx
  ON notification_intents (intent_key);
```

### Message Delay DDL (spec)

```
ALTER TABLE messages
  ADD COLUMN IF NOT EXISTS deliver_at timestamptz NULL,
  ADD COLUMN IF NOT EXISTS delivery_status text NOT NULL DEFAULT 'pending'
    CHECK (delivery_status IN ('pending', 'delivered', 'blocked'));

CREATE INDEX IF NOT EXISTS messages_delivery_pending_idx
  ON messages (delivery_status, deliver_at);
```

### Timezone Offset Storage (spec)

```
ALTER TABLE eligible_principals
  ADD COLUMN IF NOT EXISTS last_known_timezone_offset_minutes integer NULL;
```
