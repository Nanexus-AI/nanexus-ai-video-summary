# Stage 6A reproducibility baseline and verification plan

Date: 2026-09-19
Repository: Nanexus AI Video Summary
Discipline: Task -> Evidence -> Review -> Gate -> Preserve
Scope: planning and read-only inspection only; Stage 6B has not started

## Executive summary

Gate 5 has passed. Stage 6A establishes a sanitized baseline and a reproducible plan for
backend, Web, Android, Docker/Compose, model, and cross-repository verification. No commit,
staging operation, dependency change, model download, broad integration run, or Event
Intelligence change was made.

The source worktree is intentionally dirty and contains the intended public changes as well
as ignored private Stage 9 material. Verification must therefore not run directly in this
worktree. The recommended candidate is a detached temporary worktree at the recorded HEAD,
with the reviewed tracked diff applied and only explicitly allowlisted untracked public files
copied into it. Ignored files are excluded by construction. A candidate manifest and hashes
make the result repeatable without creating a commit.

The present Linux Python resolution is demonstrably CPU-only. An NVIDIA PCI device is visible,
but the driver is not usable from this environment and the installed Torch has no CUDA build.
CPU success therefore cannot satisfy the GPU gate. CUDA dependency routing and real RTX 5060
Ti inference remain independent Stage 6F work.

## Environment baseline

### Repository identity and state

- Branch: `main`
- Exact HEAD: `da3b7c6eb32160d927ff5101194698478da8b2de`
- Staged state: empty (`git diff --cached --name-status` produced no entries)
- `git diff --check`: passed with no whitespace errors
- Working tree: intentionally dirty; no baseline cleanup was attempted

Tracked modifications:

```text
.env.example
.gitignore
README.md
compose.model.yaml
compose.release.yaml
compose.search.yaml
compose.slice.yaml
docker-compose.yml
docker/mosquitto/mosquitto.conf
docs/architecture.md
docs/resource-profiles.md
pyproject.toml
scripts/benchmark_openclip_cpu.py
src/nanexus/config.py
src/nanexus/event_intelligence_contracts/__init__.py
src/nanexus/providers/openclip.py
tests/test_config.py
tests/test_openclip_provider.py
uv.lock
```

Tracked deletions consist of the former root-level development/acceptance/history documents
being consolidated into the public documentation set and `docs/history/`. They are:

```text
docs/android-dev-machine.md
docs/architecture-reviews/2026-08-21-contract-001-gate.md
docs/architecture-reviews/2026-08-21-contract-002-005-gate.md
docs/architecture-reviews/2026-08-21-foundation-001-006-gate.md
docs/architecture-reviews/2026-08-21-model-001-006-gate.md
docs/architecture-reviews/2026-08-21-slice-001-005-gate.md
docs/architecture-reviews/2026-08-24-chat-worker-adr.md
docs/architecture-reviews/2026-08-24-client-stage8-adr.md
docs/baseline-acceptance.md
docs/chat-stage7-acceptance.md
docs/client-stage8-acceptance.md
docs/compatibility-matrix.md
docs/deployment-security-runbook.md
docs/development-progress.md
docs/event-intelligence-migration-development-plan.md
docs/m0-implementation.md
docs/m1-implementation.md
docs/m2-implementation.md
docs/rough_idea.txt
docs/search-stage5-acceptance.md
docs/stage9-acceptance.md
docs/stage9-closeout-acceptance.md
docs/stage9-closeout-plan.md
docs/summary-stage6-acceptance.md
docs/technical-assessment-and-migration-reference.md
```

Untracked public-candidate material is listed completely below. Each path must be placed on the
candidate allowlist individually; directory-level wildcard copying is prohibited.

