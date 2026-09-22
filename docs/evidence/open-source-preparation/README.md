# Open-source preparation evidence

This directory contains concise, sanitized public engineering evidence from the repository's open-source preparation. The records support reproducibility and stage-gate review by describing what was checked, the conclusions and decisions reached, remaining risks, and the basis for each gate result.

Raw or private evidence is intentionally excluded. Machine-specific or sensitive logs, execution prompts, scanner output, runtime identifiers, and other local evidence are not committed here. These records are not a substitute for release notes, deployment documentation, security guidance, or artifact-specific licensing materials.

## Evidence index

- [Stage 0 — Repository baseline](stage-0-repository-baseline.md)
- [Stage 1 — Dirty-tree classification](stage-1-dirty-tree-classification.md)
- [Stage 2 — Public-exposure audit](stage-2-public-exposure-audit.md)
- [Stage 3 — Licensing audit](stage-3-licensing-audit.md)
- [Stage 4A — License and provenance](stage-4a-license-and-provenance.md)
- [Stage 4B — Personal and network sanitization](stage-4b-personal-network-sanitization.md)
- [Stage 4C — Trusted-network security](stage-4c-trusted-network-security.md)
- [Stage 4D — Event Intelligence portability](stage-4d-event-intelligence-portability.md)
- [Stage 4E — Ignore and evidence boundary](stage-4e-ignore-and-evidence-boundary.md)
- [Stage 5A — Documentation inventory and information architecture](stage-5a-documentation-inventory.md)
- [Stage 5B — README refresh](stage-5b-readme-refresh.md)
- [Stage 5C — Core technical documentation](stage-5c-core-technical-docs.md)
- [Stage 5D — Security, contributing, and Android documentation](stage-5d-security-contributing-android.md)
- [Stage 5E — Historical documentation cleanup](stage-5e-historical-doc-cleanup.md)
- [Stage 5F — Full documentation review](stage-5f-full-documentation-review.md)
- [Stage 6B — Backend reproducibility verification](stage-6b-backend-reproducibility.md)

## Release-workspace hygiene

Public releases should be built and verified from a clean checkout or clean clone, using tracked public files and reproducible dependency manifests. The current working directory must not be archived wholesale: it may contain ignored, generated, private, or machine-specific material outside the public release boundary.
