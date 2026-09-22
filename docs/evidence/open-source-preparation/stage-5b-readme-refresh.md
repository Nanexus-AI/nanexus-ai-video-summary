# Stage 5B README refresh evidence

## Scope

Rewrote only the public `README.md` landing page and added this evidence record. No runtime,
dependency, Compose, or other documentation file was changed for Stage 5B.

## Claims replaced

- Replaced the M2/M3 project framing with an honest initial-release maturity statement.
- Replaced the Frigate-first identity with the Camera/NVR/VMS → Event Intelligence → Video
  Summary architecture while retaining Frigate as a current integration and rollback path.
- Replaced stale service/API summaries and the old OpenCLIP identity with current v1 capability
  wording and `ViT-B-32-quickgelu` / `openai`.
- Removed workstation-specific paths, example LAN addresses, and implied release artifacts.

## Current framing and quick-start basis

The README identifies Event Intelligence as separate vendor-neutral middleware and Video Summary
as the upper application layer. It describes public HTTP/v1 integration, optional local source
builds, the configurable `EVENT_INTELLIGENCE_SOURCE_DIR`, and the supported default sibling
checkout without making source proximity a runtime requirement.

The quick start uses the smallest tracked, currently validated no-camera path: loopback-bound
development infrastructure, synthetic `seed_events.py` data, and the legacy-compatible
`AI_MODE=stub` worker/API flow. It needs no model weights, GPU, cloud key, real camera, or private
network. Integrated and external v1 topology guidance is deferred rather than inferred from the
multiple release and integration Compose files.

## Boundaries documented

- **Security:** trusted-network default; internal services stay off untrusted networks;
  development credentials and anonymous MQTT remain development-only; deployers supply VPN,
  TLS/authentication gateway, zero-trust, or equivalent controls; no complete public gateway is
  claimed.
- **CPU/GPU:** Linux CPU OpenCLIP is supported and tested; CUDA/GPU is an intended project path,
  but explicit Linux Torch resolution still targets the CPU wheel index and CUDA release
  verification remains open.
- **Release/bundling:** source-first; no bundled weights, caches, camera media, private
  configuration, published container images, or downloadable APK/AAB artifacts are promised.

## Links and verification

README relative links were checked against existing paths: `docs/architecture.md`,
`docs/compatibility-matrix.md`, `docs/deployment-security-runbook.md`,
`docs/android-dev-machine.md`, `docs/resource-profiles.md`, `.env.example`, `LICENSE`, `web/`, and
`android/`. Quick-start commands were checked against `docker-compose.yml`, `.env.example`,
`pyproject.toml`, the service module entry points, `scripts/seed_events.py`, and
`scripts/build_summary.py`. The referenced base Compose configuration was rendered successfully.

Verification also included `git diff --check`, complete README diff review, scans for M2/M3
framing, obsolete repository names, stale model defaults, personal paths/IPs, CPU/GPU
contradictions, and unsafe network wording. The ignored private Stage 9 prompt, raw CPU evidence,
and local CPU gate Compose file remained ignored and untracked.

## Deferred documentation work

Dedicated public development, deployment, Android, security, and consolidated architecture
documents remain future documentation work. Selecting and documenting one complete public v1
integrated/external Compose demo is also deferred; this refresh does not convert historical
acceptance material into user workflow guidance.

## Gate recommendation

**PASS**, subject to the verification results recorded above remaining clean.
