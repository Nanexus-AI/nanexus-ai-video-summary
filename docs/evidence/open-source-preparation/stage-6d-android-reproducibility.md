# Stage 6D Android reproducibility verification

Date: 2026-09-19
Repository: Nanexus AI Video Summary
Scope: isolated Android execution and verification only

## Executive summary

The reviewed public Android candidate is reproducible with JDK 17, the declared Gradle 8.9
wrapper, Android Gradle Plugin 8.7.3, Kotlin 2.0.21, and installed Android SDK 35 tooling. A
fresh-cache dependency resolution succeeded, all 6 Debug unit tests passed, Debug lint passed
with 0 errors and 7 understood non-blocking warnings, and a clean Debug APK build succeeded.

The build used a disposable `local.properties`, isolated Gradle state, and, for the final clean
build, isolated Android user state that generated its own standard disposable Debug keystore.
No personal SDK path, signing secret, build output, or cache was copied into the candidate.
Source hashes remained unchanged and the main worktree stayed on the same HEAD with an empty
index. Stage 6E was not started.

## Clean candidate and identity

- Source branch and HEAD before construction: `main` at
  `da3b7c6eb32160d927ff5101194698478da8b2de`.
- The source index was empty; `git diff --cached --name-status` had no entries.
- A detached temporary worktree was created from that exact HEAD. The reviewed binary-safe
  tracked diff was applied and the 45 public untracked paths approved through Stage 6C were
  copied individually. Ignored material was excluded by construction.
- Tracked-patch SHA-256:
  `e0f52240531852e2e8db9760f56a7b01b926c0080fc1132024ae59eb8869409a`.
- The pre-build candidate manifest covered 202 files: 138 unchanged HEAD files, 19 files from
  the tracked patch, and 45 allowlisted public untracked files. Each entry recorded origin,
  size, SHA-256, and candidate-relative path.
- Candidate-manifest SHA-256:
  `3f42abd1f3289b839e80c809049f2ca8ff5f0452821e1e45c35c95ce9c8a99f5`.
- A post-verification comparison found zero mismatches among the 202 manifested source files.
- The initial candidate contained no `local.properties`, `.env`, keystore, APK/AAB, project
  build directory, project Gradle cache, signing password, or private Stage 9 material.

## Android and Java baseline

| Component | Verified value |
|---|---|
| Application version | 0.1.0 (`versionCode` 1) |
| Java | Eclipse Temurin OpenJDK 17.0.20 |
| Gradle wrapper | 8.9 |
| Android Gradle Plugin | 8.7.3 |
| Project Kotlin plugins | 2.0.21 |
| Java/Kotlin bytecode target | 17 |
| Compile SDK | 35 |
| Target SDK | 35 |
| Minimum SDK | 26 |
| Installed SDK platform | Android 35 |
| Installed build tools | 34.0.0 and 35.0.0 |

The Gradle distribution reports its own embedded Kotlin as 1.9.23; that is distinct from the
project's explicitly configured Kotlin Android/Compose/serialization plugin version 2.0.21.
No global Java setting was changed.

## `local.properties` independence

- `android/local.properties` is not tracked and is ignored by the repository.
- No absolute personal path appears in tracked Android configuration.
- The candidate started without this file. A disposable file containing the available SDK
  location was created inside the isolated candidate only, rather than copying the source
  worktree's personal file.
- All checks succeeded with that developer-supplied location. The file was classified as
  disposable local machine configuration and removed with the candidate.

This verifies that a developer supplies their own SDK path and that the source does not depend
on the original machine's path.

## Dependency resolution

The wrapper first attempted to use a completely fresh isolated Gradle user home. Network access
was required to download the declared Gradle 8.9 distribution and artifacts from the configured
Gradle Plugin Portal, Google, and Maven Central repositories. A sandboxed attempt was blocked
before download; the same declared workflow succeeded when public repository access was
allowed. `app:dependencies` then completed successfully.

The build defines dependencies directly in `app/build.gradle.kts`; it has no dependency lock
files or version catalog to update. The root build file, app build file, and wrapper properties
were byte-identical after resolution. No upgrade, version substitution, audit fix, or SDK-level
change was made. A later `assembleDebug` confirmation succeeded in offline mode from the fresh
cache.

## Unit tests

The task inventory defines `app:test`, `app:testDebugUnitTest`, and
`app:testReleaseUnitTest`, separately from connected/device instrumentation tasks. The normal
Debug verification task was run:

| Task | Tests | Passed | Failed | Errors | Skipped |
|---|---:|---:|---:|---:|---:|
| `./gradlew testDebugUnitTest` | 6 | 6 | 0 | 0 | 0 |

Compilation emitted two non-failing Kotlin warnings: a deprecated non-auto-mirrored Send icon
in application code and redundant `Json` construction in a test. No emulator or device was
required. Connected/device test tasks are defined by the Android plugin, but the repository has
no `androidTest` source files; instrumentation was therefore classified separately and not run
as unit testing.

## Android lint

