# Stage 6E Docker/Compose reproducibility verification

Date: 2026-09-20
Repository: Nanexus AI Video Summary
Scope: isolated Docker/Compose execution, corrective context verification, and bounded Stub runtime

## Executive summary

Stage 6E **passes**. The original build-context
blocker is fixed by a narrow repository `.dockerignore`. An adversarial `COPY .` audit proved
that `.git`, private environment files, local dependencies/caches, build output, databases,
logs, model artifacts, raw verification output, and private Stage 9 material no longer reach
BuildKit, while every required image-build input remains available. All documented public
Compose surfaces still render and all eight Stub release application images rebuilt from source
without cache.

The bounded runtime progressed substantially: local PostgreSQL, Redis, and MQTT started; release
database migration completed; the release database, Redis, model Stub, API, workers, and Web
container reached their expected running/healthy state once a capability-only Event Intelligence
stub satisfied the documented fail-closed startup dependency. API, database/Redis health,
capability output, and deterministic 512-dimensional Stub inference passed. Actual host bindings
matched the documented loopback/internal-service boundary.

The initial Web smoke exposed a missing nginx static root: the built files existed, but the SPA
fallback resolved against the wrong directory and returned HTTP 500 with an internal redirect
cycle. A separately reviewed one-line server-level `root /usr/share/nginx/html;` correction fixed
that defect without changing routing, headers, bindings, Compose, or runtime code. Nginx syntax,
Web/static/proxy behavior, and a complete scoped stop/start cycle then passed.

## Clean candidate and environment

- Main HEAD remained `da3b7c6eb32160d927ff5101194698478da8b2de`; the index was empty.
- A new detached Stage 6A candidate was constructed from that HEAD, the binary-safe tracked
  patch, and the explicit public untracked set.
- The corrective candidate contained 205 source files before adversarial audit fixtures.
- Its sorted content-manifest digest for the nginx corrective rerun was
  `69388f4c0a942f6738f0199a546a592e1367d502aaf5210d5f00312dec20bdda`.
- Docker client/Engine: 29.1.3, API 1.52.
- Compose: standalone `docker-compose` v2.32.4; the plugin command form was unavailable.
- All verification projects used isolated `nanexus6e-*` names and project-owned volumes.

The candidate started without `.env`, private Stage 9 files, dependency trees, build output,
databases, logs, model caches/weights, or prebuilt application images. Existing unrelated Docker
resources were inventoried and left untouched.

## Compose topology inventory

| Compose file(s) | Purpose | Event Intelligence checkout | Weights/GPU | Host publication |
|---|---|---|---|---|
| `docker-compose.yml` | host-run local infrastructure | No | No | PostgreSQL `127.0.0.1:5432`, Redis `:6379`, MQTT `:1884` |
| `compose.release.yaml` | source-built release, Stub defaults | No for external mode | No in Stub | API `127.0.0.1:8000`, Web `:8080` |
| release + `compose.external-event.yaml` | independently deployed Event Intelligence | No | No in Stub | release ports only |
| release `--profile integrated` | integrated source build | Yes | No in Stub | release ports only; Event services internal |
| `compose.slice.yaml` | synthetic cross-project evidence harness | Yes | No | Event API `127.0.0.1:18000` |
| slice + `compose.search.yaml` | migration-era search/summary/chat overlay | Yes | Stub selectable | slice port only |
| slice + search + `compose.model.yaml` | migration-era OpenCLIP override | Yes | weights on use; CPU default | slice port only |
| release resource variables | Stub, CPU OpenCLIP, prospective CUDA | integrated only | profile-dependent | release ports only |

The ignored private `compose.cpu-openclip-gate.yaml` is not a public topology.

## Configuration rendering

Standalone Compose 2.32.4 successfully rendered all of the following after the correction:

- base local infrastructure;
- slice, slice plus search, and slice plus search/model;
- release Stub and release plus external-Event overlay;
- release integrated with default sibling layout;
- slice and integrated release with sanitized `/tmp/stage6e-event-intelligence` override; and
- CPU OpenCLIP and prospective CUDA selections as configuration-only checks.

Service references, interpolation, volumes, secrets, and build contexts were valid. The obsolete
repository path did not appear. Rendered ports retained the documented loopback policy, and
internal release databases, Redis, model service, workers, and integrated Event services had no
host publication. Compose interpolates the integrated-profile `EVENT_DB_PASSWORD` even when the
profile is inactive, so validation supplied a sanitized value.

