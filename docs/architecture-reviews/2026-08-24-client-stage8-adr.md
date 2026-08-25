# ADR: Stage 8 client product boundary

Status: Accepted for stage 8 (2026-08-24).

## Decision

Web and Android use Video Summary `/api/v1/capabilities`, Summary, Search and asynchronous Chat Job APIs by default. Every citation is an Event Intelligence Subject UUID opened through Video Summary `/api/v1/subjects/{subject_id}`; that endpoint redirects to the configured public Event Intelligence `/api/v1/events/{subject_id}` boundary. Clients do not know the internal Event Intelligence URL, call Frigate, or reproduce Review/Evidence rules.

The capability response exposes compatibility and mode metadata only. It never exposes tokens, prompts, internal service URLs or credentials. Chat renders answers, citations and degradation, but never chain-of-thought.

## Compatibility, ownership and security

Legacy DTOs, Retrofit methods, routes and ViewModels remain rollback-only; default navigation and the new Web product do not use them. `owner_id` provides record isolation only. `ownership_authentication=not-configured` states that it is not production authentication. Android has a centralized future `TokenProvider` boundary.

Android Debug permits configurable LAN HTTP. Release uses an HTTPS placeholder, rejects HTTP origins, disables cleartext and has no HTTP logger. Debug header logging redacts Authorization.

## Rollback

Rollback is a client/navigation change back to retained `/summary/today`, `/search`, `/timeline`, `/events/*` and `/chat` methods. No schema, legacy code or data is removed. Retirement requires separate authorization.
