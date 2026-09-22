# Stage 5A — Documentation inventory and information architecture

## Scope and summary

This was a documentation-only inventory and source-of-truth review. The repository has useful
architecture, migration, client, deployment, and acceptance material, but its public entry points
still mix the original Frigate-first M0–M3 prototype with the later Event Intelligence-backed
application. The first public release needs a small authoritative documentation set; milestone,
gate, and assessment material should not remain the primary setup or architecture guidance.

No runtime, dependency, architecture, historical document, or public guide was changed in this
stage. This record is the only new file; the existing evidence index was updated to link it.

## Documentation inventory and classification

Classification reflects treatment for the first public source release, not the value of a file as
engineering history.

| Document | Classification | First-release treatment |
|---|---|---|
| `README.md` | NEEDS REWRITE | Replace the M2/Frigate-first entry point with the content map below. |
| `LICENSE` | PUBLIC CORE | Ship unchanged as the Apache-2.0 license. |
| `.env.example` | PUBLIC REFERENCE | Keep as the commented configuration inventory; align future guides to it. |
| `docs/architecture.md` | NEEDS REWRITE / NEEDS MERGE | Preserve current boundary decisions; remove obsolete original roadmap/design as authority. |
| `docs/android-dev-machine.md` | NEEDS MERGE | Merge into `docs/android.md`; retain JDK 17, SDK, emulator, Debug/Release network behavior. |
| `docs/deployment-security-runbook.md` | NEEDS REWRITE / NEEDS MERGE | Split deployment procedure into `deployment.md` and the security boundary into `SECURITY.md`. |
| `docs/resource-profiles.md` | NEEDS REWRITE | Keep as the resource authority, but retract the claim that CPU/GPU dependency routing is solved. |
| `docs/compatibility-matrix.md` | PUBLIC REFERENCE | Keep compact compatibility data; remove Stage 9 framing and commit-specific pinning when releases exist. |
| `docs/rough_idea.txt` | INTERNAL / SHOULD NOT SHIP | Early conversational design draft, duplicated and obsolete. |
| `docs/m0-implementation.md` | PUBLIC HISTORICAL / ARCHIVE | Reduce/move later; old setup commands must not remain normative. |
| `docs/m1-implementation.md` | PUBLIC HISTORICAL / ARCHIVE | Reduce/move later; contains stale model/default and legacy media behavior. |
| `docs/m2-implementation.md` | PUBLIC HISTORICAL / ARCHIVE | Reduce/move later; describes rollback APIs as the main product. |
| `docs/technical-assessment-and-migration-reference.md` | NEEDS MERGE / PUBLIC HISTORICAL | Mine rationale into architecture/development; archive the dated M2 assessment. |
| `docs/event-intelligence-migration-development-plan.md` | PUBLIC HISTORICAL / ARCHIVE | Preserve a reduced migration history, not a 1,653-line public development guide. |
| `docs/development-progress.md` | PUBLIC HISTORICAL / ARCHIVE | Convert later to concise history/release notes; it is not setup documentation. |
| `docs/baseline-acceptance.md` | EVIDENCE | Retain only in a clearly labeled historical/evidence collection. |
| `docs/search-stage5-acceptance.md` | EVIDENCE | Same treatment. |
| `docs/summary-stage6-acceptance.md` | EVIDENCE | Same treatment. |
| `docs/chat-stage7-acceptance.md` | EVIDENCE | Same treatment. |
| `docs/client-stage8-acceptance.md` | EVIDENCE | Same treatment. |
| `docs/stage9-acceptance.md` | EVIDENCE / NEEDS SANITIZATION | Preserve the incomplete-gate facts; remove workflow instructions from public guidance. |
| `docs/stage9-closeout-plan.md` | INTERNAL / SHOULD NOT SHIP | Internal gate checklist; useful facts belong in sanitized evidence. |
| `docs/stage9-closeout-prompt.md` (ignored local file) | INTERNAL / SHOULD NOT SHIP / NEEDS SANITIZATION | Raw execution prompt with workstation layout, repository history, and internal process language. Keep untracked and exclude. |
| `docs/stage9-closeout-acceptance.md` | EVIDENCE / NEEDS SANITIZATION | Reduce to sanitized evidence; retain unresolved CPU/GPU and release blockers. |
| `docs/architecture-reviews/2026-08-21-contract-001-gate.md` | PUBLIC HISTORICAL / ARCHIVE | Keep as an ADR/gate record, outside core navigation. |
| `docs/architecture-reviews/2026-08-21-contract-002-005-gate.md` | PUBLIC HISTORICAL / ARCHIVE | Same treatment. |
| `docs/architecture-reviews/2026-08-21-foundation-001-006-gate.md` | PUBLIC HISTORICAL / ARCHIVE | Same treatment. |
| `docs/architecture-reviews/2026-08-21-slice-001-005-gate.md` | PUBLIC HISTORICAL / ARCHIVE | Same treatment. |
| `docs/architecture-reviews/2026-08-21-model-001-006-gate.md` | PUBLIC HISTORICAL / ARCHIVE / NEEDS SANITIZATION | Keep decisions; remove unavailable linked artifact and machine-specific benchmark caveats. |
| `docs/architecture-reviews/2026-08-24-chat-worker-adr.md` | PUBLIC REFERENCE | Retain as a concise accepted ADR. |
| `docs/architecture-reviews/2026-08-24-client-stage8-adr.md` | PUBLIC REFERENCE | Retain as a concise accepted ADR. |
| `docs/evidence/open-source-preparation/README.md` and `stage-0` through `stage-4e` | EVIDENCE | Ship as the sanitized evidence index/records after a final consistency review. |

