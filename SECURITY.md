# Security

## Supported security scope

Security reports are welcome for the current Nanexus AI Video Summary source and its documented deployment boundaries. Reports about the application API, Web or Android clients, authentication and authorization, secret handling, data isolation, dependency use, and the public HTTP/v1 integration with Nanexus Event Intelligence are in scope.

This project is source-first and is still completing initial-release validation. A supported source checkout does not by itself provide a hardened public-internet deployment.

## Deployment boundary

The default deployment assumes a trusted internal network. PostgreSQL, Redis, MQTT, workers, model services, and Event Intelligence processor- or middleware-facing services are internal components. Do not expose them directly to untrusted networks.

Web and the Video Summary API are the intended ingress surfaces. Anyone making them externally reachable is responsible for appropriate TLS, firewalling, authentication, authorization, rate limiting, monitoring, and network access controls. A VPN, protected reverse proxy, authentication gateway, or zero-trust access layer may be appropriate. This repository does not provide a complete public-network security gateway.

See [Deployment](docs/deployment.md) before operating beyond local or trusted-network development.

## Secrets and credentials

- Never commit `.env` files, tokens, passwords, identity files, signing keys, Android keystores, private keys, camera credentials, or customer configuration.
- Treat values in `.env.example`, development authentication, blank tokens, and anonymous local MQTT as development-only defaults.
- Store deployment secrets outside version control, restrict their permissions, use distinct service and user identities, and rotate credentials according to the deployment's operating policy.
- Avoid logging authorization headers, tokens, prompts, evidence, private URLs, or sensitive query content.

If a secret is exposed, revoke or rotate it immediately. Removing it from a later commit is not sufficient.

## Models, downloads, and caches

No pretrained model weights or pre-populated model caches are bundled. OpenCLIP weights are obtained on demand by upstream tooling and cached locally. Operators are responsible for download provenance, upstream availability, storage permissions, cache integrity, and any applicable model terms. Model weights and caches must not be added to this repository.

The default validated Linux dependency path is CPU-oriented. The separate containerized
GPU/CUDA dependency route and NVIDIA device reservation have also passed hardware validation.
That compatibility result is not a security guarantee for other host, driver, toolkit, or GPU
combinations.

## Dependencies and supply chain

Use `pyproject.toml` with the committed `uv.lock` for reproducible Python environments, `web/package-lock.json` for Web dependencies, and the committed Gradle wrapper and Android declarations for Android builds. Review intentional dependency changes and regenerate the relevant lock data rather than editing it by hand. Record source revisions and locally built artifact identities where deployment reproducibility matters.

External packages, container base images, Gradle artifacts, and model downloads remain upstream supply-chain inputs. Deployers should apply their own vulnerability scanning, artifact retention, update, and provenance policies.

## Reporting a vulnerability

No dedicated security mailbox or configured private vulnerability-reporting channel is documented for this repository. Do not put sensitive vulnerability details in a public issue.

To request a private reporting route, open a minimal issue in the repository's public issue tracker after it becomes available. State only that you have a potential security report and need private contact instructions. If no issue tracker is available, wait for the project to publish a reporting channel rather than disclosing sensitive details publicly.

Once a private route is established, include:

- the affected revision, version, component, and deployment mode;
- a concise impact assessment and the required preconditions;
- sanitized, reproducible steps or a minimal proof of concept;
- whether the issue crosses the documented trusted-network boundary;
- any known mitigations; and
- a safe way to contact you for follow-up.

Do **not** post secrets, credentials, exploit payloads, private IP addresses, camera URLs, customer or camera data, private logs, internal topology, or unredacted screenshots in a public issue. Use synthetic data and redact identifiers wherever possible.

## Scope and operator responsibility

Configuration-specific exposure of internal services, weak external gateways, reused development credentials, third-party infrastructure, unsupported modifications, and failures to secure the host or network are primarily deployment responsibilities. Reports that identify a project defect enabling or worsening those failures are still useful; describe the project-controlled behavior separately from the deployment configuration.

Nanexus Event Intelligence is a separate project. Vulnerabilities confined to its implementation should be reported through that project's process. Cross-project contract or integration issues may be reported here with both affected revisions, without publishing sensitive details.
