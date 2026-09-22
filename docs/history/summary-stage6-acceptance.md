# Stage 6 Summary migration acceptance

> **Historical evidence.** This dated acceptance record is retained for engineering context and
> does not describe the current project stage. See [`docs/architecture.md`](../architecture.md).

Date: 2026-08-24
Scope: SUMMARY-001 through SUMMARY-008

## Preconditions verified

Both repositories were inspected independently. Stage 1 contracts, Foundation, cross-repository slice, Model Provider and Search code/acceptance artifacts exist. Event Intelligence remains authoritative for ReviewItem, Evidence, Claim, ModelInvocation, Decision and Feedback. Video Summary owns its embedding and Summary tables. The pre-existing Event Intelligence untracked assets/document were not modified.

Stage 5's real PostgreSQL/pgvector migration was already recorded as passed. Representative HNSW EXPLAIN and human relevance labeling remain deployment/quality gates; they neither authorize a Search quality claim nor force Summary to use the legacy Event table.

## SUMMARY-001/002

Migration `6b1c001008` creates application-owned, versioned `summaries` with all planned fields, status and lookup indexes. The generation identity uses PostgreSQL `NULLS NOT DISTINCT`, so a site-wide `camera_id=NULL` result is idempotent. Local day conversion uses IANA timezone data and half-open UTC bounds; UTC, Toronto summer, 23-hour spring DST and 25-hour fall DST cases are fixed tests.

## SUMMARY-003/004/005

The public Event list deduplicates source Review lifecycles; Video Summary additionally deduplicates by canonical `review_item_id`, prefers ended revisions, deduplicates Object keys, preserves all Subject/Claim IDs and tolerates missing Claims/Evidence. Importance is deterministic and traceable across Decision, Feedback, Label, Zone, Duration, local time and Claim quality. Equivalent highlights are compressed while review coverage remains explicit. Rule v1 is offline and output-stable.

## SUMMARY-006/007

LLM receives only serialized structured Review/Claim Context—never media, URLs or source credentials. Invocation metadata records prompt/model/provider/timestamps and enforced input-character, output-Token and estimated worst-case Cost budgets. Budget, configuration or provider failure returns the Rule summary.

The independent Summary Worker calls Event Intelligence public HTTP APIs, applies Site/Camera filters and local UTC bounds, then persists locally. Manual v1 rebuild only queues work; API reads ready precomputed results and exposes job status. Generation identity is idempotent. A prior active version is superseded only after a new result is ready; no Summary is overwritten or deleted.

## SUMMARY-008 and verification

The fixed migration Fixture compares legacy duplicate count/coverage/UTC day with Review duplicate count/coverage/Toronto day, highlight order and deterministic output SHA-256. Expected Review output hash is `3e23d38df2eeeae42b471348dd1d51600e4dfed146805e5d7157d0ae2c816c36`.

- Video Summary: 62 passed; compileall and changed-file Ruff F/I checks passed.
- Event Intelligence: 153 passed, 3 skipped; changed-file Ruff passed.
- PostgreSQL 16/pgvector: migration head `6b1c001008`; duplicate NULL-camera identity rejected; persistence/idempotency/supersede/fallback smoke passed.

## Exit assessment

- New Summary v1 does not query the legacy Event table.
- ReviewItem deduplication and Site Timezone semantics are enforced.
- Rule mode is fully offline; LLM failure is safe.
- API reads precomputed v1 results and does not invoke Event Intelligence or LLM synchronously.
- Every ready Summary records all source Subject IDs, source Claim IDs in structured content, and generator/model/prompt versions.

Stage 6 is complete. Legacy endpoints remain for rollback. No publish, push, client cutover, old-chain deletion or stage 7 work was performed.
