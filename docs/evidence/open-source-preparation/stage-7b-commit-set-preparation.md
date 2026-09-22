# Stage 7B — Commit-set preparation

Date: 2026-09-20
Repository: Nanexus AI Video Summary
Branch and baseline: `main` at `da3b7c6eb32160d927ff5101194698478da8b2de`

## 1. Executive summary

The intentionally dirty worktree was divided into eight proposed commits and each candidate was
staged by explicit path or hunk, reviewed in full, checked with `git diff --cached --check`,
scanned for public exposure, assigned a staged-tree identity, and unstaged before the next set.
No commit, push, tag, configuration change, or history rewrite was made.

The Stage 7A architecture remains sound with two refinements. The complete CPU/CUDA dependency
solver change and its single regenerated lock belong in commit 2 because splitting the lock would
invent an unverified intermediate resolution. The `OPENCLIP_MODEL` example hunk belongs in commit
1 so that its intermediate configuration agrees with the new QuickGELU default. Remaining
`.env.example` hunks are separated among integration, security, device-profile, and documentation
sets. `compose.release.yaml` is divided between CPU model-cache/default work and portable Event
Intelligence source contexts; `compose.slice.yaml` is entirely integration portability.

Stage 7B is **NEEDS REVIEW**, not blocked. The commit candidates are deterministic, but a human
must decide whether to correct or explicitly document the legacy `/health` `ai_mode` field before
creating commit 4, and must approve every commit. The separate Event Intelligence contract change
must precede Video Summary commit 3.

## 2. Git preflight and identity

- branch: `main`
- exact HEAD before and after preparation: `da3b7c6eb32160d927ff5101194698478da8b2de`
- initial staged state: empty
- identity: `Andy Shen <80353459+edge-ai4cv@users.noreply.github.com>`
- identity origin: both values come from global Git configuration; there is no repository
  override
- configuration changes: none

The identity matches the approved identity for future commits. Existing historical identity is
preserved under the approved no-rewrite strategy.

## 3. Definitive commit order and map

### 1. `feat(model): complete CPU OpenCLIP closeout`

Purpose: preserve the CPU Stage 9 closeout that predates open-source preparation: the audited
QuickGELU model pair, activation compatibility guard, CPU benchmark coverage, cache persistence,
and synthetic mock source.

Files/hunks:

- `.env.example`: only `OPENCLIP_MODEL=ViT-B-32-quickgelu`;
- `compose.release.yaml`: only the model-service QuickGELU default, Hugging Face/cache volume,
  enrichment-worker cache mount, and `model-cache` volume declaration;
- `scripts/benchmark_openclip_cpu.py`, `src/nanexus/config.py`,
  `tests/smoke/openclip_gate_mock_frigate.py`, `tests/test_config.py`, and
  `tests/test_openclip_provider.py`: complete diffs;
- `src/nanexus/providers/openclip.py`: only `validate_activation_config` and its load-time
  model/pretrained validation; device resolution and capability hunks are excluded.

Verification: cached diff check and exposure scan passed; `tests/test_config.py` plus
`tests/test_openclip_provider.py` passed (6 tests). Stage 6F-2 supplies real CPU inference,
pgvector, repeatability, and offline-cache evidence. Final staged-tree identity:
`ccbbca049b1f4e39042f67f4cba9fff1c2cce59f`.

Dependency: baseline only. This commit records pre-existing Stage 9 work; it must not be described
as created by Stages 4–6.

### 2. `feat(model): add explicit CPU and CUDA execution profiles`

Purpose: make Linux CPU and container CUDA dependency/device behavior explicit, mutually
exclusive, observable, and fail-closed.

Files/hunks:

- `.env.example`: only the `AI_DEVICE` CPU/CUDA/fail-closed explanation;
- `pyproject.toml`: only `openclip-cuda`, uv conflicts, CPU/cu130 indexes and sources; legal and
  build-backend hunks are excluded;
