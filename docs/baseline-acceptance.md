# BASELINE-001～005 acceptance record

Date: 2026-08-21
Scope: stage 0 only; no CONTRACT-001 work, foundation refactor, OpenCLIP migration, deployment, or runtime cutover.

## Repository and prerequisite audit

- Video Summary started at `e56a172` on `main`; pre-existing `android/gradle.properties` edits and both untracked migration reference documents were preserved.
- Event Intelligence was inspected as a separate repository. It contains pre-existing untracked assets and `docs/v0.2.0_api_release_scope.md`; none were changed.
- No prior stage-0 tests, migration fixture, acceptance snapshot, or progress log existed.
- No stage-1 contract artifact was assumed or created.

## BASELINE-001 — frozen legacy scope

The maintenance boundary is recorded in `docs/architecture.md`. The legacy runtime remains intact. No feature was added to the MQTT listener, Event model, Redis queue, media path, or OpenCLIP path.

## BASELINE-002 — backend baseline

`pytest` tests fix the following behavior:

- new/update/end Frigate payload parsing and invalid payload rejection;
- deterministic rule summary and empty-day output;
- keyword-stub query result ordering for `person`, `driveway`, `package`, and a no-match query;
- extractive count answer and empty-context fallback;
- Timeline/Search Pydantic serialization;
- default configuration without camera, database service, Redis service, private media, or cloud credentials.

Canonical output strings and structures are stored under `expected` in `tests/fixtures/migration-baseline.v1.json`.

## BASELINE-003 — Android baseline

JVM tests cover Timeline DTO deserialization, repository snapshot URL composition, Summary success state, Timeline failure state, and Search blank/success states. `assembleDebug` is the repeatable Debug APK build check.

UI acceptance record (code-level, no private screenshots):

| Page | Baseline acceptance |
|---|---|
| Summary | loading, summary/fallback content, and error state are represented |
| Timeline | newest-event list, camera filter, event navigation, snapshot URL are represented |
| Search | query editing, blank-query no-op, results, and error state are represented |
| Event detail | event fields and snapshot route are represented |
| Settings | base URL, camera filter, and health result are represented |

This record intentionally replaces screenshots: it is deterministic, contains no device/network identity, and can be checked without private media.

## BASELINE-004 — sanitized fixture

`tests/fixtures/migration-baseline.v1.json` is synthetic and contains no credentials or real media. Automated assertions cover person and vehicle reviews, multiple objects, available and unavailable evidence, duplicate/update delivery, a UTC date boundary, and the Toronto local-date boundary (UTC-04:00 for the fixture date). `fixture://` references are inert identifiers.

## BASELINE-005 — behavior comparison points

- Timeline: exact `TimelineResponse` JSON under `expected.timeline`.
- Search Top-K: four exact query result-ID lists under `expected.search`.
- Rule Summary: exact full-day text under `expected.rule_summary`.
- Extractive Chat: exact answer/context under `expected.chat.how_many_events`, plus an automated empty-context assertion.
- Android: JVM state tests and the UI acceptance table above.

## Known differences and limitations

- The legacy Timeline endpoint orders descending, while the stored list is a serialization-shape snapshot in fixture order; migration comparisons must independently apply endpoint ordering before comparing ranking.
- Keyword fallback scores are an empty list internally and API hits serialize nullable scores; there is no relevance score baseline.
- Rule Summary uses UTC day bounds; the Toronto boundary is preserved as a fixture and assertion, not treated as corrected legacy behavior.
- ViewModel tests use a fake public data-source seam and do not make network requests.
- UI acceptance is code-level and build-level; no emulator screenshot/golden framework existed before this stage.
- The tests deliberately do not validate production reliability, authentication, media safety, or Event Intelligence contracts.

## Exit decision

Stage 0 exit conditions are met: the fixed fixture repeats offline; core behavior has tests or exact snapshots; no real camera/private media/cloud key is needed; comparison points are explicit; and no legacy queue or Event feature was added. The runtime path is unchanged, so rollback consists of removing test/documentation assets only. Do not start CONTRACT-001 automatically.
