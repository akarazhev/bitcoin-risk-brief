# Dependency And License Review

This file records local engineering evidence only. It is not legal advice, a full license compliance opinion, a
vulnerability scan, or a production-launch approval.

## 2026-07-10 Local Dependabot Configuration Pass

Gate status: partial local evidence recorded, not launch-passed. `.github/dependabot.yml` was added locally at
`68439864a46c5ffe49c6ae76cd925e67aaeb7fca`. The local evidence tag
`privacy-terms-local-evidence-2026-07-10` was present. No deploy, data refresh/import, cache warmup, real waitlist POST,
Cloudflare/routing change, commit, push, or tag was performed for this pass.

Configured monthly Dependabot version-update sources:

| Ecosystem | Directory | Local source |
| --- | --- | --- |
| `npm` | `/frontend` | `frontend/package.json`, `frontend/package-lock.json` |
| `pip` | `/backend` | `backend/requirements.txt` |
| `pip` | `/collector` | `collector/requirements.txt` |
| `github-actions` | `/` | `.github/workflows/ci.yml` |
| `docker` | `/backend` | `backend/Dockerfile` |
| `docker` | `/collector` | `collector/Dockerfile` |
| `docker` | `/frontend` | `frontend/Dockerfile` |
| `docker-compose` | `/` | root Compose-style image references, including the Podman Compose files if GitHub's parser accepts those filenames |

The configuration uses monthly schedules, modest open pull request limits, and one simple group per update source. It
does not add private registries, secrets, reviewer handles, assignees, private URLs, account details, or environment
values.

Conservative finding: GitHub-hosted Dependabot execution, first PR evidence, and confirmation of root Podman Compose
filename handling remain pending until this local config is merged/pushed and observed in GitHub. This pass does not
claim vulnerability/advisory clearance, legal approval, license compatibility, full license compliance, container image
license review, OS package license review, or CI action/license approval.

## 2026-07-10 Local Evidence Pass

Gate status: partial, not launch-passed. Local dependency and container references were reviewed from repository files at
`b26daf6407d88a2a65bc278f1ef0cc3343bd3040`. The existing evidence tag
`waitlist-accessibility-local-evidence-2026-07-10` was present. No deploy, data refresh/import, cache warmup, real
waitlist POST, Cloudflare/routing change, commit, push, or tag was performed for this pass.

Reviewed local sources:

- `frontend/package.json`
- `frontend/package-lock.json`
- `backend/requirements.txt`
- `collector/requirements.txt`
- `pyproject.toml`
- `backend/Dockerfile`
- `collector/Dockerfile`
- `frontend/Dockerfile`
- `podman-compose.yml`
- `podman-compose.cloudflare.yml`
- `.github/workflows/ci.yml`

No root-level runtime package manifest was found beyond `pyproject.toml`, which only defines pytest discovery settings.
No backend or collector Python lockfile was present. No local Python package `METADATA` or `PKG-INFO` files were found in
the repository scan.

## Frontend Npm Inventory

The frontend lockfile is npm lockfile version 3. The local lockfile contains 160 non-root package entries; every non-root
entry has a `license` field in the local lockfile. License identifiers observed across the lockfile were:

| License identifier from local lockfile | Package entries |
| --- | ---: |
| `MIT` | 118 |
| `MPL-2.0` | 14 |
| `Apache-2.0` | 9 |
| `ISC` | 5 |
| `0BSD` | 5 |
| `BSD-3-Clause` | 3 |
| `BSD-2-Clause` | 2 |
| `MIT-0` | 2 |
| `BlueOak-1.0.0` | 1 |
| `CC0-1.0` | 1 |

Direct frontend dependencies from `frontend/package.json` and their local lockfile metadata:

| Scope in manifest | Package | Declared range | Locked version | Local license metadata |
| --- | --- | --- | --- | --- |
| dependency | `@vitejs/plugin-react` | `latest` | `6.0.3` | `MIT` |
| dependency | `echarts` | `latest` | `6.1.0` | `Apache-2.0` |
| dependency | `echarts-for-react` | `latest` | `3.0.6` | `MIT` |
| dependency | `lucide-react` | `latest` | `1.21.0` | `ISC` |
| dependency | `react` | `latest` | `19.2.7` | `MIT` |
| dependency | `react-dom` | `latest` | `19.2.7` | `MIT` |
| dependency | `typescript` | `latest` | `6.0.3` | `Apache-2.0` |
| dependency | `vite` | `latest` | `8.1.0` | `MIT` |
| devDependency | `@axe-core/playwright` | `^4.12.1` | `4.12.1` | `MPL-2.0` |
| devDependency | `@playwright/test` | `^1.61.1` | `1.61.1` | `Apache-2.0` |
| devDependency | `@testing-library/jest-dom` | `latest` | `6.9.1` | `MIT` |
| devDependency | `@testing-library/react` | `latest` | `16.3.2` | `MIT` |
| devDependency | `@types/react` | `latest` | `19.2.17` | `MIT` |
| devDependency | `@types/react-dom` | `latest` | `19.2.3` | `MIT` |
| devDependency | `jsdom` | `latest` | `29.1.1` | `MIT` |
| devDependency | `vitest` | `latest` | `4.1.9` | `MIT` |

Accessibility tooling added for the focused local accessibility pass:

