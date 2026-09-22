# Architecture

This document is the architectural source of truth for Nanexus AI Video Summary. It describes the current system and its supported boundaries; historical milestone documents are implementation evidence, not the current architecture.

## System purpose

Nanexus AI Video Summary turns normalized camera events into an application-facing timeline, daily summaries, semantic search, and cited chat results. It sits above camera, NVR, or VMS systems and Nanexus Event Intelligence:

```text
Camera / NVR / VMS
        |
        v
Nanexus Event Intelligence
  vendor-neutral event processing and public v1 HTTP/contracts
        |
        v
Nanexus AI Video Summary
  application data, retrieval, summaries, chat, and API
        |
        +--> Web
        +--> Android
        +--> Summary
        +--> Search
        +--> Chat
```

Frigate is an important current source-system integration and a retained compatibility path. It is not the permanent system boundary: other camera, NVR, or VMS sources belong behind Event Intelligence's vendor-neutral contracts.

## Layered architecture and ownership

| Layer | Owns | Does not own |
|---|---|---|
| Camera / NVR / VMS | Detection, recording, and source media | Video Summary application behavior |
| Nanexus Event Intelligence | Source-specific ingestion, normalized events and subjects, evidence access, enrichment jobs, and public v1 HTTP/contracts | Video Summary's application database, search index, summaries, chat, or client UI |
| Nanexus AI Video Summary | Event Intelligence consumers, enrichment results, application persistence, embedding/search jobs, daily summaries, chat jobs, application API, and stable subject links | Source-system normalization or Event Intelligence's database |
| Web and Android | Presentation, user interaction, capability-aware feature exposure, and navigation through Video Summary API links | Direct database, Redis, MQTT, model-service, Frigate, or Event Intelligence service access |

The normal dependency direction is one way: Video Summary calls Event Intelligence over public, versioned HTTP contracts. The projects do not share a runtime database or ORM, and Video Summary does not import Event Intelligence source. A sibling source checkout is only a convenient build and integration-test input.

## Runtime components

- The FastAPI application exposes health, operational, legacy compatibility, and `/api/v1` client endpoints. It coordinates requests but does not run OpenCLIP inference in the normal v1 request path. `GET /health` keeps `ai_mode` as legacy compatibility metadata for the retained AI-worker path; operators must not infer the current v1 provider from it. Current v1 provider selection is `model_provider` (`MODEL_PROVIDER`). Model and device runtime identity remain on the isolated model service `/health`.
- PostgreSQL with pgvector stores Video Summary's application records, summaries, conversations, and embeddings.
- Redis carries asynchronous embedding, summary, chat, and legacy processing work.
- The Event Intelligence worker polls public v1 processor jobs, obtains job-scoped subject/evidence data, calls the selected model provider, and writes versioned results back.
- The embedding worker creates persisted search embeddings through the isolated model service.
- Summary and chat workers precompute or asynchronously produce results. Rule-based summaries and extractive chat are local defaults; an OpenAI-compatible LLM is optional.
- The model service isolates Stub or OpenCLIP processing from the API process.
- The Web application and Android application consume the Video Summary client API.

## Event and enrichment data flow

The intended integrated flow is:

```text
source event and media
  -> Event Intelligence normalizes event/subject/evidence
  -> Event Intelligence advertises a processor job
  -> Video Summary enrichment worker claims the job
  -> worker reads job-scoped subject/evidence through public v1 HTTP
  -> Stub or OpenCLIP produces the supported enrichment result
  -> worker returns the versioned result to Event Intelligence
  -> Video Summary consumers persist application-facing records and queue derived work
```

Evidence authority remains with Event Intelligence. A processor token is a service identity, and evidence access is scoped to the job. Video Summary persists the application records needed for its own retrieval and user experience rather than joining directly against Event Intelligence storage.

The retained legacy path consumes Frigate MQTT events, stores legacy event records, and processes source snapshots with the legacy AI worker. It supports rollback and the synthetic local demo; it should not be used to redefine the production boundary.

## Summary, search, and chat

The v1 features use Event Intelligence subject UUIDs as stable references:

1. Event ingestion or enrichment yields application records associated with a subject UUID.
2. The embedding worker sends text or image work to the model service and persists the returned embedding and model identity.
3. Search embeds a query through the model service, performs pgvector retrieval, and returns subject-linked results. It can report degraded behavior when semantic processing is unavailable. A legacy keyword path remains available for compatibility.
4. The summary worker aggregates stored subject data for a local date, site, and optional camera. Rule mode is deterministic; optional LLM mode uses bounded context and cost settings. Clients read the stored result instead of invoking an LLM synchronously.
5. Chat creates an asynchronous job. The worker retrieves stored search/summary context, produces an extractive or optional LLM response, and returns subject citations. Chat does not expose chain-of-thought.
6. `/api/v1/subjects/{review_item_id}` redirects to the configured public Event Intelligence
   `/api/v1/review-items/{review_item_id}` route; clients do not construct private middleware
   URLs. Observation UUIDs and canonical ReviewItem UUIDs remain distinct: Event Intelligence
   exposes an observation at `/api/v1/events/{observation_id}` and its canonical review item at
   `/api/v1/review-items/{review_item_id}`.

