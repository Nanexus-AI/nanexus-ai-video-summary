# Stage 7A — Git history and release-boundary audit

Date: 2026-09-20
Scope: read-only Git/history/release-boundary audit, except for this sanitized evidence file
Video Summary baseline: `main` at `da3b7c6eb32160d927ff5101194698478da8b2de`

## 1. Executive summary

The repository can reach a reviewable public history through ordinary new commits. Existing
history should be preserved. No committed credential, secret, private camera URL, model weight,
APK/AAB, database, log, or other security blocker was found. Existing commits do contain the
author's former personal email, a workstation name/path, and literal private-LAN example
addresses. Those are historical privacy/cosmetic concerns, not secrets, and do not justify a
history rewrite by themselves.

The current worktree must not be committed wholesale. It combines pre-open-source CPU OpenCLIP
closeout work, later GPU and device behavior, Event Intelligence consumer-contract corrections,
Docker/security corrections, legal metadata, current documentation, historical-document moves,
and 25 sanitized Stage 0–6 evidence records. Several files contain hunks for more than one
logical commit and require patch-level staging during a future, human-approved Stage 7B.

Event Intelligence has its own dirty worktree. Seven files implement the canonical ReviewItem
identity and lookup contract needed by Video Summary. They require a separate Event Intelligence
commit/PR and must precede the Video Summary commit that consumes that contract. Four unrelated
pre-existing Event Intelligence assets/documents must not be included with the integration fix.

**Recommendation: preserve existing history, add ordered atomic commits, and publish from a new
release-preparation branch created at the current `main` HEAD. Do not rewrite old commits.**

## 2. Current Git baseline

| Item | Result |
| --- | --- |
| Branch | `main` |
| Exact HEAD | `da3b7c6eb32160d927ff5101194698478da8b2de` |
| HEAD subject | `fix(release): close stage 9 validation gaps` |
| Remotes | none |
| Upstream | none configured for `main` |
| Tags | none |
| Staged state | empty |
| Tracked dirty state | 28 modified and 25 deleted files (53 total) |
| Untracked public candidates before this record | 59 files: 25 evidence, 19 history, 15 other |
| Untracked public candidates after this record | 60 files; this file is the only addition |
| Ignored state | private/local inputs and generated trees described in section 8 |

All 16 commits from `3804867` through `da3b7c6` are linear on local `main`. Recent history, newest
first, is:

```text
da3b7c6 fix(release): close stage 9 validation gaps
336a406 feat(release): harden deployment and compatibility
0afe6b4 feat(clients): migrate web and android to v1 APIs
f5f23a4 feat(chat): migrate chat to event intelligence
8825a83 feat(summary): migrate summaries to event intelligence
5572d6e feat(search): add versioned semantic retrieval
475520f feat(model): migrate OpenCLIP provider
622baec feat(migration): complete cross-repository slice
5a8635d test(migration): freeze baseline and close foundation gate
8c72495 feat(contracts): add event intelligence v1 consumer
e56a172 Add Android Compose client wired to the Nanexus API.
cad6f02 Normalize chat camera aliases and document Android host setup.
38ce66e Add M2 summary worker and RAG chat over Frigate events.
62dcd28 Add Frigate API import path for real-host verification.
eb43337 Add M1 OpenCLIP vision pipeline and semantic search.
3804867 Add M0 Frigate AI summary prototype with Docker and Python services.
```

The only additional local ref observed is a Codex turn-diff capture ref. It is not a branch, tag,
remote-tracking ref, or proposed publication ref.

## 3. Git identity audit

Current effective identity, verified from configuration:

```text
user.name  = Andy Shen
user.email = 80353459+edge-ai4cv@users.noreply.github.com
```

Both values originate in the user's global Git configuration. There is no repository-local
override.

Every existing Video Summary commit has author and committer `Andy Shen` with a historical
personal author email. The same older identity appears in inspected Event Intelligence history.
This is personally identifying metadata but is not a credential or security flaw.

**Classification: documentation only.** Use the current noreply identity for all new commits.
Do not rewrite history merely to replace the historical address. A rewrite would be justified
only if the owner makes a separate privacy decision that the address must not be public; that
would be a publication-policy choice, not a technical release requirement.

## 4. Complete dirty-tree classification