```text
CONTRIBUTING.md
LICENSE
SECURITY.md
docs/android.md
docs/deployment.md
docs/development.md
docs/evidence/open-source-preparation/README.md
docs/evidence/open-source-preparation/stage-0-repository-baseline.md
docs/evidence/open-source-preparation/stage-1-dirty-tree-classification.md
docs/evidence/open-source-preparation/stage-2-public-exposure-audit.md
docs/evidence/open-source-preparation/stage-3-licensing-audit.md
docs/evidence/open-source-preparation/stage-4a-license-and-provenance.md
docs/evidence/open-source-preparation/stage-4b-personal-network-sanitization.md
docs/evidence/open-source-preparation/stage-4c-trusted-network-security.md
docs/evidence/open-source-preparation/stage-4d-event-intelligence-portability.md
docs/evidence/open-source-preparation/stage-4e-ignore-and-evidence-boundary.md
docs/evidence/open-source-preparation/stage-5a-documentation-inventory.md
docs/evidence/open-source-preparation/stage-5b-readme-refresh.md
docs/evidence/open-source-preparation/stage-5c-core-technical-docs.md
docs/evidence/open-source-preparation/stage-5d-security-contributing-android.md
docs/evidence/open-source-preparation/stage-5e-historical-doc-cleanup.md
docs/evidence/open-source-preparation/stage-5f-full-documentation-review.md
docs/evidence/open-source-preparation/stage-6a-verification-plan.md
docs/history/README.md
docs/history/architecture-reviews/2026-08-21-contract-001-gate.md
docs/history/architecture-reviews/2026-08-21-contract-002-005-gate.md
docs/history/architecture-reviews/2026-08-21-foundation-001-006-gate.md
docs/history/architecture-reviews/2026-08-21-model-001-006-gate.md
docs/history/architecture-reviews/2026-08-21-slice-001-005-gate.md
docs/history/architecture-reviews/2026-08-24-chat-worker-adr.md
docs/history/architecture-reviews/2026-08-24-client-stage8-adr.md
docs/history/baseline-acceptance.md
docs/history/chat-stage7-acceptance.md
docs/history/client-stage8-acceptance.md
docs/history/development-progress.md
docs/history/event-intelligence-migration-development-plan.md
docs/history/m0-implementation.md
docs/history/m1-implementation.md
docs/history/m2-implementation.md
docs/history/search-stage5-acceptance.md
docs/history/summary-stage6-acceptance.md
docs/history/technical-assessment-and-migration-reference.md
tests/smoke/openclip_gate_mock_frigate.py
```

Ignored/private or generated material observed:

- private configuration: `.env`, `android/local.properties`;
- private Stage 9 material: `compose.cpu-openclip-gate.yaml`,
  `docs/stage9-closeout-prompt.md`, `docs/stage9-cpu-openclip-closeout-prompt.md`, and
  `docs/stage9-cpu-openclip-closeout-acceptance.md`;
- environments/caches: `.venv/`, Python bytecode, `.mypy_cache/`, `.pytest_cache/`,
  `.ruff_cache/`, Android `.gradle/` and `.idea/`, and package metadata;
- generated outputs/state: `android/app/build/`, `web/dist/`, `web/node_modules/`, Web
  TypeScript build metadata, and `data/`.

The named private Stage 9 files were verified with `git check-ignore -v`. They remain ignored.
The status inventory contains no staged files. Raw `git status --ignored` output is not copied
as a public artifact because later runs may contain private local names.

### Toolchain

| Surface | Observed baseline | Interpretation |
|---|---|---|
| Python | 3.12.3 (system and project virtual environment) | Within `>=3.12,<3.13` |
| uv | 0.11.7 | Available |
| Node.js | v22.23.2 | Available; newer patch than documented 22.14.0 baseline |
| npm | 10.9.8 | Available |
| Java | Temurin OpenJDK 17.0.20 | Matches JDK 17 requirement |
| Gradle | Wrapper declares 8.9 | Wrapper execution could not acquire its user-cache lock in the read-only inspection sandbox; verify in the disposable candidate |
| Docker | 29.1.3 | CLI available |
| Compose plugin | unavailable through `docker compose` | The Docker CLI does not expose the plugin |
| Standalone Compose | v2.32.4 (`docker-compose`) | Available fallback; Stage 6 must test the documented command form or record an approved substitution |
| NVIDIA hardware | NVIDIA PCI display device visible; task target is RTX 5060 Ti 16 GB | Hardware enumeration only |
| NVIDIA driver | `nvidia-smi` cannot communicate with driver | GPU gate cannot run in current state |
| Project Torch | 2.13.0+cpu | CPU build |
| Torch CUDA build | none | Current environment cannot validate CUDA |
| CUDA runtime availability | false; 0 Torch CUDA devices | GPU gate not satisfied |

No secret values, environment contents, private network addresses, complete local paths outside
the approved repository relationship, or raw runtime logs are preserved here.

