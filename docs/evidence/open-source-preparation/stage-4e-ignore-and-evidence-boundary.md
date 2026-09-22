# Stage 4E — Ignore and evidence boundary

## Task scope

Protect approved private/local material from accidental staging while preserving the
sanitized public evidence directory as a visible public candidate. This work does not
promote raw evidence or change runtime behavior.

## Private and generated material protected

- Local environment files other than the public `.env.example`
- Approved private Stage 9 prompts, raw CPU OpenCLIP acceptance evidence, and the local
  CPU integration-gate Compose file
- Raw audit, SBOM, license-scan, and benchmark outputs
- Coverage data, local databases, caches, and generated data directories
- Signing keys and keystores
- Downloaded model caches and common model-weight formats
- Generated APK/AAB packages

The ignore rules are intentionally scoped so that application source, `.env.example`,
and `docs/evidence/open-source-preparation/` remain visible to Git.

## Evidence boundary

Only concise, sanitized stage records are stored in this directory. Raw scanner output,
machine-specific logs, execution prompts, local runtime identifiers, model downloads,
and private acceptance records remain local and must not enter public Git history.
Releases must be verified from a clean checkout or clone rather than by archiving the
live workspace.

## Verification performed

- The approved private Stage 9 and CPU gate files are ignored and untracked.
- `.env` and `.env.*` are ignored while `.env.example` remains public.
- Representative database, key, keystore, model-weight, APK/AAB, raw-report, and cache
  paths are ignored.
- Public source and this evidence directory are not ignored.
- No files are staged.

## Remaining responsibilities

Ignore rules reduce accidental staging risk but do not replace clean-checkout release
verification or artifact-specific review. Prebuilt containers, APK/AAB packages, model
caches, and pretrained weights remain outside the initial source-first publication.

## Gate recommendation

**PASS** — the approved private boundary is protected, sanitized evidence remains public,
and generated binary/model/database material is excluded from the source-first release.
