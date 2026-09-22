# Deployment

This document describes supported deployment concepts for Nanexus AI Video Summary. It is not a claim of turnkey production readiness. Read [Architecture](architecture.md) for service ownership and [Security](../SECURITY.md) for the supported security and reporting scope.

## Assumptions and trust boundary

The default deployment assumption is a trusted internal network. PostgreSQL, Redis, MQTT, workers, the model service, and Event Intelligence processor-facing services are internal. They are not intended for direct exposure to an untrusted network.

Web and the Video Summary API are ingress surfaces. External access is the deployer's responsibility and requires controls appropriate to the environment, such as TLS termination, a VPN, an authentication gateway, firewalling, or a zero-trust access layer. This repository does not install or configure a complete public-network gateway.

Development mode, local credentials, blank tokens, and anonymous MQTT are only for local or trusted-development use. Production mode must use deployment-specific secrets and HTTPS public origins and is designed to fail closed when required credential files are absent or development authentication is selected.

## Source-first release model

The initial release is built and operated from source. It does not include project-published prebuilt Docker images, APK/AAB downloads, OpenCLIP weights, model caches, camera media, or private environment files. Build outputs and runtime state stay local to the deployer.

A clean checkout should reproduce Python dependencies from `pyproject.toml` and `uv.lock`, Web dependencies from `web/package-lock.json`, Android tooling from the Gradle wrapper plus the declared SDK/JDK requirements, and container services from the tracked Dockerfiles and Compose files. External base images, packages, and on-demand model weights still require registry or network availability.

## Compose surfaces

| File | Intended role |
|---|---|
| `docker-compose.yml` | Local development infrastructure only: PostgreSQL, Redis, and anonymous Mosquitto, all published on loopback |
| `compose.release.yaml` | Current source-built Video Summary deployment; with the `integrated` profile it also builds a separate Event Intelligence checkout |
| `compose.external-event.yaml` | Overlay for containers reaching an independently deployed Event Intelligence service through the host gateway |
| `compose.slice.yaml` | Synthetic cross-project integration/evidence harness, including a synthetic Frigate endpoint and Event Intelligence fixtures |
| `compose.search.yaml` | Migration-era search/summary/chat application overlay used with the slice, not the default release topology |
| `compose.model.yaml` | Migration-era OpenCLIP worker override, not the default release topology |
| `compose.gpu.yaml` | GPU OpenCLIP overlay for the model service; combine with release or search Compose. Requests one NVIDIA GPU and does not publish extra host ports |

Do not assume all Compose files can or should be started together. The release topology and local infrastructure serve different workflows. The GPU overlay is additive and must not be used as a replacement for the CPU OpenCLIP profile.

## Base local development topology

For host-run development, copy `.env.example`, select Stub where desired, and start only infrastructure:

```bash
cp .env.example .env
docker compose up -d
```

This publishes PostgreSQL `127.0.0.1:5432`, Redis `127.0.0.1:6379`, and MQTT `127.0.0.1:1884` (container port `1883`). Application processes run on the host; the recommended API address is `127.0.0.1:8000`. This topology uses development credentials and is not an external deployment.

Stop it without deleting data:

```bash
docker compose stop
```

## Integrated Event Intelligence source topology

`compose.release.yaml` with the `integrated` profile builds Event Intelligence from an optional local checkout, gives Event Intelligence and Video Summary separate databases, and connects them through Event Intelligence's public v1 HTTP interface:

```bash
docker compose --env-file <deployment-env> \
  -f compose.release.yaml --profile integrated up --build -d
```

The default checkout is `../nanexus-event-intelligence`. For another layout, set:

```dotenv
EVENT_INTELLIGENCE_SOURCE_DIR=/path/to/nanexus-event-intelligence
```

This variable changes Compose build contexts and, in the synthetic slice, a fixture mount. It does not authorize a runtime source import or shared database. Internal `EVENT_INTELLIGENCE_URL` defaults to `http://event-intelligence:8000`.

## External Event Intelligence service topology

When Event Intelligence is independently deployed, no source checkout or Event Intelligence database is needed by this repository. Point the runtime at its compatible public v1 service and use the external overlay where the target is reachable through the Docker host:

```bash
docker compose --env-file <deployment-env> \
  -f compose.release.yaml -f compose.external-event.yaml up --build -d
```