## Selected clean-candidate strategy

### Recommendation

Use a detached temporary Git worktree at the recorded HEAD, then materialize the intended
uncommitted candidate with two reviewed inputs:

1. a binary-safe patch of all tracked changes relative to the recorded HEAD; and
2. an explicit, line-by-line allowlist of untracked public-candidate files.

Generate a manifest containing candidate-relative path, origin (`HEAD`, tracked patch, or
allowlisted untracked), size, and SHA-256. Store raw patch/manifests outside the repository;
only a reviewed, sanitized summary may later be promoted as public evidence.

### Controlled procedure for Stage 6B

1. Reconfirm branch, HEAD, staged state, `git status --short`, and `git diff --check` in the
   source worktree. Stop if they differ from the approved baseline until the allowlist is
   reviewed again.
2. Create a temporary directory with restrictive permissions outside the repository.
3. Create a detached worktree at the exact HEAD. Do not use the current index as candidate
   state and do not create a branch or commit.
4. Export the tracked binary-safe diff to the restricted temporary area and apply it in the
   detached worktree. Confirm the applied name/status set equals the approved tracked list.
5. Copy each approved untracked file individually. Reject symlinks, device files, absolute
   paths, path traversal, and any path absent from the allowlist.
6. Assert that every candidate path is either tracked at HEAD, changed by the reviewed patch,
   or individually allowlisted. Assert that no ignored source-worktree path was copied.
7. Scan names, types, and content for `.env`, credentials, local infrastructure identifiers,
   logs, DBs, media, model artifacts, caches, APK/AAB files, and raw evidence before tests.
8. Record the manifest/hash and use that immutable candidate directory for each test run, or
   recreate it from the same inputs for a clean surface-specific run.
9. Remove the detached worktree with Git's worktree command and delete only the explicitly
   recorded temporary directory after evidence review. Never clean or reset the source tree.

This is safer than a plain temporary worktree, which would omit intended uncommitted changes;
safer than `git archive`, which has the same omission and loses useful Git-state auditing; and
safer than a clone after a local commit, which violates Stage 6A and introduces an unnecessary
publication-like commit. It preserves Stage 9 work, excludes ignored material by construction,
and is repeatable and disposable.

## Verification matrix

| Area | Candidate setup and commands | Evidence | Pass condition | Planned stage |
|---|---|---|---|---|
| Candidate | Recreate detached candidate; compare manifest/hash; run status and pollution checks | Sanitized manifest summary and command exit codes | Exact intended public candidate, no ignored/private input | 6B preflight |
| Backend install/lock | `uv lock --check`; clean `uv sync --frozen --extra test` in candidate-owned cache/venv | Versions, exit codes, lock checksum | Lock current; frozen sync succeeds without changing lock/source | 6B |
| Backend static | `uv run ruff check .`; `uv run mypy` | Sanitized summaries and exit codes | Both succeed | 6B |
| Backend unit/contracts | `uv run pytest`; retain aggregate counts, not raw payloads | Test counts and exit code | All required tests pass; approved exception is explicit | 6B |
| Backend migration | Fresh disposable PostgreSQL; `uv run alembic upgrade head`; optionally downgrade/upgrade only if migrations claim it | Revision before/after, exit code | Fresh schema reaches head with no private data | 6B |
| Backend smoke | Stub only; synthetic input; API liveness/capability/summary/search/chat checks | Redacted endpoint/status matrix | Deterministic supported path completes | 6B |
| Web install | In clean candidate: `npm ci` | npm/lock checksum and exit code | Exact lock install succeeds without lock mutation | 6C |
| Web checks | `npm run typecheck`; `npm run lint`; `npm test`; `npm run build` | Test counts, exit codes, dist inventory | All succeed; output remains disposable | 6C |
| Android setup | JDK 17, SDK 35, candidate-owned `GRADLE_USER_HOME`; inspect tasks | Tool versions and task inventory | No private SDK/signing values beyond ordinary local SDK discovery | 6C |
| Android checks | `./gradlew --no-daemon clean testDebugUnitTest lintDebug assembleDebug` (use actual defined lint task) | Exit codes, test/lint summaries, APK metadata only | Clean debug build succeeds without signing secrets; tests/lint pass | 6C |
| Compose render | Use sanitized ephemeral env/secrets; `config --quiet` for base, release Stub, integrated, external, slice, search/model combinations that documentation supports | File/profile matrix and exit codes | Every documented combination renders; no secret printed | 6D |
| Container builds | Build source images for supported initial profiles; no publication/push | Image IDs/digests and exit codes | Required builds succeed from candidate | 6D |
| Startup/health | Start base infrastructure and release Stub; check migrations, health, API and Web; matched `stop`/`down` cleanup | Sanitized service/health matrix | Required profiles start healthy and stop cleanly | 6D |
| Event integration | Synthetic fixture through Event Intelligence public v1 into Video Summary Stub and clients | Contract versions, opaque synthetic IDs, result assertions | Full public-boundary flow succeeds without shared DB/source imports | 6E |
| OpenCLIP Stub | No model extras/cache; deterministic provider and service path | Provider identity, deterministic result, zero model files | Supported no-model path passes | 6F |
| OpenCLIP CPU | Fresh CPU extra/profile, isolated cache, synthetic image/text inference | Torch build, device, model tuple, timing range, output shape/assertions, cache inventory | Actual CPU inference succeeds under documented CPU routing | 6F |
| OpenCLIP GPU | Separate CUDA dependency/image route plus GPU exposure and synthetic inference | Driver/runtime/Torch matrix, CUDA device, VRAM, actual inference result | Actual inference executes on CUDA; CPU fallback is forbidden | 6F |
| Public boundary | Audit source and candidate after every row | Before/after manifests and classifications | No private/generated artifact enters candidate source | Every stage |