## `.dockerignore` corrective decision

The original run proved that the absence of `.dockerignore` transmitted the detached worktree's
`.git` pointer and its personal absolute path. The corrective file excludes these precise
categories:

- Git metadata/local ignore configuration;
- private `.env` variants while explicitly retaining `.env.example`;
- Python environments, bytecode, test/type/lint caches, and coverage output;
- Node dependencies and Web build output;
- Android/Gradle state, build directories, APKs, and AABs;
- local DB sidecars, logs, and runtime state;
- model caches and common checkpoint/weight formats;
- local artifact, test-result, raw-evidence, and verification-output directories;
- the two known private Stage 9 surfaces; and
- common editor, OS, swap, and temporary files.

Rules are repository-relative and category-specific. Required source, package locks/manifests,
migrations, Docker configuration, scripts, public fixtures/assets, and documentation were not
broadly excluded.

## Required build inputs preserved

Inspection of every public Dockerfile and Compose build context established the required set:

- model worker: `pyproject.toml`, `uv.lock`, `README.md`, `src/`, `services/`;
- search/API/workers: those inputs plus `alembic.ini` and `alembic/`;
- slice worker: `src/` and `services/`;
- Web: `web/package.json`, `web/package-lock.json`, complete `web/` source/config/static input,
  and `docker/nginx.conf`; and
- external Event Intelligence contexts: owned by that separate checkout and unaffected by this
  repository's root `.dockerignore`.

The deterministic audit image confirmed representative required files including `.env.example`,
all Python packaging/migration inputs, API/model source, Web manifests/source, nginx config, and
synthetic smoke fixtures remained present.

## Build-context privacy verification

A fresh candidate was deliberately populated with sentinel files at `.env`, `.venv`, Web
`node_modules`/`dist`, Android `.gradle`/build, log and SQLite paths, model cache/weight paths, the
private Stage 9 overlay, and raw verification output. Its real detached `.git` pointer was also
present.

A temporary audit Dockerfile performed `COPY . /audit`. BuildKit loaded the 1.14 kB
`.dockerignore` and transferred 815.49 kB, down from the original unfiltered 1.13 MB. Inspection
inside the resulting image proved every sentinel, `.git`, and `.gitignore` absent. Recursive
content scans found neither the sentinel text nor the personal absolute workspace path. Required
inputs listed above were present. This verifies actual context behavior rather than only pattern
interpretation.

The adversarial fixtures were removed after the audit and were never part of the source manifest.

## Regression source-image build

The isolated release project performed a `--pull --no-cache` Stub rebuild. All eight tags built:

- model service;
- migration;
- embedding, enrichment, summary, and chat workers;
- Video Summary API; and
- Web.

BuildKit read the corrected ignore file for each local context. Python images installed the
locked base environment from the public Astral uv/Python base; Web ran `npm ci`, TypeScript, and
Vite from the public Node base and copied output into nginx. Registry metadata and package
downloads required network access. No OpenCLIP extra, model weight, or GPU dependency was used.
No image was exported, pushed, or published.

The Web install reported the lock's existing npm audit summary of two moderate and one high
vulnerability. Versions were not changed in this corrective reproducibility task.

## Stub/local startup and health

`nanexus6e-base` started successfully: PostgreSQL and Redis became healthy and Mosquitto ran.

`nanexus6e-stub` completed Video Summary migration with exit 0. Its Video DB, Redis, and model
service became healthy; embedding, enrichment, summary, and chat workers ran. Release mode
correctly failed closed until its required Event Intelligence capability endpoint was available.
To avoid full cross-repository integration, a temporary capability/read-only HTTP stub was
attached only to the isolated network. It advertised compatible v1 contracts, health, no pending
processor job, and an empty event page. After the normal startup retry, API and Web containers
reached Compose's healthy state.

This temporary service was a topology-startup dependency only. It did not exercise Event
Intelligence persistence, workers, fixtures, or end-to-end contracts and is not Stage 6F evidence.

## Actual port/security verification

Docker inspection proved these host bindings:

