# Stage 9 deployment and security runbook

Trusted-LAN development explicitly uses `DEPLOYMENT_MODE=development`/`AUTH_MODE=development`; its owner header is isolation-only and must not be public. Production requires TLS reverse proxy, firewall, production mode, static reference identities or a compatible gateway adapter, and distinct service credentials. It fails closed for absent credential files, development auth, non-HTTPS public origins, migration failure, or incompatible capability.

Create untracked identity JSON (`{"tokens":[{"token":"random","owner_id":"operator","role":"admin","sites":["*"]}]}`) and service-token files. Set their paths, unique DB passwords, `PROCESSOR_API_TOKEN`, and HTTPS origins. Integrated start: `docker compose --env-file .env.stage9 -f compose.release.yaml --profile integrated up --build -d`. Existing-foundation start: `docker compose --env-file .env.stage9 -f compose.release.yaml -f compose.external-event.yaml up --build -d`.

Migration images build current source and complete before services. Never use `Base.create_all()`. Stop with matching arguments and `docker compose stop`; never use `down -v` on user data. Old Compose/API/client paths remain rollback options.

Roles are reader/user/admin; identity binds owner/sites server-side. Read requires reader+, Chat/rebuild user+, operations admin. UUID-only Subject paths and a fixed configured origin prevent open redirects. Evidence stays job-scoped through Event Intelligence service credentials. Browser credentials are memory-only; prefer gateway HttpOnly sessions. Android uses Android Keystore AES-GCM, clears tokens on unpair/sign-out, and Release rejects HTTP/header logging.

Never log Authorization, keys, prompts, full queries, Evidence, internal URLs, or chain-of-thought. API security headers and controlled CORS apply. Liveness/readiness and admin operations/metrics cover dependencies, backlog, retry, DLQ/error, model/search latency/error, token/cost, freshness, heartbeats and compatibility with bounded labels only.

Failure drills: stop model/worker (Video degrades; Event Intelligence stays healthy), inject wrong capability (startup refusal), remove secret (production refusal), and fail migration (dependents remain stopped).