## Backend plan

Use a fresh candidate-owned virtual environment and caches, never the source worktree `.venv`.
First prove the lock is current without rewriting it, then use frozen synchronization. Record
the Python/uv versions and hashes of `pyproject.toml` and `uv.lock`. Run Ruff, Mypy, the complete
pytest suite, and contract tests. Any skipped or xfailed test must be enumerated and reviewed;
an unexpected skip is not a pass.

For database verification, start an empty disposable PostgreSQL/pgvector instance with
synthetic credentials, apply `alembic upgrade head`, and verify the reported head. Do not use
or copy a local application database. Run Stub smoke checks with synthetic records against
`/health/live`, `/health`, `/api/v1/capabilities`, Summary, Search, and asynchronous Chat where
the current topology supports them. Preserve only aggregate and assertion-level evidence.

## Web plan

Remove/recreate only candidate-local `web/node_modules` and `web/dist`, run `npm ci`, and assert
that `package-lock.json` remains byte-identical. Run typecheck, lint, Vitest, and the production
build. Inspect the built asset inventory for source maps, embedded secrets, absolute local
paths, private origins, and unexpected large/binary assets. The build output is reproducible
disposable output and must not be copied back to source or published automatically.

For the integration slice, point the Web client only at the synthetic Video Summary API. Check
capability negotiation and visible Summary/Search/Chat states without retaining screenshots
that include internal URLs or tokens.

## Android plan

Use JDK 17, Android SDK 35, and Gradle wrapper 8.9 with a candidate-owned Gradle cache. The
local `android/local.properties` must not be copied; an ordinary developer may create a local
SDK locator or set the standard SDK environment outside Git. Inspect the Gradle task graph and
run the defined debug unit test, debug lint, and debug assembly tasks after `clean`.

Pass requires `assembleDebug` without a keystore, signing password, private endpoint, or other
project-specific secret. Confirm the debug artifact is signed only with the normal generated
debug key, remains outside Git, and contains no private configuration. Release signing and
APK/AAB publication are outside this source-first gate. Client contract tests must confirm v1
capability, Summary, Search, Chat, and subject-link expectations. An emulator UI check is useful
only against the synthetic API and is supplemental to the normal developer-build gate.

## Docker and Compose plan

Use a unique temporary Compose project name, candidate-owned bind paths, synthetic credentials,
temporary secret files, and loopback-only published ports. Never render configuration to a
public evidence file because rendered output may contain substituted secrets. Record only
profile/file names, exit status, and sanitized structural assertions.

Validate separately:

- `docker-compose.yml` local infrastructure;
- `compose.release.yaml` with Stub defaults and required ephemeral secrets;
- the `integrated` release profile with the approved sibling Event Intelligence candidate;
- release plus `compose.external-event.yaml` against an isolated synthetic external service;
- `compose.slice.yaml` as the cross-project synthetic harness;
- migration-era search/model overlays only in their documented combinations, not as arbitrary
  all-file merges.

