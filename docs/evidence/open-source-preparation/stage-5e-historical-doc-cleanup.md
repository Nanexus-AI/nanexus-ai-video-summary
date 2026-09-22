# Stage 5E — Historical documentation cleanup

## Scope and result

This documentation-only stage separated current public guidance from engineering history and
internal execution material. Runtime code, dependencies, private local Stage 9 files, and the
private `compose.cpu-openclip-gate.yaml` overlay were not modified. Nothing was staged, committed,
or pushed.

The authoritative public documents remain `README.md`, `LICENSE`, `SECURITY.md`,
`CONTRIBUTING.md`, `docs/architecture.md`, `docs/development.md`, `docs/deployment.md`,
`docs/android.md`, `docs/resource-profiles.md`, and this open-source-preparation evidence
collection. Historical records do not override those sources.

## Inventory and classification

The table covers every tracked documentation file that was outside the approved authoritative
set at the start of Stage 5E. “Stale” means that some architecture, default, milestone, or
operating detail reflects its date rather than the current project.

| Original document | Classification and treatment | Purpose and value | Stale / internal / duplicate / misleading risk |
|---|---|---|---|
| `docs/android-dev-machine.md` | **MERGE / SUPERSEDED**; removed | Former Android workstation/setup note; useful requirements were merged into `docs/android.md`. | Duplicated current Android guidance and previously carried workstation framing; retaining both risked conflicting network/setup instructions. |
| `docs/deployment-security-runbook.md` | **MERGE / SUPERSEDED**; removed | Former compact Stage 9 deployment checklist. | Process-heavy, duplicated `docs/deployment.md` and `SECURITY.md`, and could make a gate-specific command look authoritative. |
| `docs/compatibility-matrix.md` | **MERGE / SUPERSEDED**; removed | Compact Stage 9 protocol/mode matrix. | Useful boundary facts are now in architecture/deployment; commit-specific and Stage 9 framing risked becoming a false current compatibility promise. |
| `docs/rough_idea.txt` | **DELETE CANDIDATE**; removed | Early conversational product brainstorming. | Highly speculative, Frigate-first, duplicated later architecture, and contained internal/advisory language. Stage 5A explicitly classified it as internal and not for shipment. |
| `docs/m0-implementation.md` | **MOVE TO HISTORY** | Documents the first Stub event pipeline and its implementation lessons. | Old direct-Frigate architecture, commands, defaults, and milestone claims could mislead; moved and labeled historical. |
| `docs/m1-implementation.md` | **MOVE TO HISTORY** | Records the original OpenCLIP/search milestone. | Contains the old `ViT-B-32` default and legacy media flow; moved with an explicit model/default warning. |
| `docs/m2-implementation.md` | **MOVE TO HISTORY** | Records the original summary and chat milestone. | Treats rollback APIs and the legacy Event path as primary; moved and labeled historical. |
| `docs/technical-assessment-and-migration-reference.md` | **KEEP PUBLIC AS HISTORY / MOVE TO HISTORY** | Preserves the dated assessment and rationale for adopting Event Intelligence. | Large, M2-era, and partly duplicates current architecture; retained as a labeled snapshot rather than rewritten. |
| `docs/event-intelligence-migration-development-plan.md` | **KEEP PUBLIC AS HISTORY / MOVE TO HISTORY** | Preserves migration sequencing and decisions. | Contains extensive stage-gate and internal workflow language; its header now says it is not an active plan or authorization, and a link to excluded raw closeout material was removed. |
| `docs/development-progress.md` | **KEEP PUBLIC AS HISTORY / MOVE TO HISTORY** | Dated engineering diary with useful implementation chronology. | Stage-state language and test counts are time-bound; labeled as history rather than current status. |
| `docs/baseline-acceptance.md` | **KEEP PUBLIC AS EVIDENCE / MOVE TO HISTORY** | Synthetic baseline and comparison evidence. | Contains old scope/authorization language and legacy behavior; useful as dated acceptance evidence only. |
| `docs/search-stage5-acceptance.md` | **KEEP PUBLIC AS EVIDENCE / MOVE TO HISTORY** | Search migration acceptance evidence. | Stage claims and measurements are dated; clearly labeled historical. |
| `docs/summary-stage6-acceptance.md` | **KEEP PUBLIC AS EVIDENCE / MOVE TO HISTORY** | Summary migration acceptance evidence. | Stage claims and verification counts are dated; clearly labeled historical. |
| `docs/chat-stage7-acceptance.md` | **KEEP PUBLIC AS EVIDENCE / MOVE TO HISTORY** | Chat boundary and migration acceptance evidence. | Includes internal prerequisite/gate phrasing and dated repository facts; clearly labeled historical. |
| `docs/client-stage8-acceptance.md` | **KEEP PUBLIC AS EVIDENCE / MOVE TO HISTORY** | Web/Android migration acceptance evidence. | Includes dated environment and stage limitations; current client guidance lives in `docs/android.md` and architecture. |
| `docs/stage9-acceptance.md` | **EXCLUDE FROM FIRST PUBLIC RELEASE**; removed | Incomplete release-gate status summary. | Mostly task-control language and obsolete “next task” framing; durable public conclusions already appear in current docs and preparation evidence. |
| `docs/stage9-closeout-acceptance.md` | **EXCLUDE FROM FIRST PUBLIC RELEASE**; removed | Raw closeout execution record with detailed local run evidence. | Included temporary paths, image/runtime identifiers, commit-bound workflow, and unresolved internal execution instructions. Its durable conclusions are summarized in Stage 5A and this evidence record; raw CPU acceptance remains private and untouched. |
| `docs/stage9-closeout-plan.md` | **DELETE CANDIDATE**; removed | Internal gate checklist and prohibited-action list. | Process-only, not user or maintainer guidance; Stage 5A explicitly classified it as internal and not for shipment. |
| `docs/architecture-reviews/2026-08-21-contract-001-gate.md` | **KEEP PUBLIC AS HISTORY / MOVE TO HISTORY** | Early processor-contract decision record. | Gate authorization language is dated; architectural rationale remains valuable. |
| `docs/architecture-reviews/2026-08-21-contract-002-005-gate.md` | **KEEP PUBLIC AS HISTORY / MOVE TO HISTORY** | Result/capability contract decision record. | Dated stage and authorization language; retained behind a historical header. |
| `docs/architecture-reviews/2026-08-21-foundation-001-006-gate.md` | **KEEP PUBLIC AS EVIDENCE / MOVE TO HISTORY** | Cross-repository foundation acceptance. | Test counts, stage state, and implementation details are dated. |
| `docs/architecture-reviews/2026-08-21-slice-001-005-gate.md` | **KEEP PUBLIC AS EVIDENCE / MOVE TO HISTORY** | Cross-repository slice acceptance. | Dated rollback/prerequisite claims; retained as historical evidence. |
| `docs/architecture-reviews/2026-08-21-model-001-006-gate.md` | **KEEP PUBLIC AS EVIDENCE / MOVE TO HISTORY** | Provider migration and CPU baseline evidence. | Records old `ViT-B-32` and a local-run baseline; header warns these are not current defaults, and the unavailable local JSON link was replaced with a truthful note. |
| `docs/architecture-reviews/2026-08-24-chat-worker-adr.md` | **KEEP PUBLIC AS HISTORY / MOVE TO HISTORY** | Concise rationale for asynchronous chat. | Stage 7/legacy framing is dated, but the design rationale remains useful. |
| `docs/architecture-reviews/2026-08-24-client-stage8-adr.md` | **KEEP PUBLIC AS HISTORY / MOVE TO HISTORY** | Concise rationale for client/API boundaries. | Stage 8 and rollback wording is dated, but the design rationale remains useful. |

