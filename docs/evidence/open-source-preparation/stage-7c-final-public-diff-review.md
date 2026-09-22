# Stage 7C — Final public-diff review

Date: 2026-09-20

Repository: Nanexus AI Video Summary

Baseline: `main` at `da3b7c6eb32160d927ff5101194698478da8b2de`

## 1. Executive summary

The final intended public candidate passes the current-tree exposure, current and historical
media/blob, historical privacy, commit-boundary, documentation, and sequential-tree reviews.
No credential, private key, real camera URL, real camera/field image, private-system screenshot,
model weight, application database, APK/AAB, signing material, or raw private gate evidence was
found in the intended public tree or Git history.

The approved eight-commit architecture remains internally consistent. Commit 4 now includes the
post-Stage-7B correction that preserves legacy `ai_mode`, labels it deprecated compatibility
metadata, adds the independent `model_provider`, updates Web and Android status presentation, and
adds focused health tests. Twenty-seven focused tests pass. Existing history should be preserved
with its already-documented minor privacy metadata. Stage 7C and Gate 7C are **PASS**.

No commit, push, tag, remote, configuration change, or history rewrite was made. All candidate
staging used a disposable index and object directory under `/tmp`; the repository index remained
empty.

## 2. Git identity and state

| Item | Result |
| --- | --- |
| Branch | `main` |
| HEAD | `da3b7c6eb32160d927ff5101194698478da8b2de` |
| Initial staged state | empty |
| `user.name` | `Andy Shen` |
| `user.email` | `80353459+edge-ai4cv@users.noreply.github.com` |
| name origin | global Git configuration |
| email origin | global Git configuration |
| repository-local override | none |

The effective identity exactly matches the approved future identity. Configuration was not
modified.

## 3. Current-tree exposure audit

The complete tracked and non-ignored candidate was scanned by content and path. Findings are
limited to safe, intentional material:

- `nanexus` local-development database passwords in loopback/trusted-development Compose;
- required deployment-variable placeholders such as `VIDEO_DB_PASSWORD` and `EVENT_DB_PASSWORD`;
- the Android emulator host alias `10.0.2.2` and the illustrative `192.168.x.x` pattern;
- the approved noreply address and historical findings described in sanitized evidence;
- package URLs, versions, hashes, and disposable verification paths in evidence.

No actual credential/token/key, real RTSP URL, real device/camera/NVR identifier, concrete private
infrastructure value, live personal absolute path, workstation value, local database/log, model
weight/cache, APK/AAB, signing material, private gate Compose file, or raw Stage 9 prompt/evidence
is included. `.env`, private gate inputs, caches, generated output, databases, logs, weights,
Android signing/output material, and raw verification material remain ignored. There is no current
publication blocker.

## 4. Current image/media audit

The intended public tree contains **no image, raster, SVG, audio, video, screenshot, APK/AAB,
model-weight, or media fixture asset** requiring classification. The only database-like file found
in the working directory was an ignored generated `.mypy_cache/3.12/cache.db`, outside the public
candidate. Consequently there are no real people, vehicles, homes/private property, camera views,
locations, UI environment data, IP addresses, usernames, or device identifiers embedded in a
current media asset. The publication-default prohibition on real field imagery is satisfied.

## 5. Historical image/media/blob audit

All reachable Git objects were inventoried by path, type, and size, including deleted paths. Git
history contains no image, SVG, audio, video, screenshot, APK/AAB, database, model weight, raw
capture, or other media object. The only historical blobs at least 100 KiB are versions of
`uv.lock` and `web/package-lock.json`; both are ordinary text dependency locks. No sensitive
historical binary exists, so history cleanup is not required.

## 6. Historical text/privacy result

The Stage 7A findings are unchanged:

- **A — cosmetic/non-sensitive metadata:** historical personal author/committer email, local
  workstation hostname, and `<local-sdk-path>`;
- **B — internal but non-sensitive examples:** historical RFC1918 private-network examples;
- **C — sensitive content requiring intervention:** none.

No new evidence raises their severity. The address examples are not credentials or proof of a
reachable system, and the approved strategy is to preserve history.

## 7. Final eight-commit review

Each candidate was reconstructed from the empty baseline index, its complete cached diff was
reviewed, and `git diff --cached --check` passed. The identities below are Git tree IDs.

| # | Proposed subject | Final tree | Result |
| --- | --- | --- | --- |
| 1 | `feat(model): complete CPU OpenCLIP closeout` | `ccbbca049b1f4e39042f67f4cba9fff1c2cce59f` | PASS |
| 2 | `feat(model): add explicit CPU and CUDA execution profiles` | `7845444dd68f9705956445b56c69710229075684` | PASS |
| 3 | `feat(integration): align public Event Intelligence subject paths` | `8de238d4977bad769145c24c152aa3aaea02aaf3` | PASS |
| 4 | `fix(runtime): harden container and trusted-network boundaries` | `66d6d1d2d8b0020697ef399b94710598f4aa8225` | PASS |
| 5 | `chore(project): add Apache-2.0 and contribution metadata` | `b00cb5760c0718c960323c06cb6bdccbb9b28daa` | PASS |
| 6 | `docs: publish current architecture and operator guidance` | `45f1a8bb7608217c92f0896074b015009f2ed96c` | PASS |
| 7 | `docs(history): archive superseded engineering records` | `ce726c50655591128b6a67f4a8f6838b42759d0c` | PASS |
| 8 | `docs(evidence): record open-source preparation verification` | `2f210d7163aa58873c470cef6a736413ff4b0a6b` before this self-referential Stage 7C record | PASS |

