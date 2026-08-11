# CI Image Build Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make CI build the three container images, so that a dependency change which breaks the image fails in a pull request instead of at deploy time.

**Architecture:** One new job in the existing workflow. It builds `backend`, `collector` and `frontend` with the same contexts and build arguments the compose file uses, then makes one cheap runtime assertion per image. Nothing is pushed anywhere.

**Tech Stack:** GitHub Actions, Docker.

## Global Constraints

- **Build only. Never push an image** to any registry, and never log in to one.
- No change to any `Dockerfile`, to `podman-compose.yml`, or to application code. This plan adds a check; it does not alter what is built.
- No new dependency in `backend/requirements.txt`, `collector/requirements.txt`, `frontend/package.json`, or `docs/requirements.txt`.
- The frontend build argument uses the documented public Turnstile test key `1x00000000000000000000AA`, exactly as the existing `frontend-build`, `frontend-smoke` and `compose-validation` jobs already do. It is a placeholder, not a secret.
- Keep the workflow-level `permissions: contents: read`. The new job needs nothing more.

## Why

No CI job builds an image. `compose-validation` runs `docker compose config`, which parses the file and stops. Every Python job pins 3.13 through `actions/setup-python` and never touches a `Dockerfile`.

The consequence is live right now. Dependabot PRs **#21** and **#18** bump the container base image from `python:3.13-slim-bookworm` to `python:3.14-slim-bookworm`, and both show green checks — because nothing in CI exercises the thing they change. `pydantic-core` has no 3.14 wheel at the pinned version and needs a compiler to build from source, which a slim image does not carry. Merging on that green tick would fail at image build time, which is to say at deploy.

The build contexts differ per service and must be copied from `podman-compose.yml` rather than guessed:

| Image | Context | Dockerfile | Build argument |
| --- | --- | --- | --- |
| backend | `./backend` | `Dockerfile` | — |
| collector | `.` (repository root) | `./collector/Dockerfile` | — |
| frontend | `./frontend` | `Dockerfile` | `VITE_TURNSTILE_SITE_KEY` |

The collector's context is the repository root because its `Dockerfile` copies `backend/app/` alongside its own source.

---

### Task 1: Prove the gap is real, then close it

**Files:**
- Modify: `.github/workflows/ci.yml`
- Test: the job itself, plus a local build that demonstrates the failure it catches

**Interfaces:**
- Produces: a job named `image-build`. Task 2 adds that exact name to the branch ruleset.

- [ ] **Step 1: Demonstrate the failure the job is meant to catch**

Before adding anything, prove the claim rather than trusting it. Build the backend image with the base image PR #21 proposes:

```bash
docker build -t brb-backend-314-probe \
  --build-arg IGNORED=1 \
  -f - ./backend <<'EOF'
FROM docker.io/library/python:3.14-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
EOF
```

Record the outcome in your report either way.

**If it fails**, that is the gap this plan closes, and the failure text belongs in the report.

**If it succeeds**, say so plainly — the risk assessment on #21 and #18 was wrong and should be corrected rather than quietly dropped. Continue with the plan regardless; the job is worth having either way.

Clean up: `docker image rm brb-backend-314-probe` if it was created.

- [ ] **Step 2: Build all three images locally on the current base**

```bash
docker build -t brb-backend-check ./backend
docker build -t brb-collector-check -f ./collector/Dockerfile .
docker build -t brb-frontend-check \
  --build-arg VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA ./frontend
```

Expected: all three succeed. If one does not, stop — `main` is broken and that is a bigger finding than this plan.

- [ ] **Step 3: Verify the runtime assertions the job will make**

```bash
docker run --rm brb-backend-check python -c "import app.main; print('backend imports')"
docker run --rm brb-collector-check python -c "import collector.main; print('collector imports')"
docker run --rm --add-host backend:127.0.0.1 brb-frontend-check nginx -t
```

Expected: two `imports` lines and `syntax is ok` / `test is successful` from nginx.

`--add-host` is required, not cosmetic: `nginx.conf` proxies to the compose service name `backend`,
which resolves only inside the compose network. Without it nginx stops at
`host not found in upstream "backend"` and validates nothing. Pointing the name at the loopback lets it
finish resolving and check the rest of the file. Verified that a missing semicolon is still caught.

