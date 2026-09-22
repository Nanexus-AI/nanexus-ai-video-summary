# Client stage 8 acceptance

> **Historical evidence.** This dated acceptance record is retained for engineering context and
> does not describe the current project stage. See [`docs/android.md`](../android.md) and
> [`docs/architecture.md`](../architecture.md).

Date: 2026-08-24

## Prerequisite audit

- Video Summary started clean at `f5f23a4`; Event Intelligence started at `581a852` with four pre-existing untracked asset/document files untouched.
- Search/Summary/Chat v1 targeted tests passed (30); Event Intelligence public event/processor/contract targeted tests passed (22).
- Alembic single heads are Video Summary `7c1c001009` and Event Intelligence `4b1f001006`.
- After detecting and rebuilding a stale local migration image, an existing database upgraded from `5a1c001007` to head and completed downgrade/upgrade. A separate fresh database reached head and contained `embedding_records`, `summaries`, `chat_jobs` and `chat_messages`. Offline SQL generation passed.
- Inspection confirmed public HTTP boundaries, async Job/Worker execution, UUID citations, legacy fallback, and no new-path Event Intelligence ORM/database or Frigate/Evidence access.

## CLIENT-WEB-001～003

- Added a Video Summary-owned React/Vite product with Summary, Search, async Chat, Subject links, Processor/Model status and Settings.
- Added loading, empty, degraded, incompatible-capability, offline/error, retry and Job-processing states.
- Web tests: 3 passed; TypeScript typecheck and production build passed.

## CLIENT-ANDROID-001～006

- Added stable v1 Capability/Summary/Search/Chat DTOs and JSON fixture while preserving legacy DTOs/calls.
- Default Summary/Search/Chat ViewModels use v1. Chat submits/polls Jobs, shows degraded answers and opens UUID citations.
- Capability negotiation is visible in Settings and gates product pages. Errors are retryable.
- Added centralized Token Provider and redacted Debug-only logging. Release requires HTTPS and forbids cleartext; Debug permits LAN HTTP.
- Legacy Timeline/Event screens and methods remain rollback-only and are absent from default navigation.
- Android JVM tests, Debug build, Release build and release lint-vital passed.

## Regression and limitations

- Video Summary: 78 backend tests passed; Python compile and changed-file Ruff passed. Broad Mypy remains blocked by pre-existing SQLAlchemy/queue/provider typing debt.
- Event Intelligence: 153 passed, 3 external-service tests skipped; Ruff and strict Mypy passed. Its Web passed 5 tests, lint, typecheck and build.
- Both Compose files rendered successfully with a test-only required processor token. No schema change was needed and no historical migration changed.

The Web/Android local owner keys are isolation identifiers, not authentication. Deployment/Security must define server-issued identity, Subject authorization, HTTPS/certificates, CORS/reverse proxy policy, secure token persistence and secret distribution. This stage does not authorize deployment, shadow validation or retirement.
