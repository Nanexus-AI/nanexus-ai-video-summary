# Stage 9 compatibility matrix

| Mode | Video API | Capability | Canonical schema | Processor contract | Event Intelligence |
|---|---|---|---|---|---|
| Integrated | v1 | 1.0 | 1.0 | 1.0 | >=0.1.0 at `581a852` contract |
| Existing foundation | v1 | 1.0 | 1.0 | 1.0 | Any release advertising all required versions |
| Legacy rollback | legacy | not required | legacy | not required | existing legacy configuration |

With `CAPABILITY_CHECK_ENABLED=true`, Video Summary checks authenticated `/api/v1/processor/capabilities` before startup. Missing/incompatible required versions fail startup; unknown fields are accepted. Optional missing features are disabled safely. Web/Android require Video API v1, capability 1, canonical schema 1 and processor contract 1. Legacy routes/DTOs remain for rollback.

Dependency direction is only Video Summary → Event Intelligence over public v1 HTTP. Databases and ORM are not shared; Video Summary does not access Frigate/Evidence directly.