The categories below classify content, not merely filenames. Mixed files are explicitly marked
and must be split by hunk where indicated.

### 4.1 Core product/runtime implementation

- `services/model_service/main.py`: runtime identity/capability health response (also GPU/device).
- `src/nanexus/providers/base.py`: default runtime capability reporting (also GPU/device).
- `src/nanexus/vision.py`: shared strict device resolution (also GPU/device).

### 4.2 CPU OpenCLIP implementation

- CPU/QuickGELU hunks in `.env.example`, `src/nanexus/config.py`,
  `src/nanexus/providers/openclip.py`, `scripts/benchmark_openclip_cpu.py`,
  `tests/test_config.py`, and `tests/test_openclip_provider.py`.
- `tests/smoke/openclip_gate_mock_frigate.py`: original synthetic local source used by the CPU
  integration gate; suitable public mock tooling, not raw acceptance evidence.
- CPU-index and `openclip` dependency portions of `pyproject.toml` and `uv.lock` are mixed with
  later CUDA work and should be committed with the complete dependency-profile change rather
  than manually inventing an intermediate lock.

### 4.3 GPU/CUDA implementation

- `compose.gpu.yaml`, `docker/Dockerfile.model-worker-cuda`,
  `src/nanexus/providers/device.py`, `tests/test_gpu_profile.py`, and
  `tests/test_openclip_device.py`.
- Device/capability hunks in `services/model_service/main.py`,
  `src/nanexus/providers/base.py`, `src/nanexus/providers/openclip.py`, and
  `src/nanexus/vision.py`.
- Mutually exclusive CPU/CUDA extras, package indexes, license metadata, and regenerated lock in
  `pyproject.toml` and `uv.lock` (mixed with categories 2 and 8).
- GPU profile documentation hunks in `.env.example`, `README.md`,
  `docs/architecture.md`, `docs/deployment.md`, `docs/development.md`, and
  `docs/resource-profiles.md` belong with later documentation, not runtime commits.

### 4.4 Event Intelligence integration and contract support

- `src/nanexus/event_intelligence_contracts/__init__.py`, `src/nanexus/schemas.py`,
  `src/nanexus/public_paths.py`, and relevant `services/api/main.py` hunks.
- Contract/path coverage in `tests/test_chat_v1.py`, `tests/test_client_api.py`,
  `tests/test_semantic_search.py`, and `tests/test_public_paths.py`.
- Portable optional source-root hunks in `.env.example`, `compose.release.yaml`, and
  `compose.slice.yaml` are integration/deployment support.

### 4.5 Docker, Compose, and security fixes

- `.dockerignore`, `docker/nginx.conf`, `docker/mosquitto/mosquitto.conf`,
  `docker-compose.yml`, `compose.model.yaml`, `compose.search.yaml`, and security/runtime hunks in
  `compose.release.yaml`, `compose.slice.yaml`, and `.env.example`.
- `.dockerignore` is a Stage 6 privacy/reproducibility correction; nginx's static `root` is a
  Stage 6 runtime correction. They should be a dedicated container-boundary fix commit.

### 4.6 Public documentation

- `README.md`, `docs/architecture.md`, `docs/resource-profiles.md`, `docs/android.md`,
  `docs/deployment.md`, and `docs/development.md`.
- These describe the final behavior and should follow the relevant runtime/contract commits.

### 4.7 Historical documentation cleanup

- New `docs/history/README.md` and all 18 other files under `docs/history/`.
- The corresponding deleted root-level documents and seven deleted
  `docs/architecture-reviews/*` files are moves with historical labels/sanitization where needed.
- Deleted rather than moved as current/public authority: `docs/compatibility-matrix.md`,
  `docs/deployment-security-runbook.md`, `docs/rough_idea.txt`, `docs/stage9-acceptance.md`,
  `docs/stage9-closeout-acceptance.md`, and `docs/stage9-closeout-plan.md`.
- This is one coherent history/archive cleanup and must not be folded into product code.

### 4.8 Open-source legal/project metadata