| Service | Actual binding |
|---|---|
| local PostgreSQL | `127.0.0.1:5432` |
| local Redis | `127.0.0.1:6379` |
| local MQTT | `127.0.0.1:1884` to container `1883` |
| release API | `127.0.0.1:8000` |
| release Web | `127.0.0.1:8080` |

Release Video DB, Redis, model service, workers, migration, and the temporary capability service
had empty host port bindings. No internal service was exposed externally.

## Bounded container smoke

Passed:

- API `GET /health/live`: HTTP 200, `alive`;
- API `GET /health`: HTTP 200, database and Redis true, overall `ok`;
- API `GET /api/v1/capabilities`: HTTP 200 with public versioned capabilities;
- internal model Stub `POST /v1/embeddings/text`: deterministic response with provider
  `nanexus`, declared 512 dimensions, and a 512-element vector; and
- nginx-to-API container networking: direct internal `GET /health/live` returned HTTP 200;
- Web `GET /`: HTTP 200 with the generated 168-byte `index.html`;
- the generated 192,104-byte JavaScript and 543-byte CSS assets: HTTP 200 with the expected
  JavaScript and CSS content types;
- representative SPA route `/stage6e/client/route`: HTTP 200 with content byte-identical to
  `index.html`;
- Web-proxied `GET /health`: HTTP 200 with database and Redis true; and
- Web-proxied `GET /api/v1/capabilities`: HTTP 200 with the unchanged public capability contract.

The original Web container contained `index.html` and hashed JS/CSS assets under
`/usr/share/nginx/html`, but nginx logged `rewrite or internal redirection cycle` because the
replacement server configuration did not establish that directory as its root. The correction
added only `root /usr/share/nginx/html;` at server scope. `nginx -t` passed before runtime testing.
The affected Web image was rebuilt with `--pull --no-cache`; BuildKit used the approved
`.dockerignore`, ran `npm ci` and the Vite build, copied the generated assets, and installed the
corrected configuration. No redirect-loop or nginx error remained after initial or restart smoke.

The API health response reported legacy `ai_mode` as `openclip`, while the separately isolated
model service demonstrably ran the configured Stub provider. No OpenCLIP package or weights were
built or loaded.

## Restart/shutdown and cleanup

The matching release project completed a full `stop` followed by `up -d --no-build --wait`.
Post-restart migration again exited 0; database, Redis, model Stub, API, Web, and all workers
returned to their expected healthy/running states. Web `/`, a representative SPA route, Web
`/health`, and direct API liveness passed again. The second Web log contained no redirect cycle
or nginx error. Final scoped shutdown then completed cleanly:

- the capability stub was removed;
- both Compose projects were brought down with their matching project/file arguments;
- Stage 6E containers, networks, and named volumes were removed;
- all eight locally built `nanexus6e-stub-*` tags and the temporary audit image were removed; and
- post-cleanup filters found no remaining `nanexus6e-*` Docker resource.

No unrelated container, image, volume, or network was modified.

## CPU/GPU and artifact boundary

CPU OpenCLIP and prospective CUDA settings were rendered only. No OpenCLIP image, cache, weight,
CPU inference, CUDA dependency, GPU device, or GPU inference was used. Stage 6F retains that
scope.

Local image-build success is not approval for binary redistribution. Future distributed images
still require the previously recorded SBOM, license, provenance, and NOTICE review for bases and
installed packages.

## Pollution audit

- The candidate source manifest was checked independently of adversarial disposable fixtures.
- No runtime database, log, cache, dependency tree, model artifact, or raw result entered public
  source.
- Temporary validation secrets, capability server, audit Dockerfile, candidate worktree, and all
  Stage 6E Docker resources were removed after evidence capture.
- The main worktree remained on the same HEAD with an empty index. Existing dirty public-candidate
  work and ignored private Stage 9 material were preserved.
- Intended Stage 6E changes are `.dockerignore`, the one-line `docker/nginx.conf` root correction,
  and this updated evidence only.

## Gate recommendation

**Stage 6E verdict: PASS.** Build-context privacy, every documented Compose render, source image
builds, local and release service health, deterministic Stub behavior, actual loopback/internal
port policy, Web HTML/static/SPA serving, API proxy regression, scoped stop/start recovery, and
pollution cleanup all passed from an isolated clean candidate. The local images were not
published, CPU/GPU inference remains outside this stage, and Stage 6F has not begun.