Build required source images without pushing. Start the Stub release topology, wait for DB,
Redis, model service, API, and Web health; verify migrations completed; query liveness and
capabilities; then stop with the exact same file/profile/project arguments. After evidence is
reviewed, remove only volumes bearing the unique test project label. Preserve failure logs in a
restricted temporary evidence area, sanitize summaries, then destroy raw logs.

The missing `docker compose` plugin is a tooling issue to resolve before executing documented
commands. Standalone Compose v2.32.4 may be tested as an explicit compatibility path, but its
success alone does not silently prove the documented plugin command.

## OpenCLIP verification design

### 1. Stub/no-model

- Requirements: base locked dependencies only; `MODEL_PROVIDER=stub`; no OpenCLIP extra,
  weight volume, GPU, network model access, or cache reuse.
- Command/profile: backend provider tests plus release/model service with
  `MODEL_BUILD_PROFILE=stub MODEL_PROVIDER=stub AI_DEVICE=cpu`.
- Evidence: installed-package assertion excluding model packages where applicable, health,
  provider identity, deterministic synthetic output, and before/after model-file scan.
- Pass: deterministic service and worker flow succeeds and no weight/cache appears.
- Failure class: application/configuration or Stub packaging defect; never classify as a model
  or GPU limitation.

### 2. CPU OpenCLIP

- Requirements: Python 3.12; frozen `test` and `openclip` extras; Linux CPU-index Torch route;
  sufficient CPU/RAM/disk; isolated model cache; reviewed synthetic image/text fixture; outbound
  access only for an explicitly approved first acquisition.
- Command/profile: provider tests, model-service health, and the documented CPU benchmark/gate
  using `MODEL_PROVIDER=openclip AI_DEVICE=cpu` and the matched
  `ViT-B-32-quickgelu`/`openai` tuple. Re-run offline from the isolated cache to distinguish
  acquisition from inference reproducibility.
- Evidence: lock hashes, package versions and index origin, `torch.__version__`, CUDA-build
  field, selected device, model/pretrained tuple, weight identity/hash and license review note,
  output dimensions/finite values and semantic assertions, bounded timing/resource summary,
  and cache inventory. Do not preserve weights publicly.
- Pass: actual inference runs on CPU under the documented dependency profile, returns valid
  expected-shape outputs for synthetic inputs, and the offline rerun succeeds from the
  controlled cache.
- Failure classes: dependency/lock, weight acquisition/provenance, unsupported model tuple,
  resource exhaustion/performance, inference correctness, or cache isolation. CPU success has
  no bearing on CUDA.

### 3. GPU/CUDA OpenCLIP

- Requirements: working NVIDIA driver for RTX 5060 Ti 16 GB; compatible CUDA runtime/container
  toolkit where used; a separately resolved CUDA-enabled Torch/torchvision route; GPU device
  exposure; same reviewed model/fixture; isolated cache. Do not mutate the CPU lock/profile in
  place.
- Expected command/profile: a Stage 6F-approved CUDA dependency or image profile with
  `MODEL_PROVIDER=openclip AI_DEVICE=cuda`, followed by explicit device assertions and the same
  provider/model-service inference exercised by CPU. Exact install/profile commands cannot be
  finalized until dependency routing is corrected and reviewed in Stage 6F.
- Evidence: GPU model and VRAM, sanitized driver/CUDA versions, container GPU visibility if
  applicable, CUDA-enabled Torch build, `torch.cuda.is_available() == true`, selected device,
  tensor/model device assertions, peak allocated VRAM, model tuple, output assertions, and
  proof that inference did not fall back to CPU. Preserve no weight.
- Pass: CUDA routing resolves reproducibly and actual OpenCLIP inference completes on the GPU.
- Failure classes: host driver, container toolkit/device exposure, architecture/wheel support,
  dependency routing, CUDA/Torch ABI, out-of-memory, inference correctness, or impermissible CPU
  fallback. Environment failures are not application passes.

Stage 6F must test/correct Linux CUDA package routing, lock/profile separation, container GPU
declaration, driver/runtime compatibility with this GPU generation, explicit no-fallback
behavior, and documentation. Current facts (`torch 2.13.0+cpu`, no CUDA build, driver
unavailable) are a negative preflight result, not a GPU product verdict and not authorization
to change dependencies in Stage 6A.