No file remained **UNCLEAR** after applying the Stage 5A classifications and checking the current
authoritative documents. The removals were limited to material already classified as internal or
fully merged/superseded; uncertain engineering records were retained.

## History structure and labeling

`docs/history/` is intentionally shallow. Milestone, migration, assessment, diary, and acceptance
records live directly under it; the existing architecture-review group is preserved as the single
subdirectory. `docs/history/README.md` states that history is non-authoritative and links to the
current public sources. Every retained historical file has a short header pointing to the most
relevant current authority. Original bodies were preserved except for relocated-link fixes, the
removal of one link to excluded raw Stage 9 material, and replacement of one unavailable local
benchmark-artifact link.

The main README was not changed to promote history.

## Stage 9 evidence treatment

The tracked Stage 9 acceptance, raw closeout record, and closeout checklist were excluded from the
first public release. They were dominated by incomplete-gate status, local execution artifacts,
and agent/task-control language rather than stable public guidance. Useful conclusions remain in
the sanitized open-source-preparation evidence: Stage 5A records the unresolved CPU/GPU,
licensing, security, and portability findings, while the current resource/deployment/security
documents state supported behavior without reproducing raw runtime evidence.

The ignored private files `docs/stage9-closeout-prompt.md`,
`docs/stage9-cpu-openclip-closeout-prompt.md`, raw
`docs/stage9-cpu-openclip-closeout-acceptance.md`, and
`compose.cpu-openclip-gate.yaml` were not modified, moved, renamed, staged, or published.

## Contradiction scan

The remaining current-facing documentation was scanned separately from `docs/history/` for:

- Frigate-first architecture presented as the current boundary;
- obsolete Event Intelligence/repository names;
- `ViT-B-32` presented as the current model default;
- M1/M2/M3 or Stage 9 presented as current project state;
- outdated trusted-network, exposure, authentication, or HTTPS instructions;
- stale API and port claims;
- stale CPU/GPU or bundled-weight claims; and
- personal absolute paths, hostnames, and private IP addresses.

No current-facing contradiction was found. Historical files still contain dated names, models,
ports, direct-Frigate flows, and stage language by design, but their file-level warnings make
their status explicit. References to the current `ViT-B-32-quickgelu` default and Android emulator
address `10.0.2.2` are intentional, as are loopback example ports documented by the current
deployment authority.

## Files moved, retained, and removed

- Moved: M0/M1/M2 reports, the technical assessment, migration plan, progress diary, five
  acceptance records, and seven architecture review/ADR records.
- Retained in place: only the approved authoritative documents and sanitized preparation evidence.
- Removed as merged/superseded: the Android workstation guide, deployment security runbook, and
  compatibility matrix.
- Removed as internal/obsolete: the rough idea draft and Stage 9 closeout checklist.
- Excluded from the first release: the tracked Stage 9 acceptance and raw closeout record.

## Unresolved human decisions

No additional historical-document decision blocks this stage. Broader release decisions already
recorded elsewhere—such as final GPU packaging validation, release artifact notices, production
authentication design, and a public vulnerability-reporting channel—remain outside Stage 5E.

## Gate recommendation

**PASS for Stage 5E.** Current public authorities are separated from labeled engineering history;
internal and superseded material is excluded with its disposition recorded; raw private evidence
remains outside the public boundary; and the current-facing contradiction scan is clean.
