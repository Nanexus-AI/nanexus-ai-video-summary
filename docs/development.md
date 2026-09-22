# Development

This is the developer source of truth for Nanexus AI Video Summary. For system boundaries, read [Architecture](architecture.md); for deployment concepts, read [Deployment](deployment.md); for proposed changes, read [Contributing](../CONTRIBUTING.md).

## Prerequisites

- Python 3.12 (the package requires `>=3.12,<3.13`)
- [`uv`](https://docs.astral.sh/uv/) for the reproducible Python dependency workflow
- Docker with Compose for local PostgreSQL, Redis, and MQTT and for Compose-based integration work
- Node.js 22.14.0 and npm for the currently validated Web toolchain
- JDK 17, Android SDK 35, and platform-tools for Android development

The current versions are backend package `0.3.0`, Web `0.4.0`, and Android `0.1.0`. Gradle 8.9, Android Gradle Plugin 8.7.3, Kotlin 2.0.21, compile/target SDK 35, and minimum SDK 26 are declared in the Android project.

## Python environment and dependency authority

`pyproject.toml` defines the Python package, supported interpreter, bounded direct dependencies, optional `test`, `openclip`, and `openclip-cuda` groups, and tool configuration. `uv.lock` is the committed reproducible resolution and is the preferred development path:

```bash
uv sync --extra test
source .venv/bin/activate
```

Add OpenCLIP dependencies when that runtime path is needed or when running the complete static
check suite. Mypy intentionally checks the optional provider modules, so its reproducible
environment composes the existing `test` and `openclip` extras:

```bash
uv sync --frozen --extra test --extra openclip
```

Use `uv lock --check` to detect a stale lock without changing it. Dependency changes should be made in `pyproject.toml` and intentionally relocked; do not hand-edit `uv.lock`.

`requirements.txt` is retained as a legacy/alternate pip install list. It uses lower bounds, includes OpenCLIP packages, and does not reproduce the locked environment. It is not the dependency authority and should not be silently deleted or used to update the lock.

## Environment configuration

Copy the tracked template and keep the resulting file local:

```bash
cp .env.example .env
```

[`.env.example`](../.env.example) documents the available local settings. Important groups include:

- `DATABASE_URL`, `REDIS_URL`, and MQTT settings for local infrastructure;
- `EVENT_INTELLIGENCE_URL` and `EVENT_INTELLIGENCE_TOKEN` for runtime public v1 integration;
- `EVENT_INTELLIGENCE_SOURCE_DIR` only for Compose builds that use a local Event Intelligence checkout;
- `MODEL_PROVIDER` for the current v1 model-service/enrichment path (`stub` or `openclip`); `AI_MODE` is legacy AI-worker compatibility only and must not be used to infer v1 provider selection; `AI_DEVICE`, `OPENCLIP_MODEL`, and `OPENCLIP_PRETRAINED` for OpenCLIP runtime selection;
- Summary, Chat, and optional OpenAI-compatible LLM settings;
- `DEPLOYMENT_MODE`, `AUTH_MODE`, credential-file paths, public origins, and capability checking.

The values in the template are local/trusted-development defaults. Do not reuse its database password, anonymous MQTT behavior, development auth, blank tokens, or HTTP origins for an untrusted deployment.

## Stub and synthetic local development

The smallest local workflow uses loopback-only infrastructure and deterministic legacy-compatible processing. It needs no camera, cloud key, GPU, or model download.

Set `AI_MODE=stub` in `.env`, then start the infrastructure:

```bash
docker compose up -d
```

In separate activated-shell terminals, run:

```bash
python -m services.mqtt_listener.main
python -m services.ai_worker.main
uvicorn services.api.main:app --reload --host 127.0.0.1 --port 8000
```

Seed synthetic data and inspect it:

```bash
python scripts/seed_events.py
python scripts/build_summary.py
curl -s http://127.0.0.1:8000/timeline | python -m json.tool
curl -s http://127.0.0.1:8000/summary/today | python -m json.tool
```

`scripts/dev_up.sh` automates infrastructure and a legacy editable pip environment, but `uv sync` remains the reproducible dependency workflow. The Stub demo validates a retained local-compatible path, not the complete Event Intelligence topology.

## Backend development

The main entry points are under `services/`; reusable package code is under `src/nanexus/`; migrations are under `alembic/`; and helper utilities are under `scripts/`.

Start the API with reload after local dependencies are available:

```bash
uv run uvicorn services.api.main:app --reload --host 127.0.0.1 --port 8000
```

Run migrations against the configured Video Summary database when a workflow requires the current schema:

```bash
uv run alembic upgrade head
```

The current backend verification commands are:

```bash
uv lock --check
uv sync --frozen --extra test --extra openclip
uv run pytest
uv run ruff check .
uv run mypy
```

These commands correspond to the committed pytest, Ruff, and Mypy configuration in
`pyproject.toml`. The OpenCLIP extra is required here because Mypy checks the optional provider
implementation; installing it does not load or download model weights. On Linux, the committed
uv source routing resolves Torch and torchvision from the CPU index. CUDA packaging is a
separate `openclip-cuda` extra and GPU container profile rather than an implicit developer
dependency. There is no repository Makefile, tox, pre-commit, or public CI command to substitute
for these commands.

## Web development

Install exactly the committed npm lock and run Vite:

```bash
cd web
npm ci
npm run dev
```

The committed development script passes `--host 0.0.0.0`; Vite normally uses port `5173` and proxies `/api` to `http://localhost:8000`. Keep the development server on a trusted network, or invoke Vite with a narrower host binding. Set `VITE_API_PROXY_TARGET` to another trusted-development API endpoint if needed. Available checks and builds are:

```bash
npm test
npm run lint
npm run typecheck
npm run build
```

The release Compose Web container listens on host loopback port `8080`; that is separate from the Vite development server.

## Android development

The Android project is under `android/`. From that directory, common entry points are:

```bash
./gradlew testDebugUnitTest
./gradlew assembleDebug
```

Debug defaults to `http://10.0.2.2:8000`, the Android emulator alias for the development host. A physical device needs a host address reachable on the same trusted network, and the API must listen on a reachable interface. Release builds require HTTPS. See the [Android development guide](android.md) for SDK setup, configuration, build, signing, and device details; this document intentionally does not duplicate them.

## Event Intelligence integration development

Normal integration needs only a compatible service:

```dotenv
EVENT_INTELLIGENCE_URL=http://event-intelligence:8000
EVENT_INTELLIGENCE_TOKEN=<service-token>
```

At runtime, Video Summary uses Event Intelligence public v1 HTTP/contracts. It must not import Event Intelligence source, connect to its database, or depend on its internal Redis keys.

An optional local checkout is useful for source-built Compose integration and the synthetic slice. The default is the sibling `../nanexus-event-intelligence`; override the layout without changing tracked files:

```bash
EVENT_INTELLIGENCE_SOURCE_DIR=/path/to/nanexus-event-intelligence \
  docker compose -f compose.release.yaml --profile integrated config
```

`EVENT_INTELLIGENCE_SOURCE_DIR` is a Compose build/test input, not a runtime Python setting. `compose.slice.yaml` is a cross-project synthetic evidence harness and also needs fixtures from that checkout. Consult [Deployment](deployment.md) for topology roles and [Architecture](architecture.md#compatibility-and-capability-negotiation) for current contract expectations.

## Development ports

| Surface | Development address | Exposure |
|---|---|---|
| Video Summary API | `127.0.0.1:8000` in the recommended host command | Explicit API ingress |
| Vite Web server | `0.0.0.0:5173` by the committed npm script, or the address printed by Vite | Trusted-network development only |
| Release Compose Web | `127.0.0.1:8080` | Loopback ingress |
| Model service | container port `8010` | Internal; do not publish by default |
| PostgreSQL | `127.0.0.1:5432` | Local Compose only |
| Redis | `127.0.0.1:6379` | Local Compose only |
| MQTT | `127.0.0.1:1884` mapped to container `1883` | Local anonymous broker only |
| Event Intelligence slice | `127.0.0.1:18000` mapped to container `8000` | Synthetic integration evidence |
| Android emulator API | `http://10.0.2.2:8000` | Emulator-to-host alias |

Do not publish PostgreSQL, Redis, MQTT, workers, model services, or processor interfaces to an untrusted network.

## OpenCLIP development

The current default model is `ViT-B-32-quickgelu` with pretrained identifier `openai`. The first real load downloads weights and caches them outside Git; allow time, storage, and outbound access. Stub is preferred for deterministic and resource-light development.

CPU and GPU/CUDA OpenCLIP both have current validation evidence. `pyproject.toml` routes the
Linux `openclip` extra to the explicit PyTorch CPU wheel index, so
`uv sync --frozen --extra test --extra openclip` remains CPU-oriented. The validated GPU path is
container-first: `uv sync --extra openclip-cuda` is for
`docker/Dockerfile.model-worker-cuda` and `compose.gpu.yaml`, not for normal Linux development.
The GPU host requirement is an NVIDIA driver plus NVIDIA Container Toolkit; a host CUDA toolkit
is not required. `AI_DEVICE=cuda` fails closed when CUDA is unavailable. See
[Resource profiles](resource-profiles.md).

## Local files that must not be committed

Keep these out of Git:

- `.env` and other local environment variants;
- `.venv/`, Python caches, test/type/lint caches, `node_modules/`, Web build output, and Android/Gradle build output;
- databases, local data, logs, coverage output, snapshots, and downloaded media;
- tokens, identity JSON, service credential files, signing keys, keystores, and private keys;
- OpenCLIP/model caches and weight files (`*.ckpt`, `*.onnx`, `*.safetensors`, `*.pt`, `*.pth`);
- generated APK/AAB files, audit reports, SBOM output, license-scan output, and benchmark output;
- private Stage 9 closeout/gate artifacts listed in `.gitignore`.

Before sharing changes, use `git status --short` and verify no secret, local path, private network address, downloaded weight, or generated binary has become tracked.

Report potential vulnerabilities according to [SECURITY.md](../SECURITY.md), without placing sensitive details in a public issue or pull request.