## Event Intelligence cross-repository integration plan

Baseline relationship:

- Event Intelligence local checkout: sibling repository on branch `main`, inspected HEAD
  `89bbcd7c4eeb867bdef0c04827b50a6796679856`;
- transport boundary: public v1 HTTP only;
- normative interaction: capability negotiation, processor jobs, job-scoped subject/evidence,
  result submission, and public event reads;
- prohibited coupling: runtime source import, shared database, internal Redis keys, private
  camera endpoints, or real household data.

Required services are Event Intelligence PostgreSQL, Redis, migration, API and pipeline worker;
the reviewed synthetic Frigate endpoint/fixture seeder; Video Summary PostgreSQL, Redis,
migration, Stub model service, enrichment/embedding/summary/chat workers, API; and Web for a
client-visible check. Android may be checked against the same API but is not required in
addition to Web for the end-to-end visible-result assertion.

Startup and verification order:

1. Materialize independently reviewed clean candidates for both repositories. Record both
   exact revisions/manifests. Use the existing sanitized Event Intelligence
   `fixtures/frigate/0.17/vehicle-lifecycle` fixture and Video Summary smoke scripts only after
   confirming hashes and `contains_secrets=false`; use no real media.
2. Create isolated network, project name, synthetic credentials, and separate empty databases.
3. Start databases/Redis; require their health checks.
4. Run Event Intelligence and Video Summary migrations; require successful one-shot exit and
   head revisions.
5. Start the synthetic Frigate endpoint and seed the reviewed fixture through Event
   Intelligence's own ingest path.
6. Start Event Intelligence API and pipeline; require `/api/v1/health`. Authenticate with a
   temporary service token and validate `/api/v1/processor/capabilities`: capability contract,
   processor contract and enrichment-result versions must include `1.0`, with required claim
   writeback/model-invocation features.
7. Start Video Summary Stub model service and workers. Its integration worker must acquire the
   processor job, read only granted subject/evidence endpoints, and submit a v1 result. Assert
   idempotency on a repeat/poll and confirm Event Intelligence accepted the result.
8. Start Video Summary API and require `/health/live`, `/health`, and `/api/v1/capabilities`.
   Build/derive Summary and embeddings as supported; verify synthetic subject visibility,
   Summary, Search result/citation, and asynchronous Chat result via the Video Summary API.
9. Start Web and verify capability negotiation plus a visible synthetic Summary/Search/Chat
   result and safe subject link. Optionally run the same capability/client assertion on an
   Android emulator.
10. Negative compatibility checks: incompatible major/version is rejected; missing capability
    fails closed when enabled; unknown additive fields within v1 remain tolerated where the
    contract permits; credentials/source URLs/chain-of-thought never appear in schemas or
    responses.

Capture only both candidate identities, fixture hashes, contract version matrix, service health
states, opaque synthetic identifiers, aggregate job/result assertions, Web assertion outcome,
and exit codes. Do not capture bearer tokens, rendered environment, raw evidence bytes, full
logs, DB dumps, internal addresses, or screenshots containing infrastructure details.

Shutdown in reverse order using the exact Compose project/files/profile: clients and Video
Summary workers/API, Event Intelligence workers/API, then infrastructure. Export no databases.
After review, remove only the uniquely labeled test containers/networks/volumes, temporary
secrets, raw logs, fixture copies, and candidate caches. Confirm both source repositories are
unchanged.

## Pollution-prevention rules

Run verification only in disposable candidates with test-specific cache/data directories.
Before and after every matrix row:

1. capture sanitized `git status --short` for both the source and candidate;
2. compare the complete candidate filesystem inventory against its pre-task manifest;
3. inspect new untracked and ignored files (`git status --ignored --short` locally; do not
   publish unsanitized output);
4. scan for model extensions (`*.ckpt`, `*.onnx`, `*.safetensors`, `*.pt`, `*.pth`), common
   model caches, logs, DB/SQLite files, coverage, APK/AAB, Web `dist`, `.env*`, raw evidence,
   screenshots, media, and build/cache directories;
5. check tracked-file hashes and `git diff --check`; a test must not rewrite locks or source;
6. classify every new path before cleanup or preservation.

Classification:

