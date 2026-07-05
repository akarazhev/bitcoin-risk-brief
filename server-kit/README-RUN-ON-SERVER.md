# USB Kit for Server Setup

This directory is intended to be run on the new Ubuntu server after installing the system according to `docs/server-msi-cubi5-ubuntu-26.04.md`.

## Prepare The USB On The Workstation

From the repository checkout on the workstation:

```bash
cd /path/to/bitcoin-risk-brief
bash server-kit/prepare-usb-kit.sh /Volumes/USB
```

The command creates `/Volumes/USB/bitcoin-risk-brief-server-kit`. It is safe to rerun because it replaces only that kit
directory, not the USB mount itself.

The kit contains:

- deployment docs;
- ordered server scripts;
- a filtered `project/bitcoin-risk-brief/` snapshot;
- `manifest.txt` with source revision and copied file categories;
- `SHA256SUMS` for kit integrity checks.

The kit does not contain local `.env`, `.git`, backups, dependency caches, build output, browser artifacts, container
images, or an offline package mirror.

## Contents

- `docs/server-msi-cubi5-ubuntu-26.04.md` - full server setup guide.
- `project/bitcoin-risk-brief/` - project copy without `.env`, `.git`, container data, dependencies, build output, and backups.
- `scripts/` - ordered scripts for finishing setup.
- `manifest.txt` - package timestamp, source commit, source path, kit path, copied docs, copied scripts, and project snapshot path.
- `SHA256SUMS` - checksums for every regular file in the kit.

Expected script list:

- `scripts/01-bootstrap-host.sh`
- `scripts/02-install-cloudflared-from-usb.sh`
- `scripts/03-deploy-bitcoin-risk-brief.sh`
- `scripts/04-enable-bitcoin-risk-service.sh`
- `scripts/05-health-check.sh`
- `scripts/06-debug-bitcoin-risk-service.sh`
- `scripts/07-update-bitcoin-risk-brief-from-usb.sh`

## Mount The USB On The Server

If the USB drive is not mounted automatically:

```bash
lsblk -f
sudo mkdir -p /mnt/deploy-usb
sudo mount /dev/sdX1 /mnt/deploy-usb
```

Replace `/dev/sdX1` with the actual device from `lsblk -f`.

Go to the kit:

```bash
cd /mnt/deploy-usb/bitcoin-risk-brief-server-kit
```

## Fresh Install

Run the fresh install steps in order:

```bash
bash scripts/01-bootstrap-host.sh
bash scripts/02-install-cloudflared-from-usb.sh
bash scripts/03-deploy-bitcoin-risk-brief.sh
sudoedit /srv/projects/bitcoin-risk-brief/.env
bash scripts/04-enable-bitcoin-risk-service.sh
bash scripts/05-health-check.sh
```

`03-deploy-bitcoin-risk-brief.sh` creates `.env` only when it does not already exist. The script generates a random `DB_PASSWORD` and updates `DATABASE_URL`. Before starting the service, check at least:

```env
CORS_ORIGINS=https://your-production-domain.example
COINMARKETCAP_API_KEY=
```

If there is no domain yet, leave the production hostname empty or temporary and use Quick Tunnel only for a short check:

```bash
cloudflared tunnel --url http://127.0.0.1:3001
```

For production after buying a domain, use the service install command from Cloudflare Zero Trust:

```bash
sudo cloudflared service install 'PASTE_TUNNEL_TOKEN_HERE'
sudo systemctl status cloudflared
```

## Cloudflared Through USB

If the server should not download `cloudflared`, put `cloudflared-linux-amd64.deb` in the kit root or in `packages/`, then run:

```bash
bash scripts/02-install-cloudflared-from-usb.sh
```

If direct download from the server is acceptable:

```bash
ALLOW_DOWNLOAD=true bash scripts/02-install-cloudflared-from-usb.sh
```

## Update Existing Deployment

Use the update wrapper instead of rerunning the raw deploy script:

```bash
cd /mnt/deploy-usb/bitcoin-risk-brief-server-kit
bash scripts/07-update-bitcoin-risk-brief-from-usb.sh
```

For a public readiness check after Cloudflare Tunnel is configured:

```bash
PUBLIC_URL=https://bitcoinriskbrief.minihub.app bash scripts/07-update-bitcoin-risk-brief-from-usb.sh
```

The update wrapper requires an existing `/srv/projects/bitcoin-risk-brief/.env`, runs `./scripts/backup.sh` from the
currently deployed project before copying new code, verifies the backup checksums, copies the verified backup to
`BACKUP_COPY_DEST` or the USB kit default `backups-from-server/`, verifies that copied backup, deploys the USB project
snapshot, recreates/restarts the user service, and runs local health/readiness plus optional public readiness checks.

`03-deploy-bitcoin-risk-brief.sh` preserves the existing production `.env`; the update wrapper refuses to continue if
that file is missing.

## Diagnostics

If `04-enable-bitcoin-risk-service.sh` or `05-health-check.sh` fails, collect a report:

```bash
cd /mnt/deploy-usb/bitcoin-risk-brief-server-kit
sudo bash scripts/06-debug-bitcoin-risk-service.sh
```

The script prints a report path like `/tmp/bitcoin-risk-debug-YYYYMMDDTHHMMSSZ.log`. Send the report content without extra manual shortening; secrets from `.env` are masked.