There is no standalone API reference file. FastAPI exposes generated API documentation at
`/docs`; the stable `/api/v1` contract and legacy/rollback distinction should be described once in
development documentation and linked from the README. Dependency manifests such as
`requirements.txt`, `pyproject.toml`, lock files, Gradle files, and `web/package.json` are source
truth, not prose documentation.

Ignored local files `docs/stage9-closeout-prompt.md`,
`docs/stage9-cpu-openclip-closeout-prompt.md`,
`docs/stage9-cpu-openclip-closeout-acceptance.md`, and `compose.cpu-openclip-gate.yaml` are private
raw evidence and are not tracked. They must remain excluded from the first release.

## Duplication, stale claims, and conflicts

- Setup is duplicated across README, M0/M1/M2 reports, Android notes, architecture, and the
  deployment runbook. Commands mix the legacy multi-process demo, slice integration, and release
  Compose profiles without naming which is authoritative.
- Architecture is duplicated between `rough_idea.txt`, `architecture.md`, the technical
  assessment, migration plan, compatibility matrix, and ADR/gate records. The first half of
  `architecture.md` still describes Frigate as the direct foundation, iOS/HA as planned clients,
  and M0–M4 milestones; later sections describe the current Event Intelligence boundary.
- `README.md` says the project is currently M2 and “next M3,” despite completed Stage 5–9 work and
  Web/Android v1 clients. It also says “four services” and then lists five.
- `Nanexus Video Summary` survives in migration/assessment titles; the public product name is
  `Nanexus AI Video Summary`. The obsolete repository name `nanexus_frigate_extension` survives in
  the tracked raw Stage 9 prompt and in ignored private gate material.
- M1 documents `ViT-B-32/openai`; current configuration uses
  `ViT-B-32-quickgelu/openai`. Older acceptance evidence correctly remains historical and must not
  be presented as the current default.
- Old documents describe direct Frigate MQTT/media access, file snapshots, legacy `Event`, and
  synchronous `/search` and `/chat` as primary behavior. Current v1 product paths depend one-way on
  Event Intelligence public HTTP contracts; those older paths are rollback/history.
- `docker-compose` fallback/install directions and hand-started legacy processes are historical,
  not the intended public release workflow.
- Security prose is mostly consistent on trusted-network operation, but README/Android examples
  instruct binding the API to `0.0.0.0`, while release Compose publishes Web/API only on loopback.
  Future docs must distinguish container-internal listening, loopback publication, and an
  explicitly protected LAN demo.
- `resource-profiles.md` claims Linux CPU wheels exclude CUDA packages and presents a GPU profile as
  available. Current `pyproject.toml` routes Linux `torch` and `torchvision` to an explicit CPU
  index, so CPU support is represented but the required CUDA dependency route is not. The
  CPU/GPU packaging issue is unresolved and must not be documented as solved.
- OpenCLIP weights are not bundled. `open-clip-torch` loads the configured pretrained variant on
  first use and the release profile mounts `/root/.cache`; this can require outbound download.
  Historical locally-cached runs do not establish a redistributable bundled model artifact.
- Stage/gate instructions, prohibitions, commit hashes, workstation layouts, and “do not begin the
  next stage” language are internal process material, not user documentation.

## Proposed public information architecture

