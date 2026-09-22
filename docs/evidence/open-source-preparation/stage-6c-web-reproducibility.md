# Stage 6C Web reproducibility verification

Date: 2026-09-19
Repository: Nanexus AI Video Summary
Scope: isolated Web client execution and verification only

## Executive summary

The reviewed public Web candidate is reproducible on the available compatible Node 22 runtime.
A clean locked install succeeded, type checking and lint passed, all 3 defined tests passed, and
the production build completed. Practical inspection found no private/public-boundary exposure
in the generated bundle, and the main worktree remained unstaged and otherwise unchanged.

The repository explicitly identifies Node 22.14.0 as the currently validated baseline. A
corrective run used the official `node:22.14.0` container without changing the host runtime and
passed the complete workflow. Stage 6C therefore **passes** on both the exact baseline and the
previously tested later Node 22 patch.

## Clean candidate and identity

- Source branch and HEAD before construction: `main` at
  `da3b7c6eb32160d927ff5101194698478da8b2de`.
- The source index was empty; `git diff --cached --name-status` produced no entries.
- A detached temporary worktree was created from that exact HEAD. The reviewed binary-safe
  tracked diff was applied and the 44 public untracked paths approved through Stages 6A and 6B
  were copied individually.
- Tracked-patch SHA-256:
  `e0f52240531852e2e8db9760f56a7b01b926c0080fc1132024ae59eb8869409a`.
- The pre-install candidate manifest covered 201 files: 138 unchanged HEAD files, 19 files from
  the tracked patch, and 44 allowlisted untracked files. Each entry recorded origin, size,
  SHA-256, and candidate-relative path.
- Candidate-manifest SHA-256:
  `2afad4dc012376657b3a56c06b9e232ac5bb46326f44c234326084f9c81b6f79`.
- The candidate excluded source-worktree `web/node_modules`, existing `web/dist`, `.env`, named
  private Stage 9 files, caches, logs, databases, and raw evidence by construction.

## Node and npm environment

- `.nvmrc`: `22.14.0`.
- `README.md` and `docs/development.md`: Node 22.14.0 is the currently validated Web toolchain.
- `web/package.json` does not declare a separate `engines` constraint; the lockfile root also
  does not override the documented baseline.
- Initial runtime used: Node `v22.23.2` and npm `10.9.8`.
- Exact-baseline corrective runtime: Node `v22.14.0` and npm `10.9.2` in the official
  `node:22.14.0` container image, pulled at digest
  `sha256:e5ddf893cc6aeab0e5126e4edae35aa43893e2836d1d246140167ccc2616f5d7`.
- Installed local runtimes included Node 20.20.2, 22.22.3, and 22.23.2, but not 22.14.0. No
  system runtime or declared version was replaced or edited.

### Exact-baseline status

**Verified.** The corrective container reported exactly Node `v22.14.0`; it did not replace or
modify the host's global or version-managed Node installations. The exact runtime passed the
locked install, typecheck, lint, tests, and production build.

## Locked dependency installation

`npm ci` used a fresh candidate-owned npm cache and did not reuse the source worktree's
`node_modules`. A sandboxed attempt reached package installation but could not execute the
esbuild binary because of an environment `EPERM`; the identical locked install succeeded when
execution and public registry access were allowed.

- Result: passed; 341 packages added and 342 packages audited.
- Network: required for the fresh cache.
- Lockfile SHA-256 before and after:
  `f9468c06062def886fead088310e24559301555f68a6e8f2bb7703fdd601f8f4`.
- No dependency version or lock data changed, and no audit fix was run.

The exact-baseline corrective `npm ci` used a new disposable cache and installed 340 packages,
auditing 341 packages under npm 10.9.2. The one-package count difference from npm 10.9.8 did not
alter the lockfile, source, defined checks, or generated production bundle.

## Typecheck, lint, tests, and production build

| Check | Result |
|---|---|
| `npm run typecheck` | passed with no TypeScript errors |
| `npm run lint` | passed with no ESLint errors |
| `npm test` | 1 test file passed; 3 passed, 0 failed, 0 skipped |
| `npm run build` | passed; TypeScript build and Vite 6.4.3 build completed |