| Class | Examples | Handling |
|---|---|---|
| Reproducible disposable output | virtualenv, `node_modules`, Web dist, Gradle/build trees, APK, images, containers/volumes, test DB | Keep only through review, then delete from the explicitly scoped candidate/test project; never copy to source |
| Private/raw evidence | logs, rendered Compose, tokens, DB dumps, model weights/caches, runtime media, benchmark raw data, screenshots with topology | Restrict permissions, sanitize a minimal summary, then destroy; never commit |
| Public sanitized evidence candidate | version/exit-code matrix, aggregate test count, contract/version assertion, reviewed manifest summary | Human review for secrets, paths, licensing, accuracy, and necessity; separate approval before any source addition |

No runtime-generated artifact is promoted automatically. A passing test does not change the
classification. Any unexplained new source-worktree path or tracked diff stops the gate. Cleanup
must target only recorded temporary paths and unique Compose resources; never use a broad Git
clean/reset or broad recursive deletion.

## Overall pass/fail criteria

- Backend passes only when frozen reproducible installation, lock check, lint, type checking,
  tests, required migrations, and Stub smoke path succeed, or a narrowly documented exception
  is explicitly reviewed and approved.
- Web passes only when a clean `npm ci` leaves the lock unchanged and typecheck, lint, tests,
  and production build succeed.
- Android passes only when the clean JDK 17/SDK 35 debug workflow, unit tests, lint, and build
  succeed without private signing secrets or repository-local private configuration.
- Docker passes only when every documented supported file/profile combination renders, required
  source images build, and supported Stub/integration profiles start healthy and stop cleanly.
- Integration passes only when Event Intelligence and Video Summary negotiate and complete the
  intended public v1 flow using reviewed synthetic data, followed by a Video Summary API and
  Web or Android-visible result, with no private camera/home dependency or cross-repository
  internal coupling.
- CPU passes only when real OpenCLIP CPU inference succeeds under the documented CPU dependency
  profile with controlled weight/cache handling.
- GPU/CUDA passes only when CUDA dependency routing is reproducible and real inference is proven
  on the RTX 5060 Ti independently. CPU success or mere GPU enumeration is insufficient.
- Public-boundary passes only when before/after manifests prove that private/generated/runtime
  material did not enter the public candidate and no source worktree was polluted.

Overall Stage 6 passes only if all required surface gates pass. Any failed required gate,
unexplained exception, missing CUDA proof, cross-boundary coupling, secret/private exposure, or
candidate pollution is a Stage 6 failure or explicit gate hold—not a partial pass.

## Deferred issues and risks

- CUDA dependency routing is intentionally CPU-oriented on Linux and must be designed, reviewed,
  and verified in Stage 6F; it must not replace or weaken the reproducible CPU profile.
- The NVIDIA device is visible at PCI level, but the driver is unavailable in the current
  environment. Host remediation or a suitable validation host is required before the GPU gate.
- The documented `docker compose` plugin is missing although standalone Compose v2 is present.
  Command compatibility and the intended prerequisite need resolution before Docker execution.
- Gradle 8.9 is declared, but wrapper execution was blocked by the read-only inspection sandbox's
  inability to create a user-cache lock. A candidate-owned writable Gradle cache must verify it.
- Node is v22.23.2 while documentation names 22.14.0 as the validated baseline. Stage 6 should
  either test the exact declared baseline as well or clarify the supported Node 22 range.
- Model download provenance, weight terms, checksum capture, offline cache behavior, and cleanup
  require explicit human review during model gates; no download was performed in Stage 6A.
- The candidate contains substantial uncommitted moves/additions. The per-file allowlist is a
  critical control and must be regenerated if source status changes.
- Event Intelligence integration is pinned here only for baseline reproducibility. Compatibility
  must be asserted through contracts, not assumed from sibling location or branch name.

## Gate recommendation

**Stage 6A: PASS.** The environment, dirty-tree boundary, clean-candidate strategy, verification
matrix, independent CPU/GPU gates, synthetic cross-repository plan, pollution controls, and
overall pass criteria are defined. This verdict approves the plan only. It does not claim that
Stage 6 execution, CUDA, Docker profiles, Android builds, or end-to-end integration have passed.

Proceed to Stage 6B only after review of this artifact and the exact candidate allowlist. Stop
here for Stage 6A.
