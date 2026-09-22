# CONTRACT-001 Architecture Gate

> **Historical architecture record.** Retained for engineering context; current architecture is
> documented in [`docs/architecture.md`](../../architecture.md).

Status: **APPROVED**
Date: 2026-08-21
Approver: Product owner
Review mode: read-only pre-review followed by explicit approval of all six recommendations.

## Approved decisions

1. Event Intelligence owns the normative, ORM-independent JSON Schema; consumers validate independently.
2. Processor Job v1 accepts only ended `review_item` subjects.
3. Jobs contain opaque Evidence IDs and metadata, never source URLs, credentials or internal paths.
4. Processors submit invocation facts; Event Intelligence will create authoritative ModelInvocation records in a later phase.
5. Processor Contract is transport-neutral and separate from internal Redis `StreamEnvelope`.
6. Contract `1.0` rejects incompatible majors and unknown enums; compatible additions require optional fields and capability negotiation.

## Allowed dependency direction

Only `Video Summary → Event Intelligence` through published, versioned contracts. Neither database/ORM sharing nor direct Frigate/Evidence access is permitted.

## CONTRACT-001 scope

The approved implementation covers only Processor Job v1 semantics, schema, runtime validation, unit tests and documentation. It does not authorize Result, Capability, permission APIs, shared fixtures, database migrations, ReviewItem runtime, Evidence API, queues, Workers, providers or OpenCLIP migration.

## Decision

CONTRACT-001 is authorized. CONTRACT-002 and later tasks require separate execution within their documented scope.