- `uv.lock`: complete regenerated dependency-profile diff (atomic with `pyproject.toml`);
- `compose.gpu.yaml`, `docker/Dockerfile.model-worker-cuda`,
  `src/nanexus/providers/device.py`, `tests/test_gpu_profile.py`, and
  `tests/test_openclip_device.py`: complete new files;
- `services/model_service/main.py`, `src/nanexus/providers/base.py`, and
  `src/nanexus/vision.py`: complete diffs;
- `src/nanexus/providers/openclip.py`: only device resolver import, CUDA/build state,
  `runtime_capabilities`, fail-closed resolution, and `ProviderError` preservation; QuickGELU
  validation is excluded.

Verification: cached diff check and exposure scan passed; GPU/device/provider tests passed
(17 tests); `UV_CACHE_DIR=/tmp/stage7b-uv-cache uv lock --check --offline` passed. Stage 6F-3
supplies real CUDA hardware, search, recreate, and offline-cache evidence. Staged-tree identity:
`7845444dd68f9705956445b56c69710229075684`.

Dependency: commit 1.

### 3. `feat(integration): align public Event Intelligence subject paths`

Purpose: consume canonical ReviewItem identity and keep Search/Chat subject and evidence paths
consistent while making optional source-built integration portable.

Files/hunks:

- `.env.example`: only `EVENT_INTELLIGENCE_SOURCE_DIR` and its comments;
- `compose.release.yaml`: only the three Event Intelligence build-context hunks;
- `compose.slice.yaml`: complete diff (five source/fixture context replacements);
- `services/api/main.py`, `src/nanexus/event_intelligence_contracts/__init__.py`,
  `src/nanexus/schemas.py`, `src/nanexus/public_paths.py`, `tests/test_chat_v1.py`,
  `tests/test_client_api.py`, `tests/test_semantic_search.py`, and
  `tests/test_public_paths.py`: complete diffs.

Verification: cached diff check and exposure scan passed; Chat/client/search/public-path tests
passed (26 tests, with two existing FastAPI deprecation warnings). Stage 6F-1 supplies the real
synthetic cross-repository HTTP/v1 run. Staged-tree identity:
`8de238d4977bad769145c24c152aa3aaea02aaf3`.

Dependency: commits 1–2 and, externally, the separately reviewed Event Intelligence ReviewItem
contract commit/release. No Event Intelligence repository file belongs in this commit.

### 4. `fix(runtime): harden container and trusted-network boundaries`

Purpose: exclude private/generated build-context inputs, fix nginx SPA serving, bind local
infrastructure to loopback, and make anonymous MQTT/trusted-network assumptions explicit.

Files/hunks:

- `.dockerignore`, `compose.model.yaml`, `compose.search.yaml`, `docker-compose.yml`,
  `docker/mosquitto/mosquitto.conf`, and `docker/nginx.conf`: complete diffs;
- `.env.example`: only local credential warnings, loopback/anonymous-MQTT warning, and replacement
  of concrete Frigate LAN examples with placeholders.

Verification: cached diff check and exposure scan passed; `docker-compose config -q` passed.
Stage 6E supplies clean rebuild, static/SPA/proxy, binding, restart, and adversarial Docker-context
evidence. Staged-tree identity: `9187baaaa9faf62e0a1d88c2ca9a6764c00c184c`.

Dependency: none technically; order after model/integration commits makes the review narrative
clear and prevents duplication of their Compose hunks. The unresolved legacy health-label
decision, if fixed, belongs here.

### 5. `chore(project): add Apache-2.0 and contribution metadata`

Purpose: establish the source-release license, security/contribution process, packaging metadata,
and narrow public/private ignore boundary.

Files/hunks:

- `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, and `.gitignore`: complete diffs;
- `pyproject.toml`: only setuptools 77, `license = "Apache-2.0"`, and
  `license-files = ["LICENSE"]`; dependency-profile hunks are excluded.

Verification: cached diff check and exposure scan passed; metadata/license references were
cross-checked. Staged-tree identity: `b00cb5760c0718c960323c06cb6bdccbb9b28daa`.

Dependency: none technically; placed after runtime work to keep implementation commits focused.

### 6. `docs: publish current architecture and operator guidance`

Purpose: publish the authoritative overview, architecture, development, deployment, Android, and
resource guidance with accurate capability and maturity framing.

Files/hunks:

- `README.md`, `docs/architecture.md`, `docs/development.md`, `docs/deployment.md`,
  `docs/android.md`, and `docs/resource-profiles.md`: complete diffs, including the narrow Stage
  7B README framing correction and explicit observation/ReviewItem route clarification;
- `.env.example`: only removal of obsolete Stage 4/5 labels from worker/Search comments.

Verification: cached diff check and exposure scan passed. Current-facing scans confirm
`/api/v1/events/{observation_id}`, `/api/v1/review-items/{review_item_id}`, and Video Summary
`/api/v1/subjects/{review_item_id}`; no obsolete `/events/{subject_id}` guidance remains.
Staged-tree identity: `45f1a8bb7608217c92f0896074b015009f2ed96c`.

Dependency: commits 1–5.

### 7. `docs(history): archive superseded engineering records`

Purpose: move useful dated records under a clearly non-authoritative history index and remove
obsolete/private-task-oriented documents that should not remain public guidance.

Files/hunks: complete additions under `docs/history/`; matching deletions under
`docs/architecture-reviews/` and the repository's root `docs/` directory; complete deletion of
`docs/android-dev-machine.md`, `docs/compatibility-matrix.md`,
`docs/deployment-security-runbook.md`, `docs/rough_idea.txt`, `docs/stage9-acceptance.md`,
`docs/stage9-closeout-acceptance.md`, and `docs/stage9-closeout-plan.md`.

Verification: cached diff check and exposure scan passed. All 18 retained records have explicit
historical/non-authoritative notices, `docs/history/README.md` points to current authorities, and
current docs do not depend on history for required instructions. Staged-tree identity:
`ce726c50655591128b6a67f4a8f6838b42759d0c`.

Dependency: commit 6.

### 8. `docs(evidence): record open-source preparation verification`

Purpose: publish the sanitized Stage 0–7 preparation ledger after the behavior and documentation
it describes.

Files/hunks: complete `docs/evidence/open-source-preparation/` directory and its `README.md`,
including this Stage 7B record. Raw/private Stage 9 prompts, acceptance material, temporary
candidates, audit output, caches, and machine configuration remain excluded.

Verification and staged-tree identity are recorded in section 8 after isolated staging.

Dependency: commits 1–7.

## 4. README value and maturity review

The README now explicitly explains why the application layer matters: it moves beyond raw video
timelines and isolated alerts into summaries, semantic search, cited Chat, and evidence/subject
resolution, reducing manual review. It lists the demonstrated Summary, Search, Chat, citation,
evidence/subject, Web, Android, CPU OpenCLIP, and GPU/CUDA paths. Web and Android are accurately
described as functional reference interfaces rather than finished/productized UI/UX.

It also states that Video Summary intentionally sits above the separate vendor-neutral,
platform-neutral Event Intelligence middleware, consumes stable versioned public contracts
instead of binding to one NVR/VMS, and that the middleware can support future applications beyond
Video Summary. The narrow Stage 7B edit added the previously underrepresented manual-review and
independent-middleware-value framing; it did not redesign the README.

## 5. Legacy `ai_mode` finding

Source: `Settings.ai_mode` defaults to `openclip` in `src/nanexus/config.py`; the legacy API
`GET /health` in `services/api/main.py` returns that value through `HealthResponse.ai_mode`.
The value describes the retained legacy AI-worker path. The v1 enrichment/model path instead uses
`Settings.model_provider`, defaults to `stub`, and exposes accurate provider/model/device data at
the model service's `GET /health`. `/health/live`, `/health/ready`, and
`/api/v1/operations/status` do not emit the misleading `ai_mode` value.

Classification: **misleading observability on a legacy compatibility surface**, not a failure of
the verified v1 runtime. A public operator could reasonably read the unqualified field as the
active global provider. The smallest treatment is either (a) document and label it explicitly as
legacy while adding an independently named v1/model-provider field, preserving compatibility, or
(b) deprecate/rename it in a versioned change. Replacing it silently with `model_provider` would
change its historical meaning and is not recommended. No automatic modification was made. If the
owner requires a code correction before publication, it belongs in commit 4 with a focused health
schema/test change.

## 6. Dependency-security ledger

The carried-forward Web audit remains 3 findings: 2 moderate and 1 high, involving direct
development dependency `vitest`, transitive `@vitest/mocker`, and transitive `js-yaml`. Existing
Stage 6C evidence shows Vitest/mocker are test-toolchain dependencies and that production-bundle
inspection found no Vitest, jsdom, Testing Library, test, mock, or fixture marker. The `js-yaml`
finding is in that dependency chain and was not observed as shipped application code. On current
evidence these are dev/test-toolchain findings, not demonstrated production runtime-bundle
exposure. They remain a release/security follow-up. No `npm audit fix` or dependency mutation was
performed.

## 7. Private/excluded boundary

The ignored boundary still excludes `.env`, `compose.cpu-openclip-gate.yaml`, private Stage 9
prompts/raw acceptance material, `android/local.properties`, signing material, caches, virtual
environments, dependency/build trees, databases/logs/runtime data, model weights/caches, APK/AAB
outputs, and raw audit/SBOM/license/benchmark output. Public candidates were staged only by exact
path/hunk. Exposure matches in candidate diffs were expected variable names, documented
placeholders, dependency hashes, Android's standard `10.0.2.2` emulator alias, or removed
historical strings—not embedded credentials or private infrastructure.

The evidence ledger intentionally records Stage 7A's historical finding that old commits contain
an author email, workstation path/name, and concrete RFC1918 examples. Under the approved
history-preservation strategy these are findings about immutable history, not live credentials or
new public configuration. Raw private evidence is absent.

## 8. Commit 8 verification and final state

Commit 8 contains 27 Markdown files and 3,687 added lines after mechanical removal of inherited
Markdown trailing whitespace. `git diff --cached --check` then passed. The targeted key,
credential, private-workspace, and temporary-path scan found no credential/key material or live
private workspace path. The two retained `/tmp` strings are explicitly sanitized, disposable
verification paths (`/tmp/stage6e-event-intelligence` and `/tmp/stage7b-uv-cache`), not source,
credentials, or required infrastructure. The cached candidate immediately before this final
record update had tree identity `2f210d7163aa58873c470cef6a736413ff4b0a6b`; the final identity is
reported in the Stage 7B handoff because embedding a tree's own changing hash in this file is
self-referential.

After final review, all evidence paths were unstaged. The index was empty, HEAD remained
`da3b7c6eb32160d927ff5101194698478da8b2de`, the intentionally dirty source changes remained, and
the only new worktree file created by Stage 7B was this requested evidence record. Review scratch
files and the isolated uv cache were confined to `/tmp`; no repository build/generated file was
created.

## 9. Human decisions required before any commit

1. Approve each proposed commit message, boundary, and order; no commit exists yet.
2. Decide whether legacy `/health.ai_mode` needs the compatibility-preserving commit 4 correction
   described above or an explicit documentation/deprecation follow-up.
3. Land/release the separate Event Intelligence ReviewItem contract change before Video Summary
   commit 3.
4. Accept the preserved historical author/workstation/RFC1918 metadata or separately authorize a
   privacy-driven history policy change; Stage 7B did not rewrite history.
5. Review the three Web dev/test advisories before a release; do not apply blind audit fixes.
6. Reverify the noreply identity and complete cached diff immediately before every human-approved
   `git commit`.
