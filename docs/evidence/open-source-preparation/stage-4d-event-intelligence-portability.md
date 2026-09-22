# Stage 4D: Event Intelligence portability evidence

## Task scope

Remove obsolete public-candidate assumptions about the local Event Intelligence repository name and make optional source-based integration portable without changing the HTTP/contracts boundary, runtime behavior, model routing, or either project's API schemas.

## Stale references found

| Location | Classification | Treatment |
| --- | --- | --- |
| `compose.release.yaml` Event Intelligence build contexts | Development-only integrated deployment | Replaced the obsolete fixed sibling name with a configurable source root. |
| `compose.slice.yaml` Event Intelligence build contexts | Test/evidence integration harness | Replaced the obsolete fixed sibling name with the same configurable source root. |
| `compose.slice.yaml` vehicle-lifecycle fixture mount | Test/evidence harness; external local fixture | Made the mount derive from the configurable source root and documented that it is not a normal runtime dependency. |
| Two migration/reference document headers | Stale migration residue/documentation | Corrected the repository identifier to `nanexus-event-intelligence`. |
| Private, untracked CPU OpenCLIP gate configuration | Private/local-only evidence material | Intentionally not modified or promoted. It retains private local assumptions outside the tracked public candidate. |
| Private, untracked Stage 9 prompt material mentioning the old name | Private/local-only material | Intentionally not modified solely for publication. |

No tracked runtime Python source imports Event Intelligence or depends on its repository layout. `compose.search.yaml`, `compose.external-event.yaml`, `compose.model.yaml`, and `docker-compose.yml` contain no Event Intelligence source build context requiring a portability change.

## Portability mechanism chosen

Optional local builds now use `EVENT_INTELLIGENCE_SOURCE_DIR`, defaulting to `../nanexus-event-intelligence`. The default supports the convenient correctly named sibling checkout, while an override supports any checkout location. Normal application integration remains through `EVENT_INTELLIGENCE_URL` and the public v1 HTTP/contracts boundary. No package dependency, vendored source, shared database access, or API redesign was introduced.

## Compose/configuration files changed

- `compose.release.yaml`: all three integrated-profile Event Intelligence build contexts derive from `EVENT_INTELLIGENCE_SOURCE_DIR`.
- `compose.slice.yaml`: all four Event Intelligence build contexts and the external vehicle-lifecycle fixture mount derive from `EVENT_INTELLIGENCE_SOURCE_DIR`.
- `.env.example`: documents the optional local source root and its sibling-checkout default.

Service names, networks, environment variables, commands, dependency conditions, HTTP endpoints, and production/development behavior were otherwise preserved.

## Documentation changed

- `README.md` now states that Nanexus Event Intelligence is a separate Apache-2.0 project, that normal integration uses its public versioned HTTP API/contracts, and that source-based integration is optional and path-configurable.
- The README identifies the slice fixture as integration-test-only rather than a runtime dependency.
- The two migration/reference headers now use the actual `nanexus-event-intelligence` repository name.

The Stage 4A provenance statement remains accurate: the consumer contract mirror remains locally maintained, no generated contract models were regenerated, and no Event Intelligence source was copied.

## External/local fixture treatment

The vehicle-lifecycle fixture is required only by the tracked synthetic slice/evidence workflow. It remains owned by the separate Event Intelligence checkout and is mounted read-only through the configured source root. It was not copied, vendored, or presented as a normal runtime requirement. The private CPU gate and its additional asset mounts remain private and unchanged.

## Verification performed

- `git status --short` inspected before and after the work; the repository already contained Stage 4A-4C and private Stage 9 changes, which were preserved.
- `git diff --check` passed.
- A tracked-file search found no remaining `nanexus_frigate_extension` reference.
- A Compose-file sibling-path search found only the configurable, correctly named default in tracked files; obsolete paths remain only in the intentionally untouched private untracked CPU gate.
- Standalone Docker Compose v2.32.4 successfully rendered `compose.slice.yaml` with both the default source path and an arbitrary override.
- Standalone Docker Compose v2.32.4 successfully rendered the integrated profile of `compose.release.yaml` with both the default source path and an arbitrary override.
- Rendered configurations preserved `EVENT_INTELLIGENCE_URL=http://event-intelligence:8000`; overridden build contexts and the slice fixture mount resolved consistently beneath the override.
- The separate Event Intelligence repository was inspected read-only and not modified by this task.
- No runtime Python, contract schema, model configuration, CPU/GPU routing, or security-boundary file was changed for Stage 4D, so the full Python test suite was not run.
- No files were staged, committed, or pushed. No cross-repository fixture or binary was copied.

## Remaining coupling

The integrated release profile and synthetic slice intentionally require an Event Intelligence source checkout because they build its services locally. The slice additionally requires a fixture supplied by that checkout. External-service deployments remain decoupled from source layout and communicate through the public API.

## Risks / unknowns

- The local source checkout must remain compatible with the expected `backend` and fixture subdirectories; version compatibility is governed separately and was not redesigned in Stage 4D.
- The private CPU OpenCLIP evidence configuration still contains the obsolete local name. It is outside the tracked public candidate and needs deliberate private-tooling treatment rather than publication-driven editing.
- Compose configuration rendering verifies interpolation and structure, not image builds or runtime compatibility. Those were outside this portability-only stage.

## Gate recommendation

**PASS.** Tracked public-candidate configuration no longer silently requires the obsolete repository name, optional source integration has an explicit portable override, and the public HTTP/contracts architecture remains unchanged.
