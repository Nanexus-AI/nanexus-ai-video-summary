# Stage 9 Closeout Gate

This gate closes deployment evidence gaps before any shadow traffic or retirement action.

## Required evidence

1. Fresh database migration and upgrade from an explicitly identified previous release snapshot.
2. One-command integrated and existing-foundation Compose startup with dependency health.
3. Worker kill/restart with in-flight job durability, retry/DLQ and heartbeat recovery.
4. Incompatible required capability rejected before serving; optional capability safely degraded.
5. Real CPU OpenCLIP load, weight source/cache/SHA-256/license/resource/start-time record and end-to-end inference.
6. Deterministic Stub Demo on a clean GPU-free host with no cloud key or outbound model requirement.
7. Formal secret scan, dependency/license reports and SPDX or CycloneDX SBOM for both repositories and images where supported.
8. Independent clean builds of both repositories without relying on the other repository's uncommitted worktree.
9. Video Summary full-repository Mypy errors fixed or individually classified and explicitly approved; no blanket ignore.

## Prohibited actions

Do not run Shadow Validation, disable the old MQTT listener or workers, remove legacy API/DTO/UI/data/Compose, publish, push, tag, deploy publicly, create an external repository, upload weights, or begin Legacy Retirement.

## Following gates

After this gate passes: Shadow Validation → Cutover Rehearsal → Legacy Retirement/Data Disposition → Open-source Release Gate. Each requires a separate task and authorization.