| Target | Audience and purpose | Merge from | Do not copy |
|---|---|---|---|
| `README.md` | Evaluators and first-time operators; accurate overview, status, boundaries, safe demo, and links. | Current capabilities, security paragraph, Event Intelligence boundary, Android basics. | M-number claims, raw gate history, exhaustive configuration, unverified production claims. |
| `LICENSE` | All users and redistributors; Apache-2.0 terms. | Existing license only. | Weight/dependency license conclusions or artifact notices. |
| `CONTRIBUTING.md` | Contributors; workflow, tests, style, change boundaries. | Reproducible development facts from M0 reports and progress records. | Internal approvals, personal paths, release-gate prompts. |
| `SECURITY.md` | Deployers and vulnerability reporters; trusted-network boundary, supported reporting path, exposure limits. | Security runbook and Stage 4C evidence. | Secrets, example real tokens, claims of a complete public gateway. |
| `docs/architecture.md` | Contributors/integrators; current components, ownership, flows, boundaries, rollback status. | Current tail of architecture, accepted ADRs, compatibility facts. | Original speculative roadmap, direct-Frigate architecture as current, implementation diary. |
| `docs/development.md` | Contributors; pinned toolchains, setup, focused services/tests, generated API docs. | M0 setup facts, manifests, relevant migration lessons. | Production deployment, old Compose installer workaround, stage authorization language. |
| `docs/deployment.md` | Trusted-network deployers; supported Compose entry points, configuration, ports, secrets, upgrades, backups. | Deployment runbook, `.env.example`, compatibility matrix. | Public-internet assurances, raw failure drills, private infrastructure details. |
| `docs/android.md` | Android developers/operators; requirements, build, pairing, emulator/device networking, Debug/Release security. | `android-dev-machine.md`, client ADR/acceptance facts. | APK publication promises, generic backend setup, private LAN addresses. |
| `docs/resource-profiles.md` | Capacity planners; Stub/CPU/GPU/LLM requirements, model cache/download behavior, known limits. | Existing table and measured sanitized evidence. | Claim that CUDA routing is complete, universal performance promises, bundled-weight implication. |
| `docs/evidence/open-source-preparation/` | Reviewers/maintainers; concise sanitized preparation evidence. | Existing Stage 0–5A records. | Raw prompts/logs, machine identifiers, secrets, private Stage 9 artifacts. |
| `docs/history/` (only if history is shipped) | Maintainers/researchers; reduced migration and milestone record. | M0–M2, progress, plans, acceptance and gate records. | Duplicate setup instructions or anything presented as current authority. |

Event Intelligence integration belongs in architecture plus an operational subsection of
deployment; a separate small document is not justified yet. API details should remain generated
from the application and be linked from development rather than copied into a manually maintained
endpoint catalogue.

## Future README content map

1. **Title and one-sentence scope** — application for security-camera event understanding, search,
   summaries, chat, Web, and Android.
2. **Why it exists** — user problem and application-layer value without accuracy claims.
3. **Architecture at a glance** — Camera/NVR/VMS → Event Intelligence → AI Video Summary → clients.
4. **Nanexus Event Intelligence** — separate Apache-2.0 middleware; public HTTP/v1 boundary;
   optional local source checkout via `EVENT_INTELLIGENCE_SOURCE_DIR`.
5. **Project status: working today** — verified v1 Summary/Search/async Chat, Web/Android, Stub and
   CPU OpenCLIP behavior, with legacy paths labeled rollback-only.
6. **Experimental and not guaranteed** — model quality, production-scale operation, GPU packaging,
   cloud LLMs, and unfinished retirement/publication work.
7. **Security model** — trusted internal network, internal-only services, deployer-owned external
   access controls, no complete public-network gateway claim.
8. **Resource profiles** — short Stub/CPU/GPU/LLM overview linked to the resource guide.
9. **OpenCLIP and model weights** — embeddings/zero-shot labels (not a free-form caption VLM),
   configured model/pretrained pair, first-use download/cache, no bundled weights.
10. **CPU versus GPU/CUDA** — both required goals; CPU current route and CUDA dependency routing
    explicitly unresolved.
11. **Safe local demo** — one authoritative, loopback-first Stub command path with prerequisites,
    expected URL, teardown, and no cloud key/model download.
12. **Connect Event Intelligence** — external service URL/token first; optional local checkout
    integration second.
13. **Web access** — public Video Summary API only, loopback default, reverse-proxy responsibility.
14. **Android access** — emulator `10.0.2.2`, configurable device URL, Debug HTTP versus Release
    HTTPS.
15. **What is not distributed** — no pretrained weights, prebuilt images, APK/AAB, populated cache;
    later binary/container artifacts need their own SBOM/notices.
16. **Documentation links** — architecture, development, deployment, security, Android, resource
    profiles, evidence, and generated API docs.
17. **License** — repository Apache-2.0; third-party models/dependencies remain under their own
    terms.

## Historical-document decisions

- Reduce M0/M1/M2 reports into an optional history area; never use their setup/default tables as
  current guidance.
