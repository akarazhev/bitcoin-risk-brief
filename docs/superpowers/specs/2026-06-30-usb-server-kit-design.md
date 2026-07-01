# USB Server Kit Design

> Status: completed in repository, operator copy pending. Last reviewed 2026-06-30. Scripts and README live under
> `server-kit/`; copying to a physical USB volume remains an operator step. Follow-up:
> `2026-07-01-usb-update-install-kit-v2-design.md` defines a planned reproducible packaging and backup-before-update
> flow.

## Goal

Create a complete USB handoff kit for configuring a new MSI Cubi Ubuntu server and deploying `bitcoin-risk-brief` without SSH or port forwarding.

## Scope

The kit must include:

- `docs/server-msi-cubi5-ubuntu-26.04.md`;
- a filtered repository snapshot for deployment;
- ordered scripts for host bootstrap, optional `cloudflared` installation, project deployment, systemd user service setup, and health checks;
- a short English README with the run order.

The kit must not include local `.env`, `.git`, container data, build output, backups, dependency caches, or Python/Node caches.

## Architecture

The source templates live under `server-kit/` in this repository. The final USB layout is staged as `/Volumes/USB/bitcoin-risk-brief-server-kit/`.

Scripts are independent bash entry points so the operator can pause between risky steps:

- `01-bootstrap-host.sh` installs baseline packages, disables SSH if present, creates the `apps` user, configures UFW, unattended upgrades, safe sysctl hardening, and journald limits.
- `02-install-cloudflared-from-usb.sh` installs `cloudflared-linux-amd64.deb` from the USB when available, or downloads it only when explicitly allowed.
- `03-deploy-bitcoin-risk-brief.sh` copies the project to `/srv/projects/bitcoin-risk-brief`, preserves an existing `.env`, and creates a new `.env` with a generated database password when missing.
- `04-enable-bitcoin-risk-service.sh` creates and starts a rootless systemd user service for the `apps` user.
- `05-health-check.sh` checks local app endpoints, service state, Podman containers, and optional public endpoints.

## Safety

The scripts keep the application bound to `127.0.0.1`, do not install or enable SSH, and do not overwrite an existing project `.env`. The deploy script validates that the destination is under `/srv/projects/` before using `rsync --delete`.

## Verification

Before copying to USB:

- run `bash -n` over every kit script;
- run `shellcheck` if installed;
- verify the filtered project copy excludes secret/build/cache paths;
- list the USB kit contents after copying.