The production build transformed 30 modules and generated three ignored files under `dist/`:
`index.html` (168 bytes), one CSS asset (543 bytes), and one JavaScript asset (192,104 bytes).
No generated build output was copied to the main worktree or selected for publication.

## Bundle and public-boundary inspection

Practical inspection of all generated assets found:

- no original personal/repository path, private LAN address, or embedded localhost/API target;
- no AWS, GitHub, OpenAI, Google API, or private-key-shaped credential;
- no source map or source-map marker;
- no Vitest, jsdom, Testing Library, test-file, mock, or fixture marker;
- no `caniuse-lite` or Browserslist marker, supporting the Stage 3 conclusion that these
  build-time inputs are not shipped as production application data; and
- only expected standards/React documentation URLs.

The bundle uses same-origin API paths. It includes the literal development fallback header
`X-Nanexus-Dev-Owner: local-web`; this is an identifier, not a secret. Production backend
configuration refuses development authentication, and the public deployment documentation
requires deployment-controlled authentication and ingress. No obsolete repository name or
unexpected third-party data was apparent.

## Development proxy and configuration truthfulness

`web/vite.config.ts` proxies `/api` to `VITE_API_PROXY_TARGET` when set and otherwise to
`http://localhost:8000`. The `dev` script binds Vite with `--host 0.0.0.0`. These facts match
the README and development guide, including their trusted-network warning, normal Vite port
5173, configurable target, and distinction from the release Web container on loopback port
8080. The production bundle contains neither the proxy variable nor its localhost default,
which is correct because the Vite server proxy is development-only.

## npm vulnerability summary

The install/audit reported 3 findings: 2 moderate and 1 high, with no critical findings.

- Moderate: the direct `vitest` development dependency and transitive `@vitest/mocker` are
  affected by GHSA-82fw-gwwq-j7x9 (redirect-mock path traversal/arbitrary file read). The
  reported available Vitest remediation is semver-major.
- High: transitive `js-yaml` is affected by GHSA-2883-xcg3-v3hh (CPU exhaustion involving merge
  keys).

These findings are recorded separately from build reproducibility. Stage 6C did not run
`npm audit fix`, change dependency versions, or claim vulnerability remediation.

## Pollution and main-worktree audit

- Candidate source hashes remained identical to the 201-file pre-install manifest after all
  checks; the tracked lockfile was byte-identical.
- Candidate-only generated content was limited to ignored `web/node_modules/`, `web/dist/`, and
  `web/tsconfig.app.tsbuildinfo`, plus the explicitly isolated npm cache. Tests produced no
  coverage tree or repository log.
- Those outputs and the detached candidate were disposable and removed after evidence capture.
- The main worktree retained the same branch and HEAD, an empty index, all pre-existing public
  dirty work, and ignored private Stage 9 material. The only new main-worktree path from this
  task is this sanitized evidence artifact.

For the corrective run, the detached candidate contained 202 source files: the prior 201-file
candidate plus this Stage 6C evidence artifact as the 45th explicitly allowlisted untracked
file. Its pre-install manifest SHA-256 was
`806919b862731566e8ca9bd2dc2809fd7cd6e5daf6f4b5b98ae2d046275fa4e1`.
Post-run verification found zero source-hash changes and the same lockfile SHA-256. Candidate
output was limited to ignored `node_modules`, `dist`, TypeScript metadata, and its isolated npm
cache; all were removed with the detached candidate after evidence capture. The exact build
reproduced the same three asset names and byte sizes as the Node 22.23.2 build and repeated the
public-boundary checks with no exposure found.

## Limitations and gate recommendation

No Web source defect was found. Cross-service integration was not attempted because Stage 6F
owns it. The npm advisories remain separately unresolved and require a reviewed dependency-
remediation task, but they did not affect exact-runtime reproducibility.

**Stage 6C verdict: PASS.** The exact Node 22.14.0 clean candidate passed locked installation,
typecheck, lint, all defined tests, production build, bundle-boundary inspection, and pollution
controls without changing source or lock data. Stage 6C is closed; Stage 6D was not started.
