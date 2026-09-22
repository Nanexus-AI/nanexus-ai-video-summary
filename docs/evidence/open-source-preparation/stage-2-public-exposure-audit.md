# Stage 2 — Public-exposure audit

## Sanitized findings

- No confirmed live credential, private key, committed `.env`, or real-camera media was found in the reviewed tree and targeted history review.
- Personal workstation, local-network, and machine-specific path information required sanitization.
- Development PostgreSQL, Redis, and MQTT exposure required hardening.
- The obsolete Event Intelligence sibling layout required portability cleanup.
- Raw prompts and raw acceptance evidence were classified as private.
- Ignored and generated artifacts remained outside the release boundary.
- A targeted Git-history exposure review was performed.

Publication of the repository unchanged was blocked until the approved cleanup was completed.

## Trusted-network decision

Internal services are intended for trusted-network deployment by default. Deployers are responsible for appropriate infrastructure and controls for any external access. The project does not claim to provide a complete public-network gateway.

## Gate decision

**PASS** — the exposure audit produced an approved cleanup scope and a documented deployment-security boundary.
