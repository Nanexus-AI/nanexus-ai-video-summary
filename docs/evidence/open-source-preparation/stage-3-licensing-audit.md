# Stage 3 — Licensing audit

## Decisions and findings

- The project license decision is Apache-2.0.
- Nanexus Event Intelligence is also Apache-2.0.
- The reviewed dependency graph is predominantly permissive.
- OpenCLIP source licensing and pretrained-weight licensing are separate concerns.
- Pretrained weights are not bundled and should remain runtime or user downloads by default.
- The initial release boundary is source-first: it excludes prebuilt Docker images, APK/AAB files, model caches, and pretrained weights.
- `psycopg-binary` requires LGPL redistribution consideration if binaries or images are distributed later.
- Android and container artifacts require artifact-specific SBOM and notices review before publication.
- The Event Intelligence contract mirror required an explicit provenance statement; Stage 4A subsequently addressed it.

These findings record the initial licensing boundary. They do not declare unresolved third-party redistribution questions legally closed.

## Gate decision

**PASS** — the project and initial release licensing boundary was recorded, with later artifact-specific obligations retained as open responsibilities.
