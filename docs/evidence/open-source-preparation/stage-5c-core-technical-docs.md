# Stage 5C — core technical documentation

## Scope

Stage 5C consolidated public technical guidance only. No runtime code, dependency, build artifact, release artifact, staging, commit, or publication action was included.

## Authoritative documents

- `docs/architecture.md` now defines current layers, ownership, data flows, capability negotiation, trust boundaries, topologies, compatibility paths, and non-goals.
- `docs/development.md` now defines prerequisites, the `pyproject.toml`/`uv.lock` workflow, backend/Web/Android entry points, configuration, Stub and Event Intelligence workflows, verified ports, checks, OpenCLIP caveats, and excluded local files.
- `docs/deployment.md` now defines the source-first deployment model, Compose roles, integrated and external Event Intelligence topologies, ingress/internal exposure, secrets, model caching, lifecycle concepts, reproducibility, and unsupported areas.
- README navigation was minimally extended to link the Development and Deployment guides while retaining the README as the landing page.

## Consolidation decisions

The rewrite removed Frigate-first, iOS-first, Home Assistant, fixed-device, milestone/gate, and speculative production architecture from the authoritative architecture guide. Frigate/MQTT and legacy API paths remain documented as explicit compatibility and rollback paths.

The preserved boundary is Camera/NVR/VMS -> Nanexus Event Intelligence -> Nanexus AI Video Summary -> Web/Android/Summary/Search/Chat. Runtime integration is through public v1 HTTP/contracts, without a shared database or direct source import. A sibling Event Intelligence checkout is optional and controlled by `EVENT_INTELLIGENCE_SOURCE_DIR`; `EVENT_INTELLIGENCE_URL` controls runtime service access.

`pyproject.toml` plus `uv.lock` is documented as the reproducible Python authority. `requirements.txt` remains an unmodified, unpinned legacy/alternate list.

Deployment guidance preserves the trusted internal network assumption, loopback Web/API publication in the release Compose, internal-only data/model services, deployer-owned external access controls, and the initial source-first release boundary.

## CPU/GPU status

OpenCLIP defaults were verified as `ViT-B-32-quickgelu` and `openai`. Weights are downloaded and cached on demand rather than bundled. CPU execution has current validation evidence. GPU/CUDA remains a supported capability, but current Linux dependency routing is CPU-oriented and CUDA packaging/release validation remains unresolved.

## Verification

- Reviewed all three complete target documents after rewriting.
- `git diff --check` passed for the tracked changes; new files were separately reviewed for whitespace and links.
- All local relative links in README, the three guides, resource profiles, Android notes, and the security runbook resolved.
- Commands were compared with `pyproject.toml`, `web/package.json`, Gradle files, scripts, Dockerfiles, and service entry points.
- `uv lock --check` passed with a writable temporary cache, confirming that `uv.lock` matches current project metadata.
- Standalone Docker Compose v2.32.4 successfully rendered local infrastructure, release base, integrated release, external Event Intelligence release, synthetic slice, slice plus search, and model overlay configurations with validation-only variables. No services were started.
- Ports, environment names, Android emulator URL, OpenCLIP defaults, and toolchain/package versions were compared with current source and Compose.
- A targeted scan of the authoritative guides found no obsolete project name, stale OpenCLIP default, real local filesystem path, or private network address. The Android emulator's documented `10.0.2.2` alias is intentional.
- Private Stage 9 prompt/gate paths and generated audit/SBOM/license/benchmark output remain ignored; the named private Stage 9 files are not tracked.
- The full runtime test suite was not run, as required by Stage 5C.

## Deferred work

Stage 5D/5E material remains deferred, including `SECURITY.md`, `CONTRIBUTING.md`, expanded Android documentation, historical-document reorganization, CUDA dependency resolution, published images, and APK/AAB release work.

## Gate recommendation

**PASS** — the core public technical guides are consolidated and verified within the documentation-only scope. CUDA packaging and broader external topology validation remain explicit release risks rather than documentation blockers.