Commit 1 contains the CPU/QuickGELU foundation, benchmark, cache persistence, configuration and
tests, with no later-profile material. Commit 2 keeps the CPU profile intact, isolates CUDA
dependencies and container behavior, requires no host CUDA for the CPU profile, and contains no
documentation/history/evidence. Commit 3 contains only the Video Summary consumer side of the
canonical ReviewItem, subject, Search/Chat and evidence-proxy contract; its separate Event
Intelligence contract dependency must land first.

Commit 4 owns `.dockerignore`, nginx static serving, loopback/trusted-network hardening, additive
`model_provider`, explicit legacy-`ai_mode` observability, Python/Web/Android health presentation,
and focused health tests. It contains neither Commit 1 model-foundation hunks nor Commit 3 subject
path hunks nor broad operator documentation. Commit 5 is limited to Apache-2.0, packaging,
security, contribution, and ignore metadata. Commit 6 is authoritative current documentation.
Commit 7 retains only clearly marked non-authoritative history and moves no media/private evidence.
Commit 8 contains sanitized preparation evidence, not raw runtime captures or private artifacts.

The Commit 8 tree ID necessarily changes when this report is added; embedding that final tree ID
inside the file would recursively change the ID. The final post-report identity is therefore
reported in the Stage 7C handoff, following the same non-self-referential practice used in Stage
7B.

## 8. Sequential-tree sanity

The eight candidate path/hunk sets cover the complete intended public delta. Shared files are
split only at the previously approved hunk boundaries: `.env.example`, `compose.release.yaml`,
`pyproject.toml`, `services/api/main.py`, `src/nanexus/providers/openclip.py`, and
`src/nanexus/schemas.py`. Review found no missing or duplicated hunk, no file assigned to an
unrelated commit, no unassigned public candidate, and no intermediate private exposure.

The complete candidate before adding this record has tree identity
`d5867d9271ae861b2dca370866392c3a57711eeb` and 103 changed paths. This equals the intended public
worktree at that point. A temporary-index full-tree `git diff --cached --check` passed. The final
post-report public tree identity is recorded in the handoff because of the report's self-reference.

## 9. README three-theme review

**Application value — PASS.** README contrasts traditional storage/timeline/playback/isolated
alert workflows with normalized higher-level summaries, semantic Search, cited Chat, evidence
resolution, subject traceability, and reduced manual review.

**Capabilities and UI maturity — PASS.** README describes Summary, Search, Chat, citations,
evidence, subject linking, Web, Android, CPU OpenCLIP, and GPU/CUDA OpenCLIP. Web and Android are
functional reference interfaces, not finished/productized UX; this framing does not diminish the
implemented upper application.

**Event Intelligence relationship — PASS.** README describes vendor-neutral, platform-neutral
Event Intelligence middleware as the independent stable public-contract boundary:
source-specific camera/NVR/VMS systems → Event Intelligence → higher-level applications such as
Video Summary. It accurately distinguishes EI observation
`/api/v1/events/{observation_id}`, EI ReviewItem
`/api/v1/review-items/{review_item_id}`, and Video Summary subject
`/api/v1/subjects/{review_item_id}`. CPU and GPU/CUDA validation are both stated.

## 10. Verification and npm/security carry-forward

Focused health, client, public-path, provider, device, and GPU-profile tests pass: **27 passed**
with two known FastAPI `on_event` deprecation warnings. The warning does not affect candidate
behavior or publication safety.

The existing Web audit remains **3 advisories: 2 moderate and 1 high**, in the development/test
toolchain (`vitest`, transitive `@vitest/mocker`, and transitive `js-yaml`). Prior production-bundle
inspection found no test-toolchain payload in shipped application code. No new evidence changes
the release-risk classification: track and update the test toolchain, but this is not a demonstrated
production-runtime exposure or Gate 7C blocker. `npm audit fix` was not run.

## 11. Publication and gate recommendation

History recommendation: **B — Preserve history with documented minor privacy metadata.** No real
sensitive historical image/blob or credential exists, so C/D and history rewrite are unwarranted.

Gate 7 blockers: **none**. The Event Intelligence canonical ReviewItem contract is an ordering
dependency: its separately reviewed change/release must precede Video Summary Commit 3. It is not
part of this repository and must not be merged into these commits.

Stage 7C verdict: **PASS**.

Gate 7C recommendation: **PASS**.

## 12. Final state

HEAD remains `da3b7c6eb32160d927ff5101194698478da8b2de` on `main`. The real repository index is empty.
The intentionally dirty worktree is preserved, and this file is the only Stage 7C repository
addition. No commit, push, tag, remote, history rewrite, or Stage 7D action occurred.
