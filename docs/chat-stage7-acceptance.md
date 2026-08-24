# Chat stage 7 acceptance

Date: 2026-08-24

## Scope and prerequisites

- Video Summary HEAD was `8825a83`; its Search and Summary migrations, public-contract client tests, model isolation tests, and stage-6 acceptance artifacts were inspected.
- Event Intelligence HEAD was `581a852`; its review detail contract exposes stable Review/Subject UUID, site/camera/timezone, Claim, Decision, Feedback, and Evidence identifiers through `/api/v1/events`.
- Event Intelligence contained four pre-existing untracked asset/document files. They were not modified.

## CHAT-001～007 evidence

- CHAT-001: Alembic `7c1c001009` adds normalized owner-scoped `chat_messages` and asynchronous `chat_jobs`. Role, timestamps, method, stable subjects, prompt/model version, usage/cost, errors, degradation, and ownership are explicit columns.
- CHAT-002: `parse_time_range` returns a structured UTC interval plus site timezone/expression. Today, yesterday, recent N days, explicit dates, morning/afternoon and clock ranges are covered by a fixed fixture, including America/Toronto DST-aware conversion.
- CHAT-003: the worker executes Question → time/camera/site filter → versioned semantic search → versioned summary retrieval → bounded context → answer. It never reads legacy `Event`.
- CHAT-004: answers and API citations use stable Subject UUIDs and `/api/v1/events/{subject_id}`, never legacy integer Event IDs.
- CHAT-005: API only persists/enqueues. `services.chat_worker.main` owns retrieval and LLM calls; the decision is recorded in the stage-7 ADR.
- CHAT-006: context is untrusted and delimited; prompt-injection input forces degradation; context/output are bounded; no chain-of-thought or secrets are stored.
- CHAT-007: unavailable embedding/LLM and detected injection return an auditable extractive answer rather than an unexplained failure.

## Automated verification

- Chat/schema/config/isolation targeted suite: 22 passed.
- Video Summary complete suite: 76 passed (warnings limited to the pre-existing FastAPI `on_event` deprecation).
- Event Intelligence complete prerequisite suite: 153 passed, 3 skipped. The run required the approved unsandboxed test path because sandboxed `aiosqlite` worker threads did not advance; the same suite completed in 1.86 seconds outside that restriction.
- Python compile check: passed.
- Alembic graph: one head, `7c1c001009` after `6b1c001008`; full offline SQL generation passed. The migration also repairs fresh installs where the legacy `conversations` table had only ever been created by `Base.create_all()`, while preserving existing/rollback data.
- Ruff (changed Python files, with the repository's pre-existing FastAPI `B008`/broad-exception and file-open rules excluded): passed. Mypy for the new Chat/LLM/OpenCLIP/worker modules with imports skipped: passed; the wider model module retains the repository's pre-existing dynamic SQLAlchemy `Base` typing errors.
- `docker-compose -f compose.search.yaml config -q`: passed.

## Boundary and rollback

No changes were required in Event Intelligence. Video Summary depends on it only through existing public HTTP contracts. There is no shared DB/ORM and no direct Frigate/Evidence access. Rollback is to stop `chat-worker` and keep using the unchanged legacy endpoints; no legacy data or code was deleted.

## Known limits and next prerequisite

The stage does not switch Web/Android clients, publish, deploy, or retire legacy Chat. Stage 8 may start only after this stage's migration/integration checks remain green in a Compose environment and client ownership authentication is designed; an `owner_id` is an application boundary identifier, not production authentication.

During prerequisite verification, the pre-existing OpenCLIP timeout test never returned because `asyncio.to_thread` kept the default executor alive after cancellation. `_bounded` now uses a daemon execution thread with the same retryable timeout contract; the complete Video Summary suite subsequently passed.