Set `EVENT_INTELLIGENCE_URL` to the URL reachable **from the Video Summary containers**, not a browser-only URL. The overlay provides `host.docker.internal` mapping on Linux; an example host service would therefore use a URL such as `http://host.docker.internal:<port>`. `EVENT_INTELLIGENCE_PUBLIC_URL` is a separate browser/mobile-safe public origin used for controlled subject links. Use an Event Intelligence release advertising the versions required by [Architecture](architecture.md#compatibility-and-capability-negotiation).

`EVENT_INTELLIGENCE_SOURCE_DIR` has no role in this external-service topology.

## Required configuration and secrets

Use a deployment-specific environment file kept outside version control. `compose.release.yaml` requires at least:

- unique `VIDEO_DB_PASSWORD` and, for the integrated profile, `EVENT_DB_PASSWORD`;
- `PROCESSOR_API_TOKEN` for service-to-service processor access;
- `AUTH_TOKENS_FILE` and `SERVICE_TOKEN_FILE`, each pointing to a local file mounted as a Compose secret;
- HTTPS `PUBLIC_BASE_URL` and `EVENT_INTELLIGENCE_PUBLIC_URL` for production mode;
- the correct container-reachable `EVENT_INTELLIGENCE_URL` for an external service;
- explicit model, Summary, Chat, and optional LLM choices appropriate to the deployment.

Do not place secret contents in tracked Compose or environment-template files. Use distinct user and service identities, restrict file permissions, rotate credentials operationally, and avoid logging authorization headers, tokens, evidence, prompts, full queries, or internal URLs. `.env.example` is a name/default reference, not a production secret template.

## Internal ports and ingress

The release Compose publishes only:

- Video Summary API: `127.0.0.1:8000` -> container `8000`;
- Web: `127.0.0.1:8080` -> container `8080`.

PostgreSQL (`5432`), Redis (`6379`), the model service (`8010`), workers, and integrated Event Intelligence stay on the internal Compose network. The integrated Event Intelligence service is not host-published by `compose.release.yaml`. Preserve these boundaries unless an operator has a specific protected administration requirement.

Because Web and API bind to host loopback, a reverse proxy or other controlled ingress on the same host can reach them without publishing internal dependencies. This repository intentionally does not prescribe a complete reverse-proxy, certificate, VPN, or identity-provider implementation.

## Model weights, cache, and resources

Stub needs no external model or cache. OpenCLIP defaults to `ViT-B-32-quickgelu` with pretrained identifier `openai`; weights are downloaded on first use and stored in the `model-cache` volume in the release topology. They are not baked into source or an initial release artifact. Plan outbound access for initial acquisition, persistent disk, cache provenance, and startup time.

CPU OpenCLIP has current validation evidence. The default Linux Python resolution remains CPU-oriented through the `openclip` extra and the existing model-worker image. GPU/CUDA is a separate container-first profile:

- image: `docker/Dockerfile.model-worker-cuda`;
- extra: `openclip-cuda`, which resolves Linux torch/torchvision from the PyTorch `cu130` index;
- Compose overlay: `compose.gpu.yaml`, which keeps the internal `model-service` name, sets `AI_DEVICE=cuda`, and reserves one NVIDIA GPU;
- host requirement: NVIDIA driver and NVIDIA Container Toolkit. A host CUDA toolkit and host CUDA PyTorch install are not required;
- weights: still downloaded at runtime into the existing model-cache volume.

Activate GPU only by adding the overlay to the intended topology, for example:

```bash
docker compose --env-file <deployment-env> \
  -f compose.release.yaml -f compose.gpu.yaml up --build -d
```

`AI_DEVICE=cuda` on the CPU image is not a CUDA solution. Explicit GPU mode fails closed if CUDA
is unavailable; it does not silently fall back to CPU. The separate CUDA image and Compose
reservation passed Stage 6F-3 hardware validation on the recorded validation host; operators
must still verify their own driver, toolkit, GPU, and capacity combination.

Resource needs vary substantially. Stub planning starts around 2 CPU/2 GiB RAM, while the documented CPU OpenCLIP profile starts around 4 CPU/8 GiB RAM and additional cache storage. These are planning profiles, not universal capacity guarantees; see [Resource profiles](resource-profiles.md).

## Web, API, and Android access

The Web container uses the API as the product ingress. Configure controlled CORS origins and public URLs consistently with the actual HTTPS endpoint. Keep internal service names and credentials out of browser responses.

Android Debug defaults to `http://10.0.2.2:8000`, which works only for an emulator reaching an API on its host. A physical device needs a DNS name or host address reachable on the same trusted network; a host API bound only to `127.0.0.1` is not reachable from that device. If deliberately using the host-run API for a physical device, bind it to a suitable interface and enforce host firewall/trusted-network controls. Android Release rejects cleartext HTTP and must use the externally controlled HTTPS API URL.

See the [Android development guide](android.md) for build configuration, endpoint behavior, and signing boundaries.

## Startup and shutdown

Before startup, validate the rendered configuration using the exact same files, profile, and environment file intended for deployment:

```bash
docker compose --env-file <deployment-env> \
  -f compose.release.yaml --profile integrated config --quiet
```

On startup, the database health checks gate one-shot Alembic migration services; application services depend on successful Video Summary migration, and integrated Event Intelligence services use their own migration/database. Capability checking is enabled in the release environment and can refuse an incompatible Event Intelligence service. Model-dependent workers wait on the model service where declared.

Inspect `docker compose ps`, health/readiness endpoints, and logs after startup. Use the matching Compose arguments to stop the topology:

```bash
docker compose --env-file <deployment-env> \
  -f compose.release.yaml --profile integrated stop
```

Do not use `down -v` on data you intend to retain. Back up application databases and required configuration before upgrades. The repository supplies schema migrations but not a complete backup, restore, high-availability, or disaster-recovery system.

## Reproducibility expectations

Before treating a checkout as deployable:

1. Keep the checkout clean except for an untracked deployment environment and secrets outside Git.
2. Verify the required Event Intelligence contract version and the container-reachable URL.
3. Render Compose configuration with all required variables and existing secret-file paths.
4. Build from tracked Dockerfiles and pinned lockfiles; record relevant source revisions and resulting image identifiers locally.
5. Acquire and record model/cache provenance separately when OpenCLIP is selected.
6. Start, wait for migrations and health checks, then validate API readiness and client capability negotiation.

Independently versioned external images and model artifacts mean reproducibility also depends on upstream availability and any image-digest/provenance policy adopted by the deployer.

## Unsupported or not yet verified

The project does not currently promise:

- turnkey public-internet or generalized production readiness;
- a bundled TLS proxy, VPN, identity provider, firewall, backup system, or high-availability design;
- project-published prebuilt Docker images or Android APK/AAB artifacts for the initial release;
- bundled or redistributable OpenCLIP weights/caches;
- universal GPU compatibility beyond the recorded Stage 6F-3 hardware/software combination;
- full release validation for every external Event Intelligence deployment and network layout;
- Kubernetes, Home Assistant add-on, iOS, or other orchestration/client packaging;
- retirement of legacy Frigate/MQTT and legacy API compatibility paths.
