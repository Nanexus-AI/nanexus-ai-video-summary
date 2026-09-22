# Stage 6F-1 Event Intelligence integration evidence

Date: 2026-09-20
Final verdict: **PASS**
Gate 6F-1 recommendation: **PASS**

## Executive summary

The final clean-candidate re-verification passed the complete synthetic Event Intelligence to
Video Summary integration through the intended public HTTP/v1 boundaries. The run combined and
validated all three reviewed corrections:

1. Event Intelligence now populates public `EventDetail.review_item_id` with the canonical
   ReviewItem UUID.
2. Video Summary emits the implemented, job-scoped Search evidence path without a duplicated
   segment.
3. Video Summary subjects redirect to Event Intelligence's canonical public
   `/api/v1/review-items/{review_item_id}` route.

One sanitized ended vehicle review traversed real Event Intelligence services, was claimed and
enriched by the real Video Summary processor worker using the deterministic Stub provider, and
appeared in a non-empty rule Summary, semantic Search, asynchronous explicit-date Chat, and the
nginx/Web proxy. The generated Search evidence URL returned the expected synthetic PNG. A
bounded application-service restart preserved readiness, Search, subject resolution, and
evidence access. No new independent defect was found, and Stage 6F-2 was not begun.

## Candidate identities and preflight

| Candidate | Branch and base HEAD | Construction and staged state | Files | Manifest SHA-256 |
|---|---|---|---:|---|
| Video Summary | `main`, `da3b7c6eb32160d927ff5101194698478da8b2de` | HEAD plus the complete reviewed tracked/untracked public candidate; source index empty | 208 | `53977c5396f9df67dc30cef6dc6c090fca09585fc53ee19732a9cecfd56f9b06` |
| Event Intelligence | `main`, `89bbcd7c4eeb867bdef0c04827b50a6796679856` | HEAD plus the four reviewed tracked changes and the three focused untracked review-item route/tests; unrelated images/document excluded; source index empty | 255 | `4c32277d16da86184e7c75d5f2fca84defc7958d9d43512930fecd2419ae71e2` |

Both candidates were exported to fresh `/tmp` directories. Candidate manifests were identical
before startup and immediately before cleanup. Scans found no private `.env`, database, log,
credential/key, application cache, APK/AAB, or model artifact in either candidate.

## Topology and boundary

The uniquely named Compose project `nanexus-stage6f1-final` used:

- an Event PostgreSQL database, migration, API, pipeline worker, synthetic fixture seeder, and
  credential-free synthetic snapshot server;
- a separate Video PostgreSQL database, migration, Redis, deterministic Stub model service,
  enrichment, embedding, summary, and chat workers, API, and nginx/Web service;
- project-owned network and volumes, temporary static identities, and loopback-only public
  ports.

The fixture remained the reviewed Frigate 0.17 `vehicle-lifecycle` data and generated 224x224
PNG. Runtime integration used public HTTP/v1 capability, processor job, job-scoped subject and
evidence, result submission, events, ReviewItem, and Video Summary client endpoints. No runtime
service imported sibling source or read sibling repository files.

## Identity invariant

The synthetic observation UUID and canonical ReviewItem UUID were deliberately distinct.

The canonical ReviewItem UUID matched across:

- public `EventDetail.review_item_id`;
- persisted `ProcessorJob.subject_id` with `subject_type=review_item`;
- the public processor subject response;
- Video Summary Search `subject_id`;
- Summary source/highlight subject IDs;
- Chat `related_subject_ids` and citation `subject_id`.

Namespace separation also passed. `GET /api/v1/events/{observation_id}` returned HTTP 200 and
the matching `review_item_id`; the ReviewItem UUID at `/events/{id}` returned 404.
`GET /api/v1/review-items/{review_item_id}` returned HTTP 200 with both IDs; the observation UUID
at `/review-items/{id}` returned 404.

## Processor and public-boundary flow

The real enrichment worker negotiated processor contract `1.0`, claimed the single real job,
fetched its public job-scoped subject and granted evidence, invoked the deterministic Stub, and
submitted the result. The persisted/public audit values showed:

- the job reached status `succeeded` with attempt count `1`;
- the subject revision, evidence UUID, and caption claim UUID were populated and remained
  consistent across the flow;
- invocation `deterministic-stub`, runtime `1.0+stub-labels-v1+cpu`, `local_only`,
  `external_network_used=false`, status `succeeded`;
- caption `Zero-shot stub enrichment for the selected snapshot`.

