# Contributing

Thank you for contributing to Nanexus AI Video Summary. Keep changes focused, reproducible, and consistent with the project's public boundaries.

This project is still in an early stage of active development, so external contributions are considered conservatively. Small bug fixes, documentation corrections, tests, and narrowly scoped compatibility improvements are the best fit at this stage. Discuss non-trivial features, API or contract changes, architecture changes, dependency changes, large refactors, and broad UI or product changes with the maintainers before beginning significant work. Large unsolicited changes may be declined or deferred even when technically sound if they do not align with the project's current development phase or maintenance direction.

## Scope and architecture

Nanexus AI Video Summary is the application layer for timelines, summaries, search, chat, and Web/Android experiences. Nanexus Event Intelligence is separate lower-level middleware for vendor-neutral event processing. Normal runtime integration uses public, versioned HTTP/v1 contracts; Video Summary must not import Event Intelligence source, share its database, or depend on its internal queues or storage.

Read [Architecture](docs/architecture.md), [Development](docs/development.md), and [Security](SECURITY.md) before changing a boundary or deployment assumption.

## Development setup

The current prerequisites are Python 3.12, `uv`, Docker with Compose, Node.js 22.14.0 with npm for Web work, and JDK 17 plus Android SDK 35 for Android work. Use only the parts needed by your change.

For the preferred Python setup:

```bash
uv sync --extra test
source .venv/bin/activate
```

Add `--extra openclip` for model-provider work and for the complete static-check environment,
because Mypy intentionally checks the optional provider modules. Do not add `--extra openclip-cuda`
to the default Linux development environment; that extra is the GPU container path. `pyproject.toml`
defines Python project metadata and direct dependencies; `uv.lock` is the committed reproducible
resolution.
Make dependency changes in `pyproject.toml`, relock intentionally, and use `uv lock --check` to
detect drift. Do not hand-edit `uv.lock`. `requirements.txt` is a legacy/alternate pip list, not
the reproducibility authority.

Copy `.env.example` to an untracked `.env` for local configuration. The deterministic Stub path is preferred when a contribution does not require model downloads. Detailed workflows are in [Development](docs/development.md); Web setup is under its [Web development section](docs/development.md#web-development), and Android setup is in the [Android guide](docs/android.md).

## Checks

Run the checks relevant to the files you change.

Backend:

```bash
uv lock --check
uv sync --frozen --extra test --extra openclip
uv run pytest
uv run ruff check .
uv run mypy
```

Web, from `web/`:

```bash
npm ci
npm test
npm run lint
npm run typecheck
npm run build
```

Android, from `android/`:

```bash
./gradlew testDebugUnitTest
./gradlew assembleDebug
```

Also run `git diff --check` and review `git status --short` before submitting. Do not claim checks that you did not run; explain skipped checks and environmental limits.

## Contribution principles

- Prefer the smallest change that solves one clear problem. Avoid unrelated refactors, formatting churn, dependency updates, or generated-file changes.
- Include tests or other reproducible evidence for behavior changes. Bug fixes should describe the failing case and how the change was verified.
- Preserve the trusted-network and internal-service boundary. Do not make databases, Redis, MQTT, workers, model services, or middleware-facing services public by default.
- Keep credentials, real camera media, private network details, customer data, private infrastructure, downloaded model weights, caches, APK/AAB files, and local build artifacts out of commits.
- Do not weaken HTTPS, authentication, authorization, capability checks, or secret handling merely to simplify local setup.
- Keep documentation and examples sanitized. Use synthetic data, placeholder hosts, and documented emulator aliases.

For a security-sensitive finding, follow [SECURITY.md](SECURITY.md) and do not publish sensitive details in an issue or pull request.

## Cross-repository changes

Changes to Event Intelligence belong in its repository. When a feature requires both repositories, keep each change independently reviewable, use the public versioned contract between them, update compatibility documentation, and identify the corresponding revision or pull request in each project. Do not temporarily couple repositories through shared source, databases, or private APIs.

## Commits and pull requests

Write focused commits with messages that explain the intent. Do not commit generated build outputs, local configuration, editor state, caches, audit output, or drive-by cleanup. Review the complete diff for accidental secrets and machine-specific paths.

A pull request should:

- explain the problem, scope, and user-visible or architectural effect;
- link related issues when available;
- list verification performed and any checks not run;
- call out dependency, schema, contract, security, or compatibility effects;
- include migration or rollback notes when relevant; and
- update public documentation when behavior or setup changes.

There is no contribution requirement here for a CLA or DCO. Do not assume an unconfigured CI, branch-protection, or release-automation policy; maintainers may request appropriate evidence during review.

## License

The project is licensed under the [Apache License 2.0](LICENSE). Unless you explicitly state otherwise, contributions intentionally submitted for inclusion are provided under that license as described in its contribution terms. Submit only work you have the right to contribute and preserve required third-party notices and attribution.
