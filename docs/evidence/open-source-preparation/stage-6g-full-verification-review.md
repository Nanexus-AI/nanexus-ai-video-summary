# Stage 6G full reproducibility and verification review

Date: 2026-09-20
Repository: Nanexus AI Video Summary
Verdict: **PASS**
Gate 6 recommendation: **PASS**

## 1. Executive summary

The complete Stage 6 record supports Gate 6. Clean public candidates reproducibly installed,
built, tested, started, and integrated the backend, Web, Android, Docker/Compose, deterministic
Stub, CPU OpenCLIP, and GPU/CUDA OpenCLIP surfaces. The final Event Intelligence run exercised
the real cross-repository public HTTP/v1 boundary with separate databases and canonical
ReviewItem identity. Restart, offline-cache, pollution, and public/private-boundary checks also
passed.

The evidence documents preserve initial failures as well as their corrective reruns. The final
results therefore describe the corrected state rather than treating an earlier failed run as a
pass. No complete runtime suite was repeated in Stage 6G because the records were internally
consistent and targeted source/configuration inspection confirmed the final corrections.

Stage 6G found one Gate-level documentation truthfulness issue: current-facing documents still
described GPU dependency routing or hardware validation as unresolved after Stage 6F-3 had
passed. Six narrow documentation corrections were made. No runtime source, dependency, lock,
Compose, or test behavior was changed by this review.

## 2. Verification-matrix closure

| Surface | Classification | Closure basis |
|---|---|---|
| Backend | PASS | Frozen Python 3.12 install, Ruff, Mypy, 91 tests, migration, Stub smoke |
| Web | PASS WITH KNOWN LIMITATION | Exact Node 22.14.0 workflow, 3 tests and production build passed; browser polish was not evaluated |
| Android | PASS WITH KNOWN LIMITATION | JDK 17/SDK 35 clean build, 6 tests, lint and Debug APK passed; no instrumentation or release publication |
| Docker/Compose | PASS | All documented renders, eight source images, canonical Stub runtime, nginx, ports, restart, cleanup |
| Event Intelligence integration | PASS | Real synthetic cross-repository HTTP/v1 flow through Summary, Search, Chat, subject and evidence paths |
| Stub | PASS | Deterministic no-model backend/model-service and release-stack behavior |
| CPU OpenCLIP | PASS | Real CPU provider/service inference, pgvector search, repeatability and offline reload |
| GPU/CUDA OpenCLIP | PASS | Separate cu130 image/profile, real RTX 5060 Ti inference, pgvector search and recreate/offline reload |
| Model cache/offline behavior | PASS WITH KNOWN LIMITATION | Isolated cache and supported offline flags passed; kernel network namespace was unavailable |
| Public/private boundary | PASS | Clean allowlists, exposure scans, `.dockerignore`, artifact exclusion, separate services/databases |
| Restart/repeatability | PASS | Compose, cross-repository integration, CPU cache reload and GPU recreate were repeated successfully |
| APK/AAB and prebuilt image publication | DEFERRED BY DESIGN | Source-first gate builds locally; signing, distribution and image publication are later artifact work |
| Product UI/UX validation | DEFERRED BY DESIGN | Web and Android are functional reference interfaces, not finished/productized presentation layers |

No matrix row is a blocker.

## 3. Candidate consistency

Stages 6B through 6F used detached or freshly exported candidates based on the recorded source
HEAD. Each applied the complete reviewed tracked diff and copied public untracked paths through
an explicit allowlist. Ignored/private files, the source virtual environment, dependency trees,
local Android configuration, runtime databases/logs, APK/AAB files, model caches/weights, and
private Stage 9 material were excluded. Candidate manifests and source hashes were checked before
and after execution, and the main worktree and empty index were preserved.

The candidate necessarily evolved as Stage 6 found defects. Early candidates did not contain
the later `.dockerignore`, nginx root correction, ReviewItem/evidence-path corrections, or CUDA
profile. This is not an evidence gap: each correction received a new clean-candidate rerun in its
own stage, and the final Stage 6F-3 candidate used the complete then-current tracked patch plus
all 58 reviewed public untracked files. Stage 6G's targeted scan confirms those later files and
routes coexist in the current candidate. A consolidated full-suite rerun is not required by any
contradictory evidence.

## 4. Surface conclusions

### Backend

PASS. The final frozen environment combines the existing `test` and `openclip` extras because
Mypy intentionally scans optional provider modules. Ruff, Mypy, compile checks, all 91 tests, a
fresh Alembic migration, and bounded Stub API smoke passed without lock changes, model weights,
or private infrastructure.

### Web

PASS WITH KNOWN LIMITATION. A clean `npm ci`, typecheck, lint, three tests, and production build
passed on exact Node 22.14.0/npm 10.9.2. Bundle inspection found no private target, credential,
source map, or test material. The three npm advisories remain a release/security follow-up.
Browser-level visual polish was outside the reproducibility claim.

