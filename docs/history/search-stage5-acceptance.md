# Stage 5 Embedding and semantic Search acceptance

> **Historical evidence.** This dated acceptance record is retained for engineering context and
> does not describe the current project stage. See [`docs/architecture.md`](../architecture.md).

Date: 2026-08-24
Scope: SEARCH-001 through SEARCH-007. Storage decision: Video Summary owns the application-level pgvector table. Event Intelligence remains authoritative for subjects, claims, evidence and model invocations.

## Architecture and boundary

The external enrichment worker consumes only Processor API v1. Event Intelligence's backward-compatible submit receipt now returns persisted Claim and granted Evidence UUIDs, while Subject metadata exposes camera, site and occurrence time. No database, ORM, Frigate client or Evidence source reference crosses the repository boundary.

After a Caption result is durably accepted, Video Summary enqueues an `EmbeddingJob`. The embedding worker writes `embedding_records` in the Video Summary database. Failure retries independently and ends in a dedicated DLQ; it cannot roll back the authoritative Claim. Search API v1 calls the separate model service for text vectors and queries only `embedding_records`. Evidence links point back to the job-scoped Event Intelligence media API.

## SEARCH-001/002

Migration `5a1c001007` creates the versioned record, a fixed 512-dimension constraint, uniqueness/idempotency key, Subject and filter indexes, and HNSW cosine index. Dimension changes require a new additive migration and model version; never alter vectors in place. Production startup runs `alembic upgrade head` before API/worker startup.

## SEARCH-003/004/005

Index jobs include stable Subject revision, source Claim/Job IDs, Evidence IDs, model identity, content hash and filter metadata. Query inference is HTTP-only at `/v1/embeddings/text`; the API process remains free of torch/OpenCLIP. `/api/v1/search` supports camera, site, label, time range, Subject type, offset pagination and minimum similarity. A missing/unavailable model service returns an empty `semantic-unavailable` response with `degraded=true`; no legacy Event fallback occurs.

## SEARCH-006

`scripts/reindex_embeddings.py INPUT [--dry-run] [--activate]` imports public-flow JSONL jobs, reports plan/progress/completion, coexists by model version and marks the previous version superseded only after explicit activation. Superseded rows are retained for rollback; cleanup is a separately reviewed retention operation and this stage deletes nothing.

## SEARCH-007

`docs/search-evaluation/fixed-v1.json` fixes five Chinese and five English queries, Top-K, expected relevance labels, human relevance slots and dataset/model version. Human relevance remains empty until a site-specific labeled corpus is approved; repeatability/schema is automated, but no unsupported quality claim is made.

## Verification

- Event Intelligence Processor API: 3 passed; Ruff passed.
- Video Summary stage-5 tests: 8 passed.
- Video Summary full backend: 44 passed; compileall passed.
- API heavy-import isolation remains in the full suite.

## Exit assessment

All code-level exit conditions are met. Real PostgreSQL migration passed at `5a1c001007` with all six expected indexes. Query-plan EXPLAIN and daemon-backed bilingual relevance scoring require an available Docker daemon and representative labeled Evidence; these are deployment/quality gates, not replaced by SQLite or synthetic claims.