The public job subject returned the same canonical subject, revision, lifecycle, labels, zones,
camera, site, and occurrence time. A subsequent `/jobs/next` returned `null`. Requesting an
evidence UUID outside the completed job's grant returned HTTP 403, reconfirming job scope.

## Integrated Summary

The authenticated asynchronous rebuild for `2026-02-02`, timezone `UTC`, site
`community-demo`, and rule mode moved from `queued` to `ready`. Its content reported one review,
`car=1`, and a highlight at Community Demo Entrance with the deterministic Stub caption. Its
structured content contained `review_count: 1`, the canonical ReviewItem UUID, the source claim
UUID, zone `entrance`, ten-second duration, and decision `send`. The previous `no reviews
recorded` behavior is gone.

## Search and evidence HTTP

Authenticated `POST /api/v1/search` returned one non-degraded `cosine-pgvector` result using
`deterministic-stub` version `1.0+stub-labels-v1+cpu`. The result preserved the canonical
ReviewItem UUID, subject revision, source claim, site, label, and occurrence time. It exposed the
expected subject path `/api/v1/subjects/{review_item_id}` and evidence path
`/api/v1/search/evidence/{job_id}/{evidence_id}`.

There was no duplicated `/evidence/` segment and no internal Event Intelligence processor URL.
Requesting that exact generated evidence path returned HTTP 200, `image/png`, 748 bytes, and
SHA-256 `bf031e5aa343c31e55003ef2eddeb5b46cc73c92e1d99e9839d7083429ed546d`.

## Chat citation and subject resolution

The authenticated asynchronous explicit-date request `vehicle on 2026-02-02` reached `ready`.
It retrieved the ready Summary and one related review subject, answered with the car highlight
and deterministic caption, and cited the expected `/api/v1/subjects/{review_item_id}` route.

Extractive mode correctly reported `degraded=true` because no LLM completion was requested; the
retrieval itself was `semantic-search+summary` and had no error. The cited Video Summary path
returned HTTP 307 to the loopback `/api/v1/review-items/{review_item_id}` route.

Following the redirect returned HTTP 200. The Event Intelligence response contained
`review_item_id` equal to the cited canonical UUID and observation `id` equal to the distinct
observation UUID.

## Web proxy regression

Through the real nginx/Web boundary, client capabilities returned HTTP 200, authenticated Search
returned the same canonical subject and corrected evidence path, representative subject access
returned the same 307 ReviewItem redirect, and representative evidence access returned the same
748-byte PNG with HTTP 200. API proxy behavior was healthy; UI polish was not evaluated.

## Negative-boundary verification

Event and Video databases were separate containers and volumes; each held its own single
integration record. Runtime mount inspection showed no Event source mount and no sibling
filesystem mount in Event API/worker or Video API/worker services. Only generated static identity
secrets and the project-owned model-cache volume were mounted where configured. The cache
contained uv package/build cache only; the only `.pth` files were Python path metadata, and no
OpenCLIP/model checkpoint, ONNX, safetensors, or other model weights were present.

The run used no shared database, direct cross-repository runtime import, private `.env`, real
camera, private network identity, GPU, cloud key, or model weights. The invocation explicitly
recorded local-only routing and no external network use.

## Restart and repeatability

Event API/worker and all Video application workers, API, and Web were restarted together. After
recovery, Event health was `ok`; Video readiness was `ready` with no missing workers/services;
Search returned the same canonical subject and evidence path; subject access again returned the
same 307 ReviewItem redirect; and evidence again returned HTTP 200, 748 bytes, and the identical
SHA-256.

## Cleanup and pollution audit

After capture, the isolated Compose project was removed with its orphans, volumes, and locally
built project images. Temporary candidates, identities, overlay, response bodies, and synthetic
media were removed. Pre-existing Docker resources were not modified. Both source repositories
retained their preflight working-tree changes and empty indexes. No synthetic database, media,
log, cache, model weight, or runtime secret entered either source repository. This evidence file
is the only intended source-tree change made by final verification.

## Remaining limitations

The Web check exercised its real nginx/API boundary rather than browser UI behavior. Chat used
the intended deterministic extractive mode, so `degraded=true` denotes the absence of an LLM
completion and is not an integration failure. The legacy `/health` payload still reports its
independent default `ai_mode=openclip`; the v1 model service and processor audit correctly report
the configured deterministic Stub and no OpenCLIP path was used. No Stage 6F-2 CPU/GPU/model
work was performed.

## Final gate result

All twelve Stage 6F-1 pass criteria are satisfied. **Stage 6F-1 verdict: PASS. Gate 6F-1
recommendation: PASS.**
