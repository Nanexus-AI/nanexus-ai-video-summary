# Migration development progress

## 2026-08-21: BASELINE-001～005 save legacy-system baseline

### Goal

Freeze legacy infrastructure expansion and preserve repeatable product behavior before contract work.

### Completed

- Audited both repositories and preserved all pre-existing changes.
- Documented the maintenance-only legacy boundary.
- Added backend pytest, Android JVM tests, a Debug APK build gate, a sanitized fixture, exact behavior snapshots, UI acceptance, and a known-difference list.

### Data and contract changes

Added only synthetic test fixture data. No database migration, public API contract, shared ORM, cross-repository dependency, Frigate/Evidence access, or runtime data change was introduced.

### Verification results

- Backend: `.venv/bin/python -m pytest` — 13 passed.
- Android: `./gradlew testDebugUnitTest assembleDebug` — 5 JVM tests passed and Debug APK built.
- Static checks: Python byte compilation and `git diff --check` passed.

### Failure tests

Invalid Frigate payload, empty summary day, no-match search, empty Chat context, blank Search input, and Timeline repository failure are covered.

### Compatibility impact

Runtime behavior is unchanged. Android ViewModels now depend on a small local `NanexusDataSource` interface implemented by the existing repository; production construction remains the same.

### Known limitations

See `docs/baseline-acceptance.md`. The baseline documents legacy behavior and does not claim production readiness.

### Rollback

No runtime switch changed. Test and documentation additions can be reverted independently; the old chain remains available.

### Next step

Only after a separate authorization and architecture review: verify stage 1 prerequisites before CONTRACT-001. This task does not start it.

## 2026-08-21: CONTRACT-001 Processor Contract v1 consumer boundary

### Goal

Record the approved cross-repository dependency and consumption boundary without implementing a client or runtime integration.

### Completed

- Recorded the explicit architecture Gate approval and six decisions.
- Confirmed that Video Summary will consume Event Intelligence's published Processor Job schema independently.

### Data and contract changes

No Video Summary runtime model, database, API, queue or Android DTO changed. The normative Processor Job contract is owned by Event Intelligence.

### Verification results

Event Intelligence: 135 passed, 3 existing service-dependent integration tests skipped; Ruff and Mypy strict passed. Video Summary: 13 backend tests passed; 5 Android JVM tests and Debug APK build passed. Both repositories passed `git diff --check`.

### Known limitations

No Event Intelligence client, shared CONTRACT-005 fixture, Result, Capability or permission contract exists yet.

### Next step

CONTRACT-002 only after separate task authorization; do not begin FOUNDATION or OpenCLIP migration.

## 2026-08-21: CONTRACT-002～005 cross-project contract freeze

### Goal

Freeze Enrichment Result, Capability, minimum authority/privacy, compatibility and shared sanitized fixtures without starting FOUNDATION.

### Completed

- Added independent consumer Pydantic mirrors for published Job/Result/Capability v1.
- Added the same sanitized conformance fixture used by Event Intelligence.
- Froze status invariants, auditable invocation facts, typed Caption/Tags claims and no-chain-of-thought rule.
- Froze Capability negotiation, media limits, default-deny object authority, Replay/Dry Run and compatibility semantics.

### Verification results

Video Summary consumer contract tests: 4 passed; full backend: 17 passed; Android JVM tests and Debug APK build succeeded. Event Intelligence contract tests: 16 passed; full backend: 142 passed and 3 external-service integration tests skipped. Ruff, Mypy, both `git diff --check` runs, and byte-identical Fixture comparison passed.

### Boundary verification

No runtime cross-repository import, shared ORM/database, API, queue, Worker, provider, direct Frigate/Evidence access or legacy removal was added. Event Intelligence remains the normative owner; this repository independently consumes release artifacts.

### Known limitations

Runtime auth/Evidence enforcement, authoritative Claim/ModelInvocation persistence, ReviewItem lifecycle and idempotency encoding vectors remain later-stage prerequisites.

### Next step

Stop after stage 1 acceptance. Do not begin FOUNDATION without a new task and prerequisite review.

## 2026-08-21: FOUNDATION-001～006 Event Intelligence foundation

### Goal

Complete the reliable, auditable Stub AI Enrichment foundation in Event Intelligence without moving Video Summary runtime behavior or starting the cross-repository vertical slice.

### Completed

- Verified the Event Intelligence Alembic schema, ReviewItem ended trigger, atomic Job/Outbox creation, independent consumer group, Retry/DLQ/requeue lifecycle, deterministic Stub and Claim/API/Web audit display.
- Verified missing-Evidence abstention and persisted Job/Attempt/Audit state for retry, dead-letter and operator requeue.
- Added this repository's cross-repository Gate record and updated the migration plan status.

### Verification results

Event Intelligence backend: 149 passed and 3 existing external-service tests skipped. Ruff, Mypy strict (72 source files), Alembic single head `4b1f001006`, Web 5 tests, Web production build and diff checks passed. Failure tests cover restart recovery, timeout, duplicate delivery, poison messages, unavailable Evidence and DLQ requeue.

### Boundary verification

All runtime and persistence implementation remains in Event Intelligence. This repository added documentation only: no cross-repository import, shared database/ORM, direct Frigate/Evidence access, provider, Worker, API switch, legacy removal, publish or push.

### Known limitations

The isolated run skips three external PostgreSQL/Redis tests; the real-service run passed all 152 tests and preserved Redis AOF and Alembic state across kill/restart. No real AI provider is enabled in stage 2.

### Next step

Stop after stage 2. Stage 3 (`SLICE-001` onward) requires separate authorization and a fresh prerequisite review.