- Reduce `development-progress.md` and the migration plan into a dated migration narrative, or
  exclude them from the first release if maintainers do not want to support an engineering diary.
- Merge durable rationale from the technical assessment into current architecture/development,
  then archive the assessment as a dated snapshot.
- Keep acceptance records and architecture gates only as clearly labeled evidence/history. The two
  short accepted ADRs have continuing reference value.
- Exclude raw Stage 9 prompt/checklist material. Convert the closeout acceptance into sanitized
  evidence only, retaining unresolved findings without local paths, hashes used as environment
  assumptions, or task-control language.
- Do not delete or move any of these files until the Stage 5B rewrite/archive decision is approved.

## Authoritative-document mapping

| Topic | Authority after rewrite |
|---|---|
| Architecture and component ownership | `docs/architecture.md` |
| Development setup and generated API reference | `docs/development.md` |
| Deployment, Compose entry points, ports, upgrades | `docs/deployment.md` |
| Security and exposure boundary | `SECURITY.md` |
| Android setup/connectivity | `docs/android.md` |
| Resource sizing | `docs/resource-profiles.md` |
| Event Intelligence integration | Architecture for contract boundary; deployment for configuration |
| CPU/GPU and OpenCLIP runtime behavior | `docs/resource-profiles.md`, backed by manifests/configuration |
| Model/provider behavior | Architecture for semantics; resource profiles for acquisition/cache |
| License | `LICENSE` (README only summarizes) |
| Open-source preparation evidence | `docs/evidence/open-source-preparation/` |

## Repository truthfulness findings

- Package version is `0.3.0`; Web is `0.4.0`; Android is `0.1.0` (`versionCode 1`). A single
  cross-client release version is not currently defined.
- Python is exactly the 3.12 line (`.python-version` 3.12 and `>=3.12,<3.13`). Node is 22.14.0.
  Android uses Gradle 8.9, Android Gradle Plugin 8.7.3, Kotlin 2.0.21, JDK/JVM 17, compile/target
  SDK 35, and minimum SDK 26.
- Current OpenCLIP default is `ViT-B-32-quickgelu` with pretrained variant `openai`. The external
  provider default is Stub; legacy `AI_MODE` separately defaults to OpenCLIP. Documentation must
  distinguish these paths.
- Integration configuration uses `EVENT_INTELLIGENCE_URL`, `EVENT_INTELLIGENCE_TOKEN`, timeout and
  poll settings; integrated/slice source builds additionally use `EVENT_INTELLIGENCE_SOURCE_DIR`.
  Release Compose uses `PROCESSOR_API_TOKEN` to populate the service token.
- API listens internally on 8000; model service on 8010; release Web is published at loopback 8080
  and API at loopback 8000. Local infrastructure publishes PostgreSQL 5432, Redis 6379, and MQTT
  host port 1884 only on loopback. Event Intelligence internal service uses 8000; its example
  browser-safe public URL is 8001.
- Android Debug defaults to `http://10.0.2.2:8000` and permits cleartext; Release defaults to an
  invalid HTTPS placeholder, rejects HTTP, and disables cleartext. The current Android guide is
  accurate on this point.
- `docker-compose.yml` starts legacy local infrastructure. `compose.release.yaml` is the integrated
  or external-foundation release topology; `compose.slice.yaml` is synthetic integration evidence;
  `compose.search.yaml`/`compose.model.yaml` are migration-era overlays. These roles are not clearly
  explained in current public docs.
- OpenCLIP model creation passes `pretrained=openai`, so a missing cache can trigger upstream weight
  acquisition. Release Compose persists `/root/.cache`; no populated cache or weights are part of
  the source release.
- Internal services listen on `0.0.0.0` inside containers/processes, while release host publication
  is loopback-only. A LAN demo requires a deliberate binding/firewall decision and remains within
  the trusted-network boundary.

## Human decisions required

1. Whether reduced milestone/migration history ships in `docs/history/` or is excluded initially.
2. Whether any sanitized Stage 9 acceptance record is valuable publicly beyond the open-source
   preparation evidence.
3. Which safe Stub topology is the single supported local-demo command for the first release.
4. Whether package, Web, and Android versions should remain independent or share a release version.
5. What public vulnerability-reporting contact/process belongs in the future `SECURITY.md`.
6. How GPU/CUDA dependencies will be routed and verified; documentation cannot resolve this code
   and packaging decision.

## Gate recommendation

**PASS for Stage 5A inventory.** The important documents are classified, the future authoritative
structure and README map are defined, and source checks identify the current contradictions.
Stage 5B should not present GPU/CUDA packaging as complete, should exclude raw Stage 9 prompt
material, and should obtain the human decisions above before destructive archive/move work.
