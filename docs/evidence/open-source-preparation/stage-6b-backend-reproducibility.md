# Stage 6B backend reproducibility verification

Date: 2026-09-19
Repository: Nanexus AI Video Summary
Scope: isolated Python/backend execution and verification only

## Result

Stage 6B **passes** after a bounded corrective re-verification. The intended public backend
candidate is reproducible, its locked installation succeeds, all 91 backend tests pass, a clean
PostgreSQL/pgvector database migrates to the expected head, the Stub API smoke test passes, and
the repository-defined Mypy check now passes in the documented static-check environment.

The original Mypy failure was retained and diagnosed rather than suppressed. Its environment
installed only the `test` extra even though Mypy intentionally scans optional OpenCLIP modules.
The correction composes the existing `test` and `openclip` extras for full static verification;
it changes no dependency metadata, lock resolution, runtime behavior, or CPU/GPU routing. Stage
6C was not started.

## Candidate construction and boundary

- Source branch and HEAD before construction: `main` at
  `da3b7c6eb32160d927ff5101194698478da8b2de`.
- The source index was empty; `git diff --cached --name-status` had no entries.
- The intentionally dirty source state matched the reviewed Stage 6A inventory, and
  `git diff --check` passed.
- A detached temporary worktree was created at the recorded HEAD. A binary-safe tracked patch
  was applied, then each of the 43 Stage 6A public-untracked paths was copied individually.
- Tracked-patch SHA-256:
  `e0f52240531852e2e8db9760f56a7b01b926c0080fc1132024ae59eb8869409a`.
- The pre-test candidate manifest covered 200 files: 138 unchanged HEAD files, 19 files whose
  content came from the tracked patch, and 43 allowlisted untracked files.
- Candidate-manifest SHA-256:
  `a3890fac42faf5b26e88118ae9a183d475c0ad71bfba0df65009006e8c8f0c0a`.
- Every manifest entry recorded origin, byte size, SHA-256, and candidate-relative path. A
  post-test verification found zero changes to those 200 source files.
- `.env`, private Stage 9 files, local Android configuration, caches, virtual environments,
  databases, logs, built mobile artifacts, and model artifacts were absent from the pre-test
  candidate. Generated test caches and the candidate-owned virtual environment remained
  disposable and outside the manifest.
- A content check found no original-worktree path, private-key marker, or AWS access-key-shaped
  value in the candidate source. The installed editable project pointed only to the detached
  candidate, never to the original worktree.

The corrective run reconstructed the candidate from the same baseline and tracked patch, plus
the 43 Stage 6A public paths and this existing Stage 6B evidence file as a 44th explicit public
path. Its pre-install manifest covered 201 files and had SHA-256
`34beccaefa67751ab2efc75852c38219db637708abea31e44aca29b131cfe740`.
Post-test verification found zero source-file changes and no model weights or private files.

## Toolchain and locked installation

- Python: `3.12.3`.
- uv: `0.11.7`.
- `pyproject.toml` SHA-256:
  `29b8e8e4d2d7c48a0ba6f3cc72cb544d2a6c19335ffc191d45185d96f1062b8b`.
- `uv.lock` SHA-256:
  `7dcc3cb59bb03d2d36a1bbd2cf90e8a9fdd1032b22f9b26e29d9e23803b9b81d`.
- `uv lock --check` passed before and after installation without changing either file.
- The original `uv sync --frozen --extra test` succeeded in a fresh candidate-owned `.venv` and
  cache, but did not provide the imports required by the configured Mypy scope.
- Corrective verification used the documented
  `uv sync --frozen --extra test --extra openclip`; it installed 64 compatible locked packages.
- Network access was required because the fresh cache did not contain all locked wheels. The
  first sandboxed attempt failed at DNS lookup for locked `psycopg==3.3.4`; the identical frozen
  command succeeded when public package-index access was allowed.
- `uv pip check` reported all 64 corrective-environment packages compatible. Ordinary package,
  configuration, OpenCLIP-provider, and Event Intelligence contract imports succeeded without
  a local Event Intelligence checkout.

## Static checks and tests

| Check | Result |
|---|---|
| `uv run --frozen ruff check .` | passed |
| `python -m compileall -q src services tests` | passed |
| initial `uv run --frozen mypy` with only the `test` extra | failed: 4 missing-import errors in 2 files |
| corrective `uv run mypy` with `test` and `openclip` extras | passed: no issues in 45 source files |
| `uv run --frozen pytest` | 91 passed, 0 failed, 0 skipped, 0 xfailed |

Mypy initially reported missing `open_clip` and `torch` implementations in
`src/nanexus/vision.py` and `src/nanexus/providers/openclip.py`. These are intentionally optional
runtime modules with lazy heavyweight imports, but Mypy intentionally checks all of `src` and
`services`. The packages already belong to the optional `openclip` extra and were absent only
because the Stage 6A command selected `test` alone.

The smallest honest correction is documentation: full static checks now install both existing
extras with frozen semantics. No blanket or targeted missing-import suppression was added, no
dependencies were duplicated into `test`, and `pyproject.toml` and `uv.lock` remained
byte-identical. Corrective imports confirmed `torch==2.13.0+cpu`,
`torchvision==0.28.0+cpu`, no CUDA build, and no available CUDA runtime. Installing the libraries
did not load a model or download weights. Linux CPU routing remains explicit; a future CUDA
profile remains separate and was neither implemented nor narrowed here.

The passing suite included configuration, OpenCLIP provider mocks, Event Intelligence
contracts/client behavior, compatibility/security, Summary, Search, Chat, API, queue, fixture,
and model-isolation/media/provider coverage. No model weights were downloaded and no real model
inference was run.

## Migration and Stub smoke verification

A new disposable `pgvector/pgvector:pg16` container was started with synthetic credentials and
an empty database. Alembic configuration loaded, declared `7c1c001009` as its single head, and
`alembic upgrade head` completed. The resulting database reported revision `7c1c001009`, the
`vector` extension, and six public tables. The container was stopped and auto-removed after the
checks.

The API was then started in Stub/rule/extractive modes against that disposable migrated
database. One synthetic Summary row exercised the local data path. Results were:

- `GET /health/live`: HTTP 200, alive;
- `GET /health`: HTTP 200, database true, Redis false, status degraded;
- `GET /api/v1/capabilities`: HTTP 200 with the versioned public capability contract;
- `GET /api/v1/summaries/2026-09-19`: HTTP 200 with the synthetic precomputed Summary;
- shutdown: application shutdown completed cleanly.

The degraded aggregate health result is expected for this bounded smoke because no Redis or
worker service was started. No camera, NVR credential, cloud key, Event Intelligence service,
GPU, model package extra, model cache, or model weight was used. Full Event Intelligence and
OpenCLIP CPU/GPU integration remain assigned to later Stage 6 work.

## Gate conclusion

Backend dependency installation, static checks, imports, tests, migrations, and Stub
startup/read behavior are reproducible from the isolated candidate and do not depend on private
workspace state. Mypy passes without suppressions in the documented frozen environment, lock
integrity is unchanged, and the CPU/GPU dependency boundary remains explicit. Stage 6B is
closed as **PASS**.