- `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, and `.gitignore`.
- License declaration/build-backend hunks in `pyproject.toml` are mixed with dependency work and
  should be separated by hunk if practical.

### 4.9 Tests

- Feature-coupled tests are all tests named in categories 2–4 plus
  `tests/test_gpu_profile.py`, `tests/test_openclip_device.py`, and
  `tests/test_public_paths.py`.
- Tests should travel with the feature/fix they verify; there is no benefit in a standalone
  catch-all test commit.

### 4.10 Public sanitized evidence

- `docs/evidence/open-source-preparation/README.md` and Stage 0 through Stage 6G records, plus
  this Stage 7A record: 26 files after this audit.
- Commit them together as a consolidated preparation-evidence commit after the behavior and
  documentation they describe. Per-stage commits would add noise and interleave evidence with
  product history without improving bisectability.

### 4.11 Private/local/excluded

- `.env`, `compose.cpu-openclip-gate.yaml`, the two Stage 9 prompt files, raw CPU acceptance
  material, `android/local.properties`, signing material, secrets, and private machine settings.
- None is a proposed commit candidate.

### 4.12 Generated/disposable

- Python/pytest/mypy/Ruff caches, `.venv`, egg-info, Android `.gradle`/`.idea`/build outputs,
  Web `node_modules`/`dist`/TypeScript build metadata, `data/`, databases/logs, model caches and
  weights, APK/AAB outputs, and raw audit/SBOM/license/benchmark output.
- None is a proposed commit candidate.

### 4.13 Unclear

No public candidate remains unclassified. The four unrelated Event Intelligence untracked
assets/documents are clear exclusions from the integration series, not unclear files.

## 5. Original Stage 9 work and provenance

The existing commit at `475520f` already introduced the main OpenCLIP provider architecture.
The uncommitted work that predates open-source preparation is the subsequent CPU closeout:

- change the audited model pair from `ViT-B-32/openai` to
  `ViT-B-32-quickgelu/openai`;
- reject model/pretrained QuickGELU activation mismatches;
- route Linux CPU Torch/Torchvision through the explicit CPU index;
- extend the CPU benchmark to image and text embeddings;
- add the QuickGELU/default regression tests;
- retain the public synthetic mock Frigate server used for the end-to-end gate; and
- preserve raw prompts, local gate Compose, and raw acceptance evidence as private ignored files.

The preserved 2026-08-25 CPU acceptance record identifies the repository at the same current
HEAD, states that no commit was created, and distinguishes four pre-existing documentation edits
and two pre-existing prompt files. This is direct provenance evidence; the public history should
not claim that the CPU work originated during open-source cleanup.

The broader committed Stage 9 foundation remains represented by the existing commits
`336a406` and `da3b7c6`. The current documentation restructuring must not be described as the
origin of that earlier implementation.

## 6. Stage 4–6 corrective changes

| Correction | Origin | Recommended grouping |
| --- | --- | --- |
| `.dockerignore` excludes Git/private/runtime/model/build inputs | Stage 6E defect | Dedicated Docker/security fix with nginx root and Compose boundary changes |
| nginx static root fixes SPA fallback loop | Stage 6E defect | Same Docker/runtime fix commit |
| Search evidence URL removes duplicated segment | Stage 6F-1 defect | Event Intelligence consumer/public-path commit with its test |
| Subject URL uses canonical ReviewItem public route | Stage 6F-1 defect | Same consumer/public-path commit, ordered after compatible EI change |
| EI publishes `review_item_id` and a public ReviewItem lookup | Stage 6F-1 defect | Separate EI repository commit/PR |
| CPU and CUDA extras use explicit, conflicting indexes/profiles | Stage 6F-3 defect/requirement | GPU/dependency-profile commit; keep one regenerated lock |
| GPU Compose requests one NVIDIA device | Stage 6F-3 defect | Same GPU/dependency-profile commit |
| Explicit CUDA fails closed; `auto` resolves deterministically | Stage 6F-3 behavior fix | Same GPU/device commit with source and tests |
| Portable EI source checkout variable | Stage 4D portability | Consumer/deployment integration commit, not core model code |
| loopback/anonymous-MQTT warnings, safer Compose bindings and read-only mounts | Stages 4B–4C | Docker/security fix commit |
| ignore rules and legal metadata | Stages 4A/4E | Open-source metadata commit |

## 7. Private and excluded boundary verification

The approved boundary remains effective:

- ignored and untracked: local `.env`, private Stage 9 prompts, raw CPU acceptance material,
  and `compose.cpu-openclip-gate.yaml`;
- ignored/generated: local Android SDK configuration, caches, virtual environments,
  dependencies, build outputs, runtime `data/`, databases, logs, audit/SBOM/license/benchmark
  raw output, signing keys/keystores, model caches/weights, and APK/AAB files;
- visible/public: `.env.example`, source, tests, sanitized history, and
  `docs/evidence/open-source-preparation/`.

No excluded path appears in the proposed commits. The live workspace contains generated caches
and build products, so future commits must use explicit path/hunk staging and must be verified
from a clean candidate. A broad `git add .` is unsafe and is not recommended.

## 8. Event Intelligence cross-repository boundary

Event Intelligence is separately on local `main` at
`89bbcd7c4eeb867bdef0c04827b50a6796679856`, with no upstream for `main`, tag `v0.1.0`, and no
staged files. Its integration-relevant dirty files are:

- modified: `backend/src/nanexus_event_intelligence/adapters/frigate/pipeline.py`,
  `backend/src/nanexus_event_intelligence/api/router.py`,
  `backend/src/nanexus_event_intelligence/api/routes/events.py`, and
  `backend/tests/adapters/frigate/test_pipeline.py`;
- untracked: `backend/src/nanexus_event_intelligence/api/routes/review_items.py`,
  `backend/tests/api/test_review_item_id_contract.py`, and
  `backend/tests/api/test_review_items.py`.

Together they store Review mappings as canonical `review_item`, expose `review_item_id` on event
detail with compatibility for legacy `review` rows, and add
`GET /api/v1/review-items/{review_item_id}`. These are required for Video Summary's corrected
subject link and should form one EI contract commit with their tests.

Unrelated pre-existing EI files are the three untracked PNG assets under `assets/` and
`docs/v0.2.0_api_release_scope.md`. They must remain outside the integration commit. The
`codex/readme-demo-visuals` branch is also independent.

Dependency order is strict: merge/release the EI public-contract change first, then merge Video
Summary's consumer/public-path commit and document the minimum compatible EI revision/version.
The two repositories must retain separate commit histories and PRs.

## 9. Proposed Video Summary commit architecture

### VS-1 — Preserve the CPU OpenCLIP closeout

- **Purpose:** record the pre-open-source QuickGELU/default/benchmark work with honest provenance.
- **Files/hunks:** CPU hunks in `.env.example`, `src/nanexus/config.py`,
  `src/nanexus/providers/openclip.py`, `scripts/benchmark_openclip_cpu.py`,
  `tests/test_config.py`, `tests/test_openclip_provider.py`; add
  `tests/smoke/openclip_gate_mock_frigate.py`.
- **Why together:** one validated CPU model-activation correction and its tests/tooling.
- **Dependency:** existing `475520f`; before GPU profile.
- **Message:** `fix(openclip): validate the CPU QuickGELU profile`
- **Split risk:** omitting the default, validation, or tests recreates the audited mismatch; do
  not include private raw gate files.

### VS-2 — Add explicit CPU/CUDA dependency and device profiles

- **Purpose:** make CPU and CUDA installations mutually exclusive, provide the CUDA image/profile,
  resolve devices consistently, and fail closed for unavailable explicit CUDA.
- **Files/hunks:** `pyproject.toml`, `uv.lock`, `compose.gpu.yaml`,
  `docker/Dockerfile.model-worker-cuda`, `src/nanexus/providers/device.py`, capability/device hunks
  in `src/nanexus/providers/base.py`, `src/nanexus/providers/openclip.py`,
  `src/nanexus/vision.py`, `services/model_service/main.py`, and tests
  `tests/test_gpu_profile.py`, `tests/test_openclip_device.py`.
- **Why together:** the lock, image, Compose reservation, runtime semantics, and tests describe one
  installable profile boundary. The single current lock should not be hand-split.
- **Dependency:** VS-1.
- **Message:** `feat(openclip): add explicit CPU and CUDA runtime profiles`
- **Split risk:** separating lock/index, image, reservation, and fail-closed behavior can produce
  a green-looking but CPU-fallback GPU configuration.

### VS-3 — Correct the Event Intelligence public consumer paths

- **Purpose:** consume canonical ReviewItem identity, correct subject/evidence public URLs, and
  keep optional source builds portable.
- **Files/hunks:** `src/nanexus/event_intelligence_contracts/__init__.py`,
  `src/nanexus/schemas.py`, `src/nanexus/public_paths.py`, relevant `services/api/main.py` hunks,
  EI source-root hunks in `.env.example`, `compose.release.yaml`, `compose.slice.yaml`, and
  `tests/test_chat_v1.py`, `tests/test_client_api.py`, `tests/test_semantic_search.py`,
  `tests/test_public_paths.py`.
- **Why together:** contract representation, generated links/routes, deployment portability, and
  contract tests form the consumer side of one cross-repository boundary.
- **Dependency:** compatible EI commit/PR first; independent of VS-2 otherwise.
- **Message:** `fix(integration): use canonical Event Intelligence public paths`
- **Split risk:** merging Video Summary first yields links to an EI route that does not exist;
  separating path helpers from callers/tests can preserve the duplicated evidence segment.

### VS-4 — Harden container build and runtime boundaries

- **Purpose:** prevent private/generated Docker-context leakage, fix nginx static serving, and
  preserve loopback/internal-service security defaults.
- **Files/hunks:** `.dockerignore`, `docker/nginx.conf`, `docker/mosquitto/mosquitto.conf`,
  `docker-compose.yml`, `compose.model.yaml`, `compose.search.yaml`, non-EI security/runtime hunks
  in `compose.release.yaml`, `compose.slice.yaml`, and `.env.example`.
- **Why together:** these are container and trusted-network boundary corrections found while
  reproducing the release topology.
- **Dependency:** before documentation/evidence; coordinate hunk staging with VS-3.
- **Message:** `fix(containers): harden build context and runtime defaults`
- **Split risk:** committing Compose changes without `.dockerignore` or nginx correction leaves a
  known privacy or runtime defect in an intermediate public commit.

### VS-5 — Add open-source legal and contribution metadata

- **Purpose:** establish Apache-2.0 licensing, security/contribution policy, and durable exclusions.
- **Files/hunks:** `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `.gitignore`, and legal/build-system
  metadata hunks in `pyproject.toml` if they can be staged without corrupting VS-2.
