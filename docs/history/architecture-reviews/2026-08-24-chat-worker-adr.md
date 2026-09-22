# ADR: Chat v1 asynchronous worker boundary

> **Historical architecture record.** Retained for the rationale behind the current design;
> [`docs/architecture.md`](../../architecture.md) remains authoritative.

Status: Accepted for stage 7 migration (2026-08-24).

## Decision

`POST /api/v1/chat/jobs` persists an owner-scoped user message and queues a UUID job. The API process never performs retrieval or invokes an LLM. `services.chat_worker` consumes the job, queries only Video Summary's versioned `EmbeddingRecord` and `Summary` application models, and persists a normalized assistant message. Clients poll the owner-scoped job endpoint.

Search embeddings originate from Event Intelligence public processor contracts. Summary inputs originate from Event Intelligence `/api/v1/events`. Chat does not import Event Intelligence ORM, share its database, read legacy `Event`, or access Frigate/Evidence. Stable citations are Event Intelligence subject UUIDs with the public relative review path `/api/v1/events/{subject_id}`.

## Security and failure behavior

Retrieved text is delimited as untrusted context. The system instruction forbids following context instructions or exposing prompts, credentials, tokens, internal URLs, or private reasoning. Input/context/output limits are configuration-owned. Prompt-injection markers force extractive mode. Missing model configuration, embedding failure, or LLM failure produces a structured, cited extractive answer with `degraded=true` and an auditable error code.

## Compatibility

Legacy `/chat` and its JSON conversation storage remain unchanged as rollback-only paths. No client is switched in this stage.
