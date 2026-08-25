# Migration development progress

## 2026-08-24: Stage 8 Web and Android migration

Added the Video Summary-owned Web product and migrated Android's default Summary/Search/Chat flows to stable v1 DTOs, capability negotiation, asynchronous Chat polling and Subject UUID links. Added a client-safe capability/Subject-link API, Debug/Release network split and centralized Android Token Provider boundary. Legacy client DTOs/routes/screens remain rollback-only.

Verification: Video Summary backend 78 passed; Web 3 tests plus typecheck/build; Android JVM tests plus Debug/Release builds and release lint; Event Intelligence backend 153 passed/3 skipped with Ruff/Mypy, Event Intelligence Web 5 tests plus lint/typecheck/build. Both Compose configurations and migration offline SQL passed. A rebuilt migration image verified existing `5a` → head, downgrade/upgrade and a separate fresh install at `7c1c001009`. Broad Video Summary Mypy still reports pre-existing SQLAlchemy/queue/provider typing debt; changed Python files passed Ruff.

No commit, publish, deployment, shadow validation or retirement was performed.

## 2026-08-24: Stage 9 deployment, security and compatibility

Added production fail-closed owner/site/role authorization, HTTPS/CORS/security headers, Android Keystore token storage, frozen Python 3.12 dependencies, integrated/external Compose modes, capability startup checks, operational health/metrics, and Stub/CPU/GPU/Cloud profiles. Development `owner_id` remains isolation-only; production derives ownership from authenticated identity. Legacy API/DTO/client/data/Compose rollback remains. Full Video Summary Mypy still reports nine pre-existing errors and is not reported as passing. No Shadow Validation or retirement began.

Next work is explicitly split into four gates: (1) Stage 9 Closeout—previous-version upgrade, real CPU OpenCLIP, durable kill/restart, clean Stub Demo, Secret/License/SBOM, independent builds and Mypy disposition; (2) Shadow Validation with frozen comparison thresholds; (3) separately authorized MQTT cutover rehearsal and legacy retirement/data handling; (4) open-source release readiness and human publication authorization. Completing one gate does not authorize the next.

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

## 2026-08-21: SLICE-001-005 first cross-repository vertical slice

### Goal

Consume Event Intelligence only through public v1 contracts and complete the external Stub Caption loop without switching or deleting legacy paths.

### Completed

Added the independent HTTP Client, deterministic Worker, service identity, job-scoped Evidence access, Result submission and two-repository Compose overlay. Event Intelligence remains sole owner of ReviewItem, Evidence, Claim and ModelInvocation.

### Verification results

Video Summary: 20 passed; bytecode compilation and diff check passed. Event Intelligence: 152 passed/3 skipped; Ruff and strict Mypy passed. Compose v1 config validation passed.

### Known limitations

Docker Compose v2 is unavailable locally, so services were not started. A daemon-backed smoke run with real media configuration remains a stage 4 prerequisite.

### Next step

Stop at the stage 3 gate. Do not start MODEL-001 or later work.

## 2026-08-21: MODEL-001～006 OpenCLIP Provider migration

### Goal

Move reusable OpenCLIP inference behind a worker-only Provider while preserving Stub fallback, public Evidence access and authoritative base-owned audit records.

### Completed

Added the Provider interface, deterministic Stub, lazy OpenCLIP image/text embedding and zero-shot analysis, configuration factory, dedicated model-worker image, API isolation switch, media validation, retry/abstain behavior, synthetic Compose smoke services and repeatable CPU benchmark.

### Data and contract changes

No wire schema or Video Summary database changed. Event Intelligence's existing ModelInvocation column now receives the previously omitted `latency_ms`. Model/pretrained/device/label-set identity remains within the frozen v1 bounded identity fields.

### Verification results

Video Summary: 36 passed, compileall and diff check passed. Event Intelligence: 152 passed/3 skipped, Ruff and strict Mypy passed. Stub and OpenCLIP Compose configurations validated. Public API closed loops succeeded with both Stub and real CPU OpenCLIP. CPU baseline: 2.8069 s startup, 0.1750 s median single image, 1514.7 MiB peak RSS, stable output across three runs.

### Failure tests

Unsupported type, empty/oversized/corrupt image, timeout, retryable model failure without Result submission, audited decode abstention, incompatible Provider configuration and API heavy-import isolation are covered.

### Compatibility impact

Stub remains the default. The frozen API Search path now defaults to its existing keyword fallback and requires an explicit rollback switch to run legacy in-process inference. Old services and tables remain present.

### Known limitations

The quality baseline is synthetic and English-only. OpenCLIP reports a QuickGELU warning for this installed model/tag combination. Weight licensing remains a release Gate item.

### Rollback

Set `MODEL_PROVIDER=stub` or omit `compose.model.yaml`. The legacy chain remains available; no data deletion or production switch occurred.

### Next step

Stop at stage 4. Stage 5 SEARCH-001～007 requires separate authorization and its storage decision must be reconfirmed.

## 2026-08-24: SEARCH-001～007 Embedding and semantic Search migration

### Goal

Build versioned, rebuildable semantic retrieval without reading the legacy Event table or crossing the Event Intelligence public boundary.

### Completed