- **Why together:** one project-governance boundary.
- **Dependency:** may precede runtime commits, but after VS-2 if `pyproject.toml` hunk isolation is
  judged too error-prone.
- **Message:** `chore(project): add open-source policy and license metadata`
- **Split risk:** separating the license file from package metadata creates temporary ambiguity;
  combining this with runtime changes obscures legal review.

### VS-6 — Refresh current public documentation

- **Purpose:** document the final architecture, setup, security, Android, CPU, and CUDA behavior.
- **Files:** `README.md`, `docs/architecture.md`, `docs/resource-profiles.md`, `docs/android.md`,
  `docs/deployment.md`, and `docs/development.md`.
- **Why together:** these form the current reader-facing documentation set and cross-reference the
  final runtime state.
- **Dependency:** VS-1 through VS-5 and the EI prerequisite.
- **Message:** `docs: refresh public architecture and operator guides`
- **Split risk:** earlier placement can document routes/profiles not yet present; mixing with
  archive moves makes current guidance harder to review.

### VS-7 — Archive historical development records

- **Purpose:** move useful records under `docs/history`, label them non-authoritative, and remove
  raw/obsolete Stage 9 and draft material from the public current-doc surface.
- **Files:** all 25 tracked documentation deletions plus all 19 `docs/history/` additions.
- **Why together:** Git can review the renames and sanitization as one documentation-only change.
- **Dependency:** after VS-6 so current replacements exist.
- **Message:** `docs(history): archive superseded development records`
- **Split risk:** deletion-only and addition-only commits lose rename reviewability and briefly
  remove useful provenance.