- `@axe-core/playwright` is a direct devDependency locked at `4.12.1` with local lockfile license metadata `MPL-2.0`.
- `@axe-core/playwright` depends on `axe-core` `~4.12.1`.
- `axe-core` is locked transitively at `4.12.1` with local lockfile license metadata `MPL-2.0`.
- `@axe-core/playwright` has a peer dependency on `playwright-core >= 1.0.0`; `playwright-core` is locked at `1.61.1`
  with local lockfile license metadata `Apache-2.0`.

Conservative finding: local npm lockfile metadata does not show missing license fields. External registry/tarball
verification, license text review, legal compatibility review, and vulnerability/advisory review remain pending.

## Python Inventory

The Python manifests are pinned requirements files, not lockfiles, and they do not carry local license metadata.

| Component | Local manifest | Direct packages from local manifest | Local license metadata |
| --- | --- | --- | --- |
| Backend API | `backend/requirements.txt` | `fastapi==0.115.6`, `uvicorn[standard]==0.34.0`, `asyncpg==0.30.0`, `pydantic==2.10.4` | Unknown in repository files |
| Collector | `collector/requirements.txt` | `asyncpg==0.30.0`, `httpx==0.28.1`, `APScheduler==3.11.0` | Unknown in repository files |

Conservative finding: Python direct dependency names and versions are locally visible, but package license metadata,
transitive dependency inventory, hashes, and wheel/sdist license files require external/manual confirmation or a reviewed
Python lockfile/SBOM generated from the intended environment.

## Container And CI References

Container references found locally:

| Local source | Reference | Local license metadata |
| --- | --- | --- |
| `frontend/Dockerfile` | `docker.io/library/node:22-alpine` build stage | Unknown in repository files |
| `frontend/Dockerfile` | `docker.io/library/nginx:1.27-alpine` runtime stage | Unknown in repository files |
| `backend/Dockerfile` | `docker.io/library/python:3.13-slim-bookworm` | Unknown in repository files |
| `collector/Dockerfile` | `docker.io/library/python:3.13-slim-bookworm` | Unknown in repository files |
| `podman-compose.yml` | `docker.io/timescale/timescaledb:2.17.2-pg16` | Unknown in repository files |
| `podman-compose.cloudflare.yml` | `${CLOUDFLARED_IMAGE:-docker.io/cloudflare/cloudflared:2026.6.1}` | Unknown in repository files |

CI workflow references found locally:

- `actions/checkout@v4`
- `actions/setup-python@v5`
- `actions/setup-node@v4`
- GitHub-hosted `ubuntu-latest`
- Python `3.13`
- Node `22`
- `npx --prefix frontend playwright install --with-deps chromium firefox webkit`

Conservative finding: container image and CI action versions are identifiable from local files, but base image licenses,
OS package licenses, bundled binary licenses, GitHub Action license posture, and browser package licenses were not
confirmed locally. External registry/vendor documentation, image SBOMs, or an approved offline SBOM process are still
needed before making stronger license or compliance claims.

## Open Items

- GitHub-hosted Dependabot execution and first PR evidence are pending until the local config is merged/pushed and
  observed.
- The project repository has no committed `LICENSE` file; do not claim open-source status unless a license is intentionally
  chosen.
- Python dependency license metadata is unknown from repository files.
- Python transitive dependencies are not locked in the repository.
- Container base images, OS packages, Cloudflare tunnel image contents, TimescaleDB image contents, CI actions, and
  Playwright browser/dependency bundles require external/manual confirmation.
- Data-source terms and attribution review remains separate from this dependency inventory. [Production
  Readiness](production-readiness.md) records an accepted limitation for the unpaid/non-commercial pilot only; terms
  review or a paid-plan decision remains pending before commercial claims, paid beta, or broader distribution.
- This pass did not run networked registry checks, install packages, vulnerability scans, secret scans over the full
  repository, or legal review.

## Repeatable Local Commands

These commands use local files only:

```bash
git status --short --branch
git rev-parse HEAD
git tag --list waitlist-accessibility-local-evidence-2026-07-10
sed -n '1,120p' .github/dependabot.yml
rg --files -g 'package.json' -g 'package-lock.json' -g 'requirements*.txt' -g 'pyproject.toml' -g 'poetry.lock' -g 'Pipfile' -g 'Pipfile.lock' -g 'Dockerfile*' -g 'Containerfile*' -g 'podman-compose*.yml'
jq '.packages[""] | {dependencies,devDependencies}' frontend/package-lock.json
jq -r '.packages as $p | $p[""] as $root | ((($root.dependencies // {}) | to_entries[] | {scope:"dependency", name:.key, declared:.value}), (($root.devDependencies // {}) | to_entries[] | {scope:"devDependency", name:.key, declared:.value})) | . as $d | ($p["node_modules/" + $d.name] // {}) as $pkg | [$d.scope, $d.name, $d.declared, ($pkg.version // "MISSING_LOCK_ENTRY"), ($pkg.license // "UNKNOWN_LICENSE")] | @tsv' frontend/package-lock.json
jq -r '[.packages | to_entries[] | select(.key != "") | select((.value.license? // "") == "")] | length' frontend/package-lock.json
rg -n 'FROM |image:' backend collector frontend podman-compose.yml podman-compose.cloudflare.yml
sed -n '1,130p' .github/workflows/ci.yml
```
