# Stage 9 acceptance

RELEASE-001–006 are implemented without Shadow Validation, retirement, publication, or deployment. Executed command results in the final handoff—not this document—determine pass/fail.

The boundary pins Python 3.12/frozen uv locks, Node 22.14/npm 10.9, Gradle 8.9, JDK 17 and Kotlin 2.0.21. Heavy model/cloud dependencies are optional. Complete integrated/external Compose uses source-built migrations. Production identity binds owner/site/role; development owner remains explicitly non-production. Compatibility fails early; optional features degrade; legacy APIs/DTOs/data/Compose remain.

Security headers/CORS, secret validation, Android Keystore/Release HTTPS, and bounded observability are present. No Video component reads Event Intelligence DB/ORM or bypasses it for Frigate/Evidence. No schema change was needed in Stage 9.