`./gradlew lintDebug` completed successfully. Its generated text, XML, and HTML reports were
kept only in the disposable candidate build tree.

- Errors: 0.
- Warnings: 7.
- Six warnings report newer available AndroidX dependency versions. Versions were intentionally
  not changed in this reproducibility stage.
- One warning reports the Debug variant's cleartext base configuration. This is understood and
  intentional for the emulator/local trusted-network developer workflow. The Release variant
  instead disables cleartext traffic.

No lint rule, baseline, source, or dependency version was changed to obtain the result.

## Debug build

`./gradlew assembleDebug` completed successfully. A final clean build was also run with both
the Gradle user home and Android user home isolated; it generated a fresh standard disposable
Debug keystore and completed without network access from the populated isolated cache.

- Output: one Debug APK under `android/app/build/outputs/apk/debug/` only.
- Size: 18,385,318 bytes.
- Final inspected APK SHA-256:
  `fd88e3e53680b88cef27ff67bc07ffd55b32cb72377f28a907cbd7237768d4b4`.
- APK signature verification passed using the normal Debug v2 signature.
- No custom or release keystore and no private signing value was required.
- Generated `BuildConfig` contained version 0.1.0 and the intended Debug default
  `http://10.0.2.2:8000`.

The APK was inspected in place and was not copied into tracked source or documentation.

## Release and signing boundary

No release APK or AAB was built or published. Inspection found no Gradle signing configuration,
keystore filename, password, alias, or signing secret in the public Android source. References
to Android's platform keystore API implement runtime token storage and are unrelated to APK
signing.

The Release manifest sets `usesCleartextTraffic="false"` and uses the main network-security
configuration, whose base configuration also sets `cleartextTrafficPermitted="false"`. Release
`BuildConfig` uses the HTTPS placeholder `https://nanexus.invalid`, and `ApiClient` rejects a
non-HTTPS base URL whenever `BuildConfig.DEBUG` is false. A source checkout therefore does not
pretend to contain production endpoint or signing credentials. Source-first release remains the
only claim made here.

## Endpoint and security verification

- Debug emulator default: `http://10.0.2.2:8000`, verified in Gradle configuration, generated
  Debug `BuildConfig`, and the APK.
- Physical device: the settings UI instructs the developer to use a LAN-reachable URL and shows
  only the non-real placeholder `http://192.168.x.x:8000`; no concrete LAN address is hardcoded.
- Release: cleartext is disabled by manifest/network-security configuration and application code
  requires an `https://` base URL.
- Debug HTTP logging records headers only and explicitly redacts `Authorization`.

These behaviors match the public Android and development documentation: HTTP is limited to the
Debug local/trusted-network workflow, while Release requires HTTPS.

## APK and public-boundary inspection

A practical archive listing, printable-string scan, generated-configuration review, and APK
signature verification found no personal filesystem path, real private IP address,
credential/token-shaped value, private key marker, signing password, bundled keystore,
`local.properties`, `.env`, private Stage 9 name, or obsolete repository name.

The APK contains the intended emulator URL and the documented `192.168.x.x` instructional
placeholder. It also contains OkHttp's library-internal `http://localhost/` string; this is not
an application endpoint or configured default. No unexpected local configuration was bundled.
This was a bounded leakage inspection, not exhaustive reverse engineering.

## Generated files and pollution audit

Candidate-only generated state consisted of:

1. disposable reproducible output: project `.gradle/`, `app/build/`, reports, test results, and
   the Debug APK;
2. private/raw verification state: isolated Gradle caches, disposable `local.properties`, raw
   logs, extracted APK inspection files, and the disposable Debug keystore;
3. sanitized public evidence: this document only.

All 202 manifested candidate source files retained their original hashes. The disposable build,
cache, local configuration, signing state, raw evidence, and detached candidate were removed
after evidence capture.

The main worktree remained on `main` at the same HEAD with no staged files. Its pre-existing
dirty public-candidate work and ignored local Android/build/private Stage 9 material were
preserved. No APK, AAB, cache, report, or other generated Android artifact was copied into the
main public candidate; this sanitized evidence file is the task's only addition.

## Limitations

- No emulator/device instrumentation was run because it is not part of the repository's defined
  local unit-test workflow and there are no `androidTest` sources.
- No release artifact was assembled, signed, or published. Production signing and deployment
  readiness are deliberately outside this source reproducibility claim.
- The lint dependency-update notices and two Kotlin compiler warnings remain recorded; this
  stage did not alter source, lint policy, or versions to remove them.
- APK inspection was intentionally practical rather than exhaustive mobile reverse engineering.

## Gate recommendation

**Stage 6D verdict: PASS.** The isolated public candidate used the declared JDK/Gradle/AGP/
Kotlin/SDK baseline, resolved dependencies from a fresh cache, passed all defined Debug unit
tests and Debug lint, built a Debug APK without private signing state, enforced the documented
endpoint boundary, passed practical leakage inspection, and left the main worktree safe and
unstaged. Stage 6E has not begun.