### Android

PASS WITH KNOWN LIMITATION. The candidate independently supplied `local.properties`, resolved a
fresh Gradle environment, passed six unit tests and lint, and built/inspected a disposable Debug
APK without production signing state. Seven lint and two compiler warnings are non-blocking.
Instrumentation testing and signed release publication remain outside this source gate.

### Docker/Compose

PASS. All documented configurations rendered, eight release images rebuilt, and the canonical
Stub topology passed service, API, Web, proxy, SPA fallback, binding, restart and cleanup checks.
The final `.dockerignore` prevents Git/private/runtime/model/build material from reaching
BuildKit. The nginx static root correction was rebuilt and independently smoke-tested.

## 5. Event Intelligence integration conclusion

PASS. Observation UUID and ReviewItem UUID are distinct. Event Intelligence publishes the
canonical `review_item_id`; the processor job, Summary, Search and Chat consistently use that
ReviewItem UUID. Search and Chat expose `/api/v1/subjects/{review_item_id}`. Video Summary
redirects that path to Event Intelligence's public
`/api/v1/review-items/{review_item_id}` endpoint, while Search evidence is served through the
job-scoped Video Summary `/api/v1/search/evidence/{job_id}/{evidence_id}` proxy.

The verified topology used separate Event and Video databases, no sibling runtime source mount,
no direct import, and no private filesystem or real-camera dependency. Current implementation
inspection confirms the authoritative path helpers and API routes. Architecture documentation
was narrowed to state the ReviewItem route explicitly.

## 6. CPU and GPU conclusions

CPU OpenCLIP is a distinct validated path: the `openclip` extra routes Linux Torch and
Torchvision to the CPU index, real `ViT-B-32-quickgelu`/`openai` inference produced finite
normalized 512-dimensional embeddings, the application model service and pgvector path passed,
and isolated offline-cache reload succeeded.

GPU/CUDA OpenCLIP is also a distinct validated path: the mutually exclusive `openclip-cuda`
extra routes Torch/Torchvision to the cu130 index, a dedicated CUDA image installs that extra,
and `compose.gpu.yaml` requests one NVIDIA device with `AI_DEVICE=cuda`. Explicit CUDA does not
silently fall back. Real RTX 5060 Ti inference, persistence/search, recreate and offline reload
passed; the exact-input CPU/GPU cosine similarity was `0.9999998789654755`.

Weights remain on-demand runtime artifacts. The verified revision and hash establish
provenance for the run but do not grant or claim redistribution rights.

## 7. Defect ledger

| Defect | Class | Owner | Corrected? | Independently reverified? | Remaining implication |
|---|---|---|---|---|---|
| Mypy lacked optional OpenCLIP packages | Verification environment/documentation | Video Summary | Yes: static checks install `test` + `openclip` | Yes, Mypy passed 45 files | OpenCLIP is not added to the base/test runtime; contributors must use the documented combined extras |
| Missing `.dockerignore` leaked `.git` worktree path into BuildKit context | Privacy/reproducibility | Video Summary | Yes | Yes, adversarial `COPY .` image audit and eight rebuilds | Maintain ignore rules as new artifact classes appear |
| nginx lacked static root and looped SPA fallback | Runtime configuration | Video Summary | Yes | Yes, clean rebuild, static/SPA/proxy and restart smoke | None for Gate 6 |
| `EventDetail.review_item_id` was not populated | Public contract/identity | Event Intelligence | Yes | Yes, final cross-repository run | Requires the compatible corrected EI revision/release |
| Search evidence URL had a duplicated segment | Public link generation | Video Summary | Yes | Yes, generated URL and PNG retrieval through API/Web | None for Gate 6 |
| Subject route targeted an event instead of canonical ReviewItem | Public contract/routing | Video Summary (with EI public route) | Yes | Yes, 307 plus EI ReviewItem HTTP 200 before/after restart | Deployments must configure the public EI origin correctly |
| GPU extra still selected CPU-only PyTorch | Dependency routing | Video Summary | Yes: separate conflicting CPU/cu130 extras | Yes, frozen CPU regression and CUDA image metadata/runtime | Keep profiles mutually exclusive |
| GPU Compose had no NVIDIA reservation | Deployment configuration | Video Summary | Yes: one explicit NVIDIA device | Yes, render tests and real container hardware run | Other host/GPU combinations need operator validation |

## 8. Public/private boundary conclusion

PASS. The Stage 6 records and targeted Stage 6G checks support all required negative claims:

- no credential or real camera/private-infrastructure dependency entered a candidate;
- no model weight/cache, APK/AAB, database, log, runtime artifact, or raw evidence was committed
  or copied into a clean candidate;