### VS-8 — Preserve sanitized open-source preparation evidence

- **Purpose:** publish concise Stage 0–7A gate records without raw logs/private execution data.
- **Files:** `docs/evidence/open-source-preparation/README.md` and all sanitized stage records.
- **Why together:** evidence is review metadata, not runtime behavior; consolidation keeps the
  product history readable.
- **Dependency:** last.
- **Message:** `docs(evidence): record open-source preparation gates`
- **Split risk:** interleaving stage evidence with implementation creates large evidence-only
  diffs around each feature and can falsely imply those features originated in preparation.

## 10. Proposed Event Intelligence commit architecture

One integration commit is preferred:

- **Purpose:** publish canonical ReviewItem identity and lookup for v1 consumers.
- **Files:** the seven integration-relevant EI files listed in section 8.
- **Message:** `fix(api): expose canonical ReviewItem identity`
- **Order:** before Video Summary VS-3.
- **Risk:** splitting the pipeline mapping from the compatibility read path or route/tests can
  create records the API cannot resolve, or an endpoint that only works for new rows.

The three image assets and deferred v0.2.0 scope document need separate owner decisions and, if
desired, separate commits/PRs. They have no dependency on Video Summary integration.

## 11. Deterministic ordering

1. Create and review the EI contract commit/PR; merge or otherwise establish a compatible EI
   revision.