These three assertions are the reason the job is worth more than a plain build. Installing is not importing: a dependency can resolve, install, and still break at import. And `nginx -t` validates `frontend/nginx.conf`, a file this project edited recently to add the SPA route allowlist — a syntax error there would otherwise surface only when the container refuses to start in production.

Clean up: `docker image rm brb-backend-check brb-collector-check brb-frontend-check`.

- [ ] **Step 4: Add the job**

Append to `.github/workflows/ci.yml`:

```yaml
  image-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build backend image
        run: docker build -t brb-backend:ci ./backend
      - name: Backend imports
        run: docker run --rm brb-backend:ci python -c "import app.main"

      - name: Build collector image
        run: docker build -t brb-collector:ci -f ./collector/Dockerfile .
      - name: Collector imports
        run: docker run --rm brb-collector:ci python -c "import collector.main"

      - name: Build frontend image
        run: |
          docker build -t brb-frontend:ci \
            --build-arg VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA \
            ./frontend
      - name: Frontend nginx config is valid
        run: docker run --rm --add-host backend:127.0.0.1 brb-frontend:ci nginx -t
```

One job with named steps rather than three jobs or a matrix: the step name already attributes a failure, and a single check name is what Task 2 adds to the ruleset. Three parallel jobs would save a couple of minutes and cost three ruleset entries to keep in sync.

No layer caching in this first version. Dependency pull requests — the ones this job exists for — change `requirements.txt` or `package-lock.json` and invalidate the cache anyway, so caching would speed up exactly the runs that were never at risk.

- [ ] **Step 5: Verify the workflow parses and commit**

```bash
python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/ci.yml')); print(list(d['jobs']))"
```

Expected: the job list ends with `image-build`.

```bash
git add .github/workflows/ci.yml
git commit -m "ci: build the container images"
```

---

### Task 2: Make the check required

This is a repository-settings change, performed after Task 1 merges and the job has reported at least once on `main`. It is not test-driven; it is verified by observation.

- [ ] **Step 1: Confirm the job ran green on `main`**

```bash
gh run list --branch main --workflow CI --limit 1 --json databaseId --jq '.[0].databaseId' \
  | xargs -I{} gh run view {} --json jobs \
  --jq '.jobs[] | select(.name=="image-build") | "\(.name): \(.conclusion)"'
```

Expected: `image-build: success`. Do not proceed until it has.

- [ ] **Step 2: Add it to the ruleset**

The `main` ruleset already requires eight checks. Read the current rules, append `image-build` to the `required_status_checks` list, and write them back:

```bash
gh api repos/akarazhev/bitcoin-risk-brief/rulesets --jq '.[] | "\(.id) \(.name)"'
```

Then fetch that ruleset, add `{ "context": "image-build" }` to the `required_status_checks` parameters alongside the existing eight, and `PUT` it back. Do not replace the other rules — `deletion`, `non_fast_forward` and `pull_request` must survive.

- [ ] **Step 3: Confirm**

```bash
gh api repos/akarazhev/bitcoin-risk-brief/rules/branches/main --jq '.[] | .type'
gh api repos/akarazhev/bitcoin-risk-brief/rulesets --jq \
  '.[] | select(.name=="main") | .id' \
  | xargs -I{} gh api repos/akarazhev/bitcoin-risk-brief/rulesets/{} \
  --jq '.rules[] | select(.type=="required_status_checks") | .parameters.required_status_checks[].context'
```

Expected: four rule types, and nine required contexts including `image-build`.

---

## Verification Summary

```bash
./scripts/manage.sh test-python
npm test --prefix frontend
npm run build --prefix frontend
./scripts/manage.sh validate
mkdocs build --strict
```

None of these are affected by this plan — run them to prove that.

## What This Unblocks

Once `image-build` is required, Dependabot PRs #21 and #18 stop being unverifiable. Whatever the probe in Task 1 Step 1 shows, the answer will come from CI rather than from reasoning, and the same protection applies to every future base-image or dependency bump.

## Out Of Scope

- Pushing images to any registry, and any registry authentication.
- Layer caching, image-size budgets, or vulnerability scanning of the built images.
- Running the full stack in CI, or any test that needs a database.
- Deciding what to do about #21 and #18 — this plan makes the decision answerable, it does not make it.
- Any change to a `Dockerfile` or to `podman-compose.yml`.