Added the application-owned EmbeddingRecord/Alembic migration, HNSW and metadata indexes, asynchronous retry/DLQ indexing, worker-only query embedding HTTP service, Search API v1 filters/pagination/threshold/degradation, reindex dry-run/progress/activation, version coexistence and a fixed bilingual evaluation set. Extended the Event Intelligence public submit/subject receipts with stable Claim/Evidence/Job filter metadata; no ORM or database was shared.

### Verification results

Event Intelligence Processor API: 3 passed and Ruff passed. Video Summary: 44 backend tests passed, including 8 stage-5 tests; compileall passed. The Alembic migration has a single declared head (`5a1c001007`) and Compose orders migration before Search services.

### Compatibility and rollback

The old `/search`, Event model/vector column and legacy chain remain intact. New `/api/v1/search` never falls back to them. Superseded model rows are retained. Disable the Search overlay to roll back without deleting data.

### Remaining deployment gates

Real PostgreSQL/pgvector upgrade passed at `5a1c001007` and created all six expected indexes. Before rollout, run representative HNSW/filter `EXPLAIN`, then fill human relevance and record Top-K for a representative authorized Evidence corpus. Docker daemon-backed validation was not claimed in the isolated test run.

### Next step

Stop after stage 5. Do not start SUMMARY-001. Stage 6 requires the real-database and relevance gates above plus separate authorization.

## 2026-08-24: SUMMARY-001～008 Summary migration

### Goal

Move Daily Summary from legacy Event enumeration to an application-owned, precomputed product capability based on Event Intelligence ReviewItem/Claim/Decision/Feedback public DTOs and Site local dates.

### Completed

Added the versioned `summaries` model and `6b1c001008` migration; Toronto/UTC/DST half-open bounds; canonical ReviewItem and Object deduplication; ended preference and missing Claim/Evidence degradation; explainable importance scoring and duplicate compression; deterministic Rule v1; structured-only LLM with character, Token and estimated Cost limits plus audited fallback; independent worker scheduling/manual rebuild; observable queued/running/ready/failed status; ready-only activation and supersede; and fixed legacy/Review comparison metrics and output hash.

Event Intelligence received only a backward-compatible public DTO extension (`review_item_id`, `site_id`, `camera_timezone`). No database, ORM, Frigate URL, Evidence source reference or media crossed the boundary. The old `/summary/*`, `daily_summaries` and Event chain remain unchanged for rollback.

### Verification

Video Summary full backend: 62 passed. Event Intelligence backend: 153 passed/3 skipped with explicit configured asyncio mode; Ruff passed for changed base files. Real PostgreSQL 16/pgvector migration reached `6b1c001008`; site-level NULL-camera uniqueness, idempotent queue identity, ready-only supersede and LLM-to-Rule fallback were exercised against the real database. Fixed comparison locks Review dedupe, coverage, Toronto bounds, highlight order and SHA-256 output stability.

### Exit and stop

All stage 6 exit conditions are met for the new v1 path. Existing stage-5 representative HNSW EXPLAIN/human relevance work remains a deployment/quality gate and was not reclassified. Stop after stage 6; do not begin CHAT-001～007 without separate authorization.
## 2026-08-24：CHAT-001～007 Chat 迁移

### 目标

在不读取旧 Event、不共享 Event Intelligence DB/ORM、不直连 Frigate/Evidence 的前提下，提供可审计、可降级的异步 Chat v1。

### 已完成

新增正规化 Message/Job migration、Site Timezone 时间解析、Search→Summary 检索流水线、Subject UUID 引用、独立 Chat Worker、安全边界和 Extractive 降级。旧链路未删除或切换。ADR 与阶段验收见 `architecture-reviews/2026-08-24-chat-worker-adr.md`、`chat-stage7-acceptance.md`。

前置门禁还暴露并修复了 OpenCLIP timeout 在 `asyncio.run` 关闭时等待默认 executor 的阻塞缺陷，以及 fresh Alembic 链缺少旧 `conversations` 父表的问题。

### 数据和契约变更

Video Summary Alembic head 为 `7c1c001009`。新增 `/api/v1/chat/jobs`、job poll 和 owner-scoped conversation read API。Event Intelligence 无代码或数据库变更；继续只消费其公开 v1 契约。

### 验证结果

固定问题集、注入/降级、引用、Schema、队列、隔离和 Search/Summary 回归测试通过；Video Summary 76 passed，Event Intelligence 153 passed/3 skipped。Alembic 离线全链 SQL、Compose 配置、变更文件 Ruff 和新模块 Mypy 校验通过；全模型 Mypy 仍有既有 SQLAlchemy 动态 Base 类型问题，未误报为通过。

### 故障测试

覆盖无效时区、语义向量不可用、LLM 不可用、Prompt Injection、空检索和 worker failure 状态。

### 兼容性影响

旧 `/chat` 和 JSON 消息保留作回退；阶段 8 前不切换 Web/Android。

### 已知限制

`owner_id` 只实施存储与查询隔离，不等同于生产认证；真实 Compose/外部模型成本需部署阶段验证。

### 回退方式

停止 Chat Worker，继续使用旧 Chat；数据库 downgrade 仅用于明确维护操作，本阶段未执行数据删除。

### 下一步

不自动开始阶段 8。其前置是 Chat Compose 集成门禁持续通过，并完成客户端认证/所有权设计。
