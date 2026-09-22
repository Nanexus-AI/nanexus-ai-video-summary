# Stage 4C — Trusted-network security hardening

## Task scope

Stage 4C reviewed the development and release Compose definitions, the local Mosquitto configuration, development environment examples, and public deployment/security documentation. The work was limited to conservative host bindings and documentation of the trusted-network boundary. It did not redesign networking, add an external-access platform, change Event Intelligence sibling paths, or alter CPU/GPU dependency behavior.

## Security-boundary decision

The repository assumes local development or a trusted internal network by default. Databases, brokers, workers, model services, and middleware-facing interfaces are internal services and are not presented as safe for direct exposure to untrusted networks. Deployers requiring external access must terminate it through deployment-appropriate controls such as a VPN, TLS reverse proxy, authentication gateway, or zero-trust access layer. The repository does not claim to provide a complete public-network security gateway.

## Services reviewed

- Base development Compose: PostgreSQL, Redis, and Mosquitto.
- Slice/search Compose: Event Intelligence database, Redis, API, workers, model service, and Video Summary services.
- Release Compose: integrated databases, Redis, Event Intelligence, workers, model service, Video Summary API, and Web service.
- Mosquitto listener configuration and the host-side MQTT development path.

## Bindings/defaults changed

- PostgreSQL host publication changed from `5432:5432` to `127.0.0.1:5432:5432`.
- Redis host publication changed from `6379:6379` to `127.0.0.1:6379:6379`.
- Mosquitto host publication changed from `1884:1883` to `127.0.0.1:1884:1883`.
- Container ports, service names, Docker-network connectivity, health checks, and volumes were unchanged.
- Existing application ingress was not narrowed: the documented host-run API remains available on port 8000, Android emulator access via `10.0.2.2` remains viable, and existing slice/release loopback publications remain unchanged.

## Development credentials treatment

The `nanexus:nanexus` database value and anonymous Mosquitto access remain available for local development and are explicitly identified as development-only defaults. Documentation directs deployers to use deployment-specific credentials outside local/trusted development. These example values were not treated as leaked secrets.

## Documentation changes

- `README.md` now has a concise operational security-boundary statement.
- `.env.example` labels the database credentials and anonymous MQTT broker as local-development defaults and notes the broker's loopback publication.
- `docs/deployment-security-runbook.md` states the trusted-network assumption and external-access responsibility.
- `docker/mosquitto/mosquitto.conf` labels anonymous access as local-development-only and unsuitable for untrusted exposure.

## Verification performed

- `git status --short` was inspected before and after the work; the repository already contained unrelated modified and untracked files.
- `git diff --check` passed.
- Scoped diffs for all Stage 4C files were reviewed.
- Docker Compose v2 was unavailable, so the installed legacy-compatible `docker-compose` client was used.
- `docker-compose config` passed for the base development Compose file.
- `docker-compose -f compose.slice.yaml config` passed with a validation-only processor token.
- `docker-compose -f compose.slice.yaml -f compose.search.yaml config` passed with a validation-only processor token.
- `docker-compose -f compose.release.yaml config` passed with validation-only required variables and placeholder secret-file paths; no services were started.
- The effective base configuration reports `host_ip: 127.0.0.1` for PostgreSQL 5432, Redis 6379, and Mosquitto host port 1884.
- Effective slice/release configurations retain Docker-internal database, Redis, worker, Event Intelligence, and model-service connectivity. Their existing host publications remain loopback-bound.
- Mosquitto 2.1.2 loaded `docker/mosquitto/mosquitto.conf` successfully in a disposable container with networking disabled; it was stopped after five seconds.
- No broad integration test was run, as required by the stage boundary.

## Remaining deployment responsibilities

Deployers must provide suitable perimeter controls, TLS, authentication/authorization, firewall policy, secret management, and unique production credentials for their environment. Any intentional access beyond localhost or a trusted internal network requires an explicit, secured publication design. Anonymous MQTT must not be published to an untrusted network.

## Risks / unknowns

- Host-run API commands intentionally continue to bind `0.0.0.0` to support the documented Android emulator and trusted-device workflow; operators must not expose that development server to an untrusted network.
- Loopback-bound Compose infrastructure is unavailable directly to other physical hosts. This is intentional; cross-host deployments require explicit secure networking and configuration.
- Mosquitto listens on container IPv4 and IPv6 interfaces, but its only host publication in the development Compose file is IPv4 loopback. Docker-network peers can still reach it as intended.
- The worktree was already dirty. Existing changes, including Stage 9-related files and CPU/OpenCLIP work, were left untouched by Stage 4C. No claim is made here about their readiness.

## Gate recommendation

**PASS.** The development database, Redis, and anonymous MQTT broker are no longer unnecessarily published on all host interfaces; internal connectivity and documented local application access remain intact; and the trusted-network/external-access boundary is stated publicly. No files were staged, committed, or pushed.
