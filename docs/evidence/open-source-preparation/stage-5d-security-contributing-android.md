# Stage 5D — security, contributing, and Android documentation

## Scope

Stage 5D added public maintainer documentation and minimal cross-links only. It did not change runtime code, dependencies, build artifacts, staging, commits, publication, or Stage 5E material.

## Files created and updated

Created `SECURITY.md`, `CONTRIBUTING.md`, and `docs/android.md`. Updated only documentation links and short navigation text in `README.md`, `docs/development.md`, `docs/deployment.md`, and `docs/architecture.md`.

## Decisions

- **Security reporting:** repository inspection found no documented security mailbox, Git hosting remote, `.github` security configuration, or evidence that private vulnerability reporting is enabled. The guide therefore asks reporters to open only a minimal non-sensitive issue requesting private instructions once a public tracker exists, or wait for a published channel. It explicitly prohibits public secrets, exploit payloads, private addresses, camera URLs, and customer data.
- **Contribution boundary:** contributions use Apache-2.0 terms without inventing a CLA, DCO, branch-protection, CI, or release-automation requirement. Guidance keeps changes focused and preserves the public HTTP/v1 boundary with the separate Event Intelligence project.
- **Android consolidation:** the new guide records the declared JDK, SDK, Gradle, AGP, Kotlin, and app versions; build and test commands; emulator and physical-device connectivity; debug HTTP versus Release HTTPS behavior; local configuration and signing boundaries; ignored outputs; troubleshooting; and the source-first no-APK/AAB release boundary. `docs/android-dev-machine.md` remains present but is identified as non-authoritative.

## Cross-links

README navigation now links all three documents. Development links contribution, security, and Android guidance; Deployment links security and Android guidance; Architecture links the security and Android boundaries.

## Unresolved items

- A private vulnerability-reporting channel and public repository issue tracker are not currently evidenced.
- GPU/CUDA dependency routing and release validation remain unresolved; the default Linux dependency path is CPU-oriented.
- No initial project-published Docker images or Android APK/AAB artifacts are provided.
- Android public release signing and store automation are not configured.

## Verification

- Reviewed the complete contents of `SECURITY.md`, `CONTRIBUTING.md`, and `docs/android.md` against current Gradle, manifest, Kotlin configuration, lockfiles, README, architecture, development, deployment, and ignore rules.
- Checked Apache-2.0 wording against `LICENSE` and `pyproject.toml`.
- Verified reporting language against available repository hosting/configuration evidence.
- Ran `git diff --check` and verified local relative documentation links.

## Gate recommendation

**PASS** — the Stage 5D maintainer documentation is complete and consistent with the current source-first, trusted-network, and cross-repository boundaries. The unresolved reporting channel, CUDA validation, and release-artifact publication remain explicit follow-up items rather than documentation blockers.