2. Video Summary VS-1: CPU QuickGELU closeout.
3. VS-2: CPU/CUDA dependencies and device/profile behavior.
4. VS-3: Event Intelligence consumer contract and public paths.
5. VS-4: Docker/security/runtime corrections.
6. VS-5: legal/project metadata (or before step 2 if the `pyproject.toml` legal hunk is safely
   isolated).
7. VS-6: current public documentation.
8. VS-7: historical documentation archive/cleanup.
9. VS-8: consolidated sanitized evidence.

Each future commit should be built/tested from the exact staged tree. Where a mixed file cannot be
split without producing a known-invalid intermediate state, keep the complete file with the
earliest commit that requires its final form and explain the provenance in the commit body.

## 12. Existing committed-history exposure findings

The complete reachable `main` history was inspected for author identities, private-network and
workstation strings, credential/key patterns, artifact filenames, and large blobs.

- **Harmless historical metadata:** all commits use the older personal author/committer email.
- **Embarrassing/private but non-sensitive:** committed documentation/examples include a local
  workstation hostname, a `<local-sdk-path>`, and historical RFC1918 private-network examples.
  Current dirty documentation removes or generalizes these.
- **Expected non-sensitive networking:** Android emulator address `10.0.2.2` and placeholder
  `192.168.x.x` are normal documentation values.
- **No actual blocker found:** no AWS-access-key-shaped value, private-key block, embedded
  credential, real token, model/binary artifact, APK/AAB, database/log artifact, or blob at least
  1 MiB is reachable from `main`.
- Token-related matches were variable names and token-provider code, not embedded token values.

The old workstation/LAN details remain reachable after ordinary corrective commits. They are a
privacy blemish, not a secret. Default recommendation is documentation only, with no rewrite.
If the owner considers the workstation name/path or exact private addresses unacceptable public
metadata, that is the one human privacy decision that could trigger a stronger cleanup before a
remote is created.

## 13. Recommended history strategy and release boundary

Choose **A plus B** from the evaluated strategies:

- **A:** preserve all existing committed history and add clean commits;
- **B:** organize the accumulated uncommitted work into the atomic series above rather than one
  monolithic snapshot.

Do not choose **C** (rewrite) on current evidence. A new release-preparation branch is useful as
an operational review boundary, but it should point at the same existing history and receive the
new commits; it is not a replacement/synthetic history. Therefore **D** is recommended only in
the branch sense, not as an orphan branch or rewritten root.

The repository can reach a public-ready Git history through ordinary new commits. No stronger
history intervention is technically required. Before publication, verify each commit's staged
diff, run proportional tests, scan the final reachable history again, and perform a clean-clone
release check. Do not add a remote, push, tag, or publish without separate human authorization.

## 14. Human decisions required

1. Approve or revise the proposed Video Summary and Event Intelligence commit boundaries.
2. Decide whether historical personal email, workstation name/path, and exact RFC1918 examples
   are acceptable as non-sensitive history. Default: accept and document; do not rewrite.
3. Choose the compatible EI revision/version to document before merging VS-3.
4. Decide whether unrelated EI assets and the deferred v0.2.0 scope document should receive
   separate future commits; they must not enter the integration commit by accident.
5. Authorize Stage 7B separately before any staging or commit action.

## 15. Gate recommendation

**Stage 7A verdict: NEEDS REVIEW.**

The audit found no technical or security blocker and recommends ordinary new commits on preserved
history. Human approval is still required for commit architecture, cross-repository ordering, and
acceptance of non-sensitive historical identity/workstation metadata. This task did not stage,
commit, push, rewrite history, add a remote, create a tag, or begin Stage 7B.
