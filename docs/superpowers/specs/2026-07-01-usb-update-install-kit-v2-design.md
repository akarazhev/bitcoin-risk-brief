# USB Update And Install Kit V2 Design

> Status: future-facing operational hardening. Last reviewed 2026-07-01. This extends the completed USB server-kit
> templates under `server-kit/` by making USB preparation reproducible and by adding an explicit backup-before-update
> gate.

## Goal

Make production updates and fresh server installs safer when the operator deploys through a USB drive instead of SSH or a
remote Git workflow.

The v2 kit should let the operator prepare a deployment USB from the workstation with one command, then use the USB on
the server for either:

- a fresh install after the host is bootstrapped; or
- an update to an existing `bitcoin-risk-brief` deployment after a verified backup is created.

## Current Gap

The repository already contains server-run scripts for bootstrap, optional `cloudflared` install, project deployment,
systemd user service enablement, health checks, and debug reports. The missing part is the workstation-side packaging
workflow. Today the operator must manually copy docs, scripts, and a filtered project snapshot to the USB drive.

Manual copying is error-prone because it can:

- include local `.env`, `.git`, backups, dependency caches, or build output;
- miss a required doc or script;
- deploy an unclear project revision;
- skip backup before an update.

## Scope

The v2 kit is a reproducible release/update kit, not a fully offline artifact.

It should place only these categories on the USB drive:

- a filtered project snapshot;
- `server-kit/` scripts;
- current deployment, operations, and server setup docs;
- a manifest with project revision, timestamp, source path, and copied file categories;
- checksums for integrity verification.

The existing `02-install-cloudflared-from-usb.sh` behavior remains acceptable: use a `.deb` from USB when present, or
download `cloudflared` on the server when `ALLOW_DOWNLOAD=true` is set. Container images and application builds are
created on the server.

## Non-Goals

This design does not include:

- container images on the USB drive;
- full apt, npm, Python, or Podman dependency mirrors;
- offline Ubuntu package installation;
- production secrets on the USB drive;
- automatic restore into a live production database.

Full offline deployment can be revisited only if the server must operate without internet access during setup.

## Workstation Packaging Flow

A future workstation-side script should prepare the USB kit from the repository root.

Expected behavior:

- accept a target mount path such as `/Volumes/USB` or `/media/$USER/DEPLOY`;
- create a deterministic kit directory such as `bitcoin-risk-brief-server-kit`;
- copy `server-kit/README-RUN-ON-SERVER.md`, `server-kit/scripts/`, and relevant docs;
- copy the project snapshot under `project/bitcoin-risk-brief`;
- exclude `.env`, `.git`, `backups`, database volumes, dependency directories, frontend build output, caches, logs, and
  local editor files;
- mark server-run scripts executable;
- write `manifest.txt`;
- write `SHA256SUMS`;
- fail if a local `.env` or obvious secret file appears in the staged project snapshot.

The packaging command should not require secrets and should be safe to run repeatedly against the same USB directory.

## Server Update Flow

For an existing production host, the server-side flow should be:

1. Mount the USB drive.
2. Run a backup from the current deployed project before copying new code.
3. Copy or verify the latest backup to off-server storage, preferably the same USB drive or another removable drive.
4. Deploy the project snapshot from USB.
5. Recreate or restart the systemd user service.
6. Run local health and readiness checks.
7. Run public readiness checks when the Cloudflare Tunnel is configured.

Backup is a gate for updates that may affect the database, migrations, data pipeline, or production configuration. A
code-only update can still use the same gate because the cost is low and the rollback story is clearer.

## Fresh Install Flow

For a new server, the existing ordered server scripts remain the base flow:

1. `01-bootstrap-host.sh`
2. `02-install-cloudflared-from-usb.sh` or `ALLOW_DOWNLOAD=true ...`
3. `03-deploy-bitcoin-risk-brief.sh`
4. edit `/srv/projects/bitcoin-risk-brief/.env`
5. `04-enable-bitcoin-risk-service.sh`
6. `05-health-check.sh`

The v2 packaging flow makes this install path less manual by ensuring the USB contains the expected docs, scripts, and
project snapshot before the operator touches the server.

## Safety Rules

- Never copy local `.env` to the USB.
- Never overwrite an existing production `.env` during deploy.
- Keep deployment under `/srv/projects/bitcoin-risk-brief` unless the operator explicitly overrides and validates the
  path.
- Require backup before update promotion.
- Keep backup artifacts outside the project snapshot copied from the workstation.
- Treat checksums and manifest as operator evidence, not as a secret or trust boundary.

## Verification

Before using a v2 kit for production:

- run shell syntax checks for every `server-kit/scripts/*.sh`;
- run `python3 -m unittest discover -s server-kit/tests -v` after script changes;
- verify that the staged project snapshot contains no `.env` and no `.git`;
- verify the manifest and checksums are present;
- run the existing health check script after deployment;
- confirm `/api/readiness` locally and through the public hostname when available.

## Phase Fit

This belongs in the production operations track before or alongside the next production deployment. It is closest to
Phase 6 because it improves deployment mechanics, and it also supports Phase 7 because updates should create a backup
before promotion.

It should not block product experiments or risk methodology research unless a manual USB deploy is the only practical
way to update the production host.