## OpenCLIP and model processing

The deterministic `Stub` provider is the lightweight development and verification path. OpenCLIP supplies image/text embeddings and zero-shot labels through isolated model processing. Its current default is `ViT-B-32-quickgelu` with pretrained identifier `openai`.

OpenCLIP weights are downloaded on demand and cached locally; they are not in this repository or
its source-first release. CPU execution and the separate container-first GPU/CUDA profile
(`openclip-cuda`, `docker/Dockerfile.model-worker-cuda`, and `compose.gpu.yaml`) have current
hardware-validation evidence. The default Linux dependency workflow remains CPU-only and must
not be inferred to install CUDA.

Model-service failure should degrade model-dependent Video Summary features without changing Event Intelligence's ownership of normalized source data. Model inference remains outside the normal API process; `LEGACY_API_MODEL_INFERENCE_ENABLED` exists only for rollback compatibility.

## Compatibility and capability negotiation

Video Summary can query Event Intelligence's authenticated `/api/v1/processor/capabilities` endpoint during startup. When `CAPABILITY_CHECK_ENABLED=true`, missing or incompatible required API, canonical schema, capability, or processor-contract versions fail startup. Unknown fields are tolerated and optional absent features can be disabled safely.

Web and Android query `/api/v1/capabilities` on the Video Summary API and use its advertised Summary, Search, Chat, subject-reference, and legacy-fallback capabilities. The current boundary expects Video API v1, Capability 1.0, Canonical Schema 1.0, and Processor Contract 1.0. Compatibility checks reduce accidental version mismatch; they are not a substitute for release testing between independently versioned projects.

## Client relationship

Web and Android are peers over the same Video Summary v1 client contract. They never receive internal database, Redis, MQTT, model-service, Frigate, or processor credentials. They use Video Summary's subject links to enter public Event Intelligence review/evidence surfaces when appropriate.

The React Web client is served separately and proxies `/api` to the API during development. The Jetpack Compose Android client uses `http://10.0.2.2:8000` in Debug by default so an emulator can reach a host API; Release requires an HTTPS base URL. Android's Timeline view and legacy server routes remain compatibility surfaces while Summary, Search, and asynchronous Chat use v1. Build, endpoint, and device setup details are in the [Android development guide](android.md).

## Security and trust boundary

The default operational assumption is a trusted internal network. PostgreSQL, Redis, MQTT, workers, the model service, and middleware-facing services are internal and are not intended for direct untrusted-network exposure. Development authentication, local database credentials, and anonymous local MQTT are development conveniences only.

The supported public ingress concept is a controlled Web/API endpoint in front of internal services. A deployer exposing the application outside a trusted network must add suitable TLS, firewalling, identity, authorization, and access controls. This repository is not a complete public-network gateway. Production mode fails closed for development authentication, missing credential files, non-HTTPS public origins, and selected compatibility failures; see [Security](../SECURITY.md) and [Deployment](deployment.md).

## Deployment topology concepts

- **Local development:** host-run Python services use loopback-published PostgreSQL, Redis, and MQTT from `docker-compose.yml`; the Stub path permits synthetic development without a camera or model download.
- **Integrated source build:** `compose.release.yaml --profile integrated` builds an optional Event Intelligence checkout and gives it a separate database while retaining HTTP v1 as the runtime boundary.
- **External Event Intelligence:** `compose.release.yaml` plus `compose.external-event.yaml` connects containers to an independently deployed Event Intelligence endpoint. No local Event Intelligence source or database is required.
- **Synthetic integration evidence:** `compose.slice.yaml`, optionally combined with migration-era overlays, exercises cross-project contracts with synthetic inputs. It is not the default user deployment.

The release Compose publishes only Web (`127.0.0.1:8080`) and the application API (`127.0.0.1:8000`) to the host. Internal service ports stay on the Compose network. Details and exact commands are in [Deployment](deployment.md).

## Legacy and compatibility paths

The repository deliberately retains legacy Frigate MQTT ingestion, legacy event/search/chat routes, the legacy AI worker, and historical Compose overlays for rollback and migration evidence. These paths may remain useful for the local synthetic demo, but new integrations should use Event Intelligence and the public v1 contracts. Historical M0/M1/M2 and gate documents explain prior decisions; they do not override this document or current source configuration.

## Explicit non-goals

Nanexus AI Video Summary does not:

- replace a camera, NVR, or VMS or become the canonical owner of recordings;
- make Frigate the permanent architecture boundary;
- duplicate Event Intelligence's source normalization, evidence authority, or database;
- allow clients to call Event Intelligence processor interfaces or internal services directly;
- run heavy model inference synchronously in the normal API request path;
- bundle model weights, caches, camera media, project-published container images, or APK/AAB files in the initial source-first release;
- provide a complete TLS reverse proxy, VPN, identity provider, or public-network gateway;
- claim general production readiness merely from the completed single-host GPU/CUDA validation.
