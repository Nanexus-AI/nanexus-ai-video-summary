# Stage 4A: License and provenance evidence

## Task scope

Add the approved Apache-2.0 project license and standard Python metadata, document the Event Intelligence contract mirror's provenance, and verify the approved private/local Stage 9 boundary.

## Files changed

- `LICENSE`
- `pyproject.toml`
- `src/nanexus/event_intelligence_contracts/__init__.py`
- `docs/evidence/open-source-preparation/stage-4a-license-and-provenance.md`

## Decisions

- **Apache-2.0:** The repository uses the unmodified standard Apache License 2.0 text. Python project metadata declares the `Apache-2.0` SPDX expression and includes `LICENSE` through `license-files`. No `NOTICE` was added because no current project-owned material was identified as requiring one; third-party notice review remains later work.
- **Event Intelligence provenance:** Nanexus Event Intelligence is the normative, Apache-2.0-licensed Nanexus-owned source of the public v1 contract. This repository's Nanexus-owned representation is a consumer mirror and must track, not independently redefine, that contract.

## Private-boundary files verified

The following remained untracked and unstaged and were not modified by Stage 4A:

- `docs/stage9-closeout-prompt.md`
- `docs/stage9-cpu-openclip-closeout-prompt.md`
- `docs/stage9-cpu-openclip-closeout-acceptance.md`
- `compose.cpu-openclip-gate.yaml`

Their repository-adjacent filenames create an accidental-staging risk to address in Stage 4E without changing `.gitignore` in this task.

## Verification commands

- `git status --short`
- `git diff --check`
- `git diff -- LICENSE pyproject.toml src/nanexus/event_intelligence_contracts docs`
- `git diff --cached --name-status -- <private-boundary files>`
- `git ls-files --stage -- <private-boundary files>`

No runtime source behavior changed, so focused runtime tests were not required.

## Remaining risks

- Third-party dependency and notice obligations still require their later dedicated review.
- The approved local Stage 9 files remain vulnerable to broad staging until Stage 4E.

## Gate recommendation

**PASS** — Stage 4A is ready for owner review, provided final diff and private-boundary checks remain clean.