- model caches and build artifacts were isolated and removed after verification;
- private Stage 9 prompt/overlay material remains explicitly ignored and was excluded from all
  candidates;
- the corrected `.dockerignore` blocks Git metadata, personal worktree paths, private env files,
  dependencies, build outputs, runtime state and model artifacts from Docker contexts; and
- the main worktree remains intentionally dirty but unstaged, with local ignored generated
  artifacts distinguishable from the public source candidate.

Historical root-level Stage 9 acceptance/plan files are deleted in the intended public diff;
their ignored private successors were not surfaced.

## 9. Documentation truthfulness result and narrow corrections

Before correction, current-facing files materially contradicted Stage 6F-3:

- `README.md` said CUDA was not hardware-validated and the release/integration matrix remained
  under verification;
- `SECURITY.md` said GPU dependency routing and validation were unresolved;
- `docs/architecture.md`, `docs/development.md`, `docs/deployment.md`, and
  `docs/resource-profiles.md` said GPU validation was still required or not a PASS; and
- `docs/architecture.md` described the subject destination ambiguously as a review/event origin.

Stage 6G made narrow corrections in those six files. They now distinguish the validated CPU and
containerized CUDA paths, limit the CUDA claim to the recorded validation environment, state the
canonical ReviewItem redirect, and preserve the source-first/non-production posture. `README.md`
also states the intended maturity position: Web and Android are functional reference interfaces,
not finished product UI/UX. A post-edit targeted scan found none of the obsolete GPU or
event-route claims.

## 10. Remaining issue classification

| Item | Classification | Rationale / next action |
|---|---|---|
| npm: 2 moderate, 1 high advisories in Vitest/mocker/js-yaml | Release/security follow-up | Review upgrades and exposure; no critical finding and no reproducibility failure; do not auto-fix blindly |
| Seven Android lint and two Kotlin warnings | Optional quality improvement | Zero lint errors; warnings are dependency updates, intended Debug cleartext, deprecation/redundancy |
| Legacy `/health` may report `ai_mode=openclip` while v1 service is Stub | Stage 7 issue | Observability/compatibility cleanup; verified v1 provider/audit remained authoritative |
| No browser UI polish test | Optional quality improvement | Real nginx/API paths passed; presentation polish is outside source reproducibility |
| No Android instrumentation suite/run | Optional quality improvement | No `androidTest` sources; unit/lint/build contract passed |
| Container/image SBOM, notices and final license inventory | Future artifact/publication issue | Required before publishing binary images, not before a source-first gate |
| APK/AAB release signing and publication | Future artifact/publication issue | Debug reproducibility passed; operator-controlled production signing remains intentionally absent |
| Historical Git author/email | Optional quality improvement | One historical non-noreply author email remains in immutable history; no runtime or candidate reproducibility impact; decide separately before publication |
| UI/UX maturity | Optional quality improvement | Interfaces demonstrate the real API flow but are not productized |
| Model-weight redistribution/provenance | Future artifact/publication issue | Runtime acquisition was pinned/hashed for evidence; no weights are bundled and redistribution terms remain operator/publisher work |

None is a Gate 6 blocker.

## 11. Gate 6 blockers

None. The only material documentation contradiction found by Stage 6G was corrected narrowly and
the obsolete claims no longer appear in current-facing documentation.

## 12. Verification performed

- reviewed all Stage 6A, 6B, 6C, 6D, 6E, 6F-1, 6F-2 and 6F-3 evidence documents;
- compared the planned Stage 6A matrix with final pass records and limitations;
- inspected current CPU/cu130 dependency indexes and mutually exclusive extras in
  `pyproject.toml`;
- inspected the dedicated CUDA Dockerfile, GPU Compose reservation and device behavior source;
- inspected authoritative subject/evidence path helpers and API route implementations/tests;
- scanned current-facing documentation for stale GPU and ReviewItem/event claims before and
  after the narrow edits;
- verified the named private Stage 9 files are ignored;
- checked tracked paths for credentials/config, APK/AAB, model-weight, database/log and Stage 9
  artifact classes; local APK/library artifacts found by filesystem inspection were confined to
  ignored build/virtual-environment state, not tracked source;
- ran `git status --short`, confirmed the staged diff is empty, and ran `git diff --check` with no
  errors; and
- did not commit, push, stage, start Stage 7, or rerun the complete runtime matrix.

## 13. Final decision

**Stage 6G verdict: PASS.**

**Gate 6 recommendation: PASS.** Backend, Web, Android, Docker/Compose, real synthetic Event
Intelligence integration, Stub, CPU OpenCLIP, GPU/CUDA OpenCLIP, cache/offline behavior,
restart/repeatability and the public/private boundary are closed. Remaining work is correctly
classified as Stage 7, security/release follow-up, future artifact publication, or optional
quality improvement rather than an unresolved reproducibility blocker.
