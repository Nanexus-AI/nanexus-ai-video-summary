# Stage 9 acceptance

RELEASE-001–006 are implemented without Shadow Validation, retirement, publication, or deployment. Executed command results in the final handoff—not this document—determine pass/fail.

The boundary pins Python 3.12/frozen uv locks, Node 22.14/npm 10.9, Gradle 8.9, JDK 17 and Kotlin 2.0.21. Heavy model/cloud dependencies are optional. Complete integrated/external Compose uses source-built migrations. Production identity binds owner/site/role; development owner remains explicitly non-production. Compatibility fails early; optional features degrade; legacy APIs/DTOs/data/Compose remain.

Security headers/CORS, secret validation, Android Keystore/Release HTTPS, and bounded observability are present. No Video component reads Event Intelligence DB/ORM or bypasses it for Frigate/Evidence. No schema change was needed in Stage 9.

## Closeout decision

Stage 9 is not yet a full exit. The next task is a bounded closeout gate covering: upgrade from an explicit previous-version database snapshot; real CPU OpenCLIP load and end-to-end inference; durable Worker kill/restart behavior; clean no-cloud-key Stub Demo; formal Secret Scan, license audit and SBOM; independent clean builds; and disposition of the nine existing Video Summary Mypy errors.

That closeout task must not start Shadow Validation, disable the legacy MQTT listener, retire APIs/DTOs/data, publish artifacts, or create external repositories. After closeout passes, work proceeds in separate gates: Shadow Validation → Cutover Rehearsal → Legacy Retirement/Data Disposition → Open-source Release Gate.
