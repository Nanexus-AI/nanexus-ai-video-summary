# Stage 9 Closeout execution record (2026-08-24)

## Decision

**Blocked: Stage 9 has not formally exited.** This run did not start Shadow Validation,
cut over MQTT, stop legacy runtime, retire legacy API/DTO/UI/data/Compose, publish, push,
tag, release, deploy publicly, create an external repository, or commit.

## Baseline and protected work

- Video Summary HEAD: `336a4061d13dc567ccec771d0922a355ae310c6a`.
- Event Intelligence HEAD: `89bbcd7c4eeb867bdef0c04827b50a6796679856`.
- The pre-existing modified Closeout documents in Video Summary and the four untracked
  Event Intelligence assets/documents were preserved. No Event Intelligence file changed.

## Evidence obtained

- Alembic unique heads: Video `7c1c001009`; Event `4b1f001006`. Full histories and
  offline SQL generation passed (144 and 442 lines respectively).
- Fresh source-built migration jobs completed before dependants in the isolated
  `nanexus-stage9-closeout` Compose project. Repeated migrations exited zero.
- Explicit prior states were created in retained `nanexus-stage9-upgrade` volumes:
  Video `6b1c001008`, Event `ff7f74e1aa8b`. Schema-only snapshots were saved as
  `/tmp/video-6b1c001008-schema.sql` (SHA-256
  `a739722568bba84216fda82e6513fb5561667e6f6a7d4ff3f8f85a2dc3141d5f`) and
  `/tmp/event-ff7f74e1aa8b-schema.sql` (SHA-256
  `e877e95dfed1df94c14b837e573b8868090778dc8376ae02ac1326eb9adb9998`), then upgraded
  to the current heads.
- Integrated Compose built all images from current source and became healthy with explicit
  HTTPS origins. The initial HTTP-origin run failed closed with
  `production requires HTTPS for PUBLIC_BASE_URL`. Static config for integrated and
  external-foundation overlays passed. External-foundation runtime was not completed.
- All four Video workers expired from readiness after stop while Event Intelligence health
  remained HTTP 200, then restored readiness after restart. Enrichment heartbeat was added.
- Embedding, Summary and Chat now use processing lists, explicit ACK and startup recovery.
  Real recovery probes logged one recovered in-flight job for each; Chat/Summary became
  `ready`, embedding persisted exactly one record, and all processing lists returned to zero.
- Deterministic no-cloud-key Stub runtime returned capabilities, empty Summary, deterministic
  Search, completed asynchronous extractive Chat, rejected an invalid bearer token, and
  remained ready. `/tmp/stage9-stub-demo.log` was checked for the known tokens, full probe
  queries, prompt markers and Evidence content; no match was found.
- CPU OpenCLIP built from the frozen lock and loaded on CPU. Image ID
  `sha256:93a4289970a79eb63d5faf3ea84e96e578923fcd8a49d30b13487975a089a397`, size
  2,872,386,544 bytes. Runtime was OpenCLIP 3.3.0, `ViT-B-32` / `openai`, CPU,
  512 dimensions. Cached weight upstream is
  `timm/vit_base_patch32_clip_224.openai@a6f597a30f7b82c51704746581f9a4e41421e878`,
  declared Apache-2.0, 605,143,284 bytes, SHA-256
  `e6d1bd7789aa45192b3bf90570a789b478bae1b74ebcce7eddd908e83a2b7c31` under the retained
  `nanexus-stage9-openclip-model-cache` volume. Two warm text embeddings were deterministic
  (response SHA-256 `7bc55c...2374c`), about 0.02 seconds each; observed memory was 1.028 GiB.
  A QuickGELU mismatch warning was emitted.
- Gitleaks v8.28.0 scanned both complete worktrees with `--no-git --redact`: no leaks found.
  Empty JSON reports are under `/tmp/nanexus-stage9-gitleaks/`, both SHA-256
  `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570`.
- Syft 1.51.0 generated SPDX JSON and CycloneDX JSON for both repositories under `/tmp`.
  `pip-licenses` 5.0.0 and `license-checker` 25.0.1 generated Python/npm reports under
  `/tmp`.
- Video backend: 90 passed; Ruff, compileall and full-repository Mypy passed (45 files).
  The prior nine Mypy errors were all disposed: seven safe local fixes and two precise
  third-party OpenCLIP `import-untyped` annotations. No blanket ignore or exclude was added.
- Event backend: 153 passed, 3 skipped. Sandbox execution hung in aiosqlite; the same frozen
  suite passed outside the sandbox. Event Web: 5 passed, lint and production build passed.
- Video Web: 3 passed; newly fixed ESLint Gate, typecheck and production build passed.
- Android Gradle 8.9/JDK 17: Debug and Release JVM tests, Debug/Release APK builds and
  Release lint passed. Release lint report is `android/app/build/reports/lint-results-release.html`.
- `git diff --check` passed. No Event Intelligence tracked file was modified.

## Blocking evidence gaps

1. CPU OpenCLIP media-image embedding through Event Intelligence Evidence and the final
   Search API was not completed; only real model load and text embedding were measured.
2. Exact cold-start/download and warm-start timings were not captured. The frozen Linux lock
   also pulls CUDA 13/NVIDIA packages into the CPU image, producing a 2.87 GB image. This is
   an unaudited CPU-profile/resource and license burden, not an accepted CPU-only profile.
3. License audit is not clean. Syft reports 101 Video and 62 Event packages as `NOASSERTION`;
   pip-licenses reports 34 Video and 27 Event `UNKNOWN` metadata results. Gradle and container
   base-package license reports were not completed. Unknown licenses block this gate.
4. External-foundation Compose was config-validated but not run end to end against a separately
   installed compatible foundation.
5. Independent clean build contexts excluding the opposite repository's uncommitted worktree
   were not completed.
6. The four-worker runtime drill proved heartbeat expiry/recovery and processing-list durability
   for embedding/summary/chat. A real queued and in-flight enrichment Processor Job kill/restart,
   with attempt/retry/DLQ timing captured from Event Intelligence persistence, remains outstanding.
7. Container image SBOMs, formal Gradle dependency licenses, complete negative capability matrix
   runtime, and exact retry/recovery latency table remain outstanding.

## Rollback and retained test data

Code rollback is removal of the uncommitted Closeout changes. Runtime rollback remains the
unchanged legacy API/client/worker/Compose path. Test projects were stopped, not removed; their
named database, Redis and model-cache volumes were retained and no user volume was deleted.

Shadow Validation remains prohibited until every blocking item above is closed and this record
is replaced by a complete passing decision.
