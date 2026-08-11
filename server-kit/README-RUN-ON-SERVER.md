# USB Kit for Server Setup

This directory is intended to be run on the new Ubuntu server after installing the system according to
`docs/operations/server-msi-cubi5-ubuntu-26.04.md`.

## Prepare The USB On The Workstation

From the repository checkout on the workstation:

```bash
cd /path/to/bitcoin-risk-brief
bash server-kit/prepare-usb-kit.sh /Volumes/USB
```

The command creates `/Volumes/USB/bitcoin-risk-brief-server-kit`. It is safe to rerun because it replaces only that kit
directory, not the USB mount itself.
Run this after checking out or committing the exact version you intend to deploy. Before ejecting the USB, compare the
kit manifest with the intended release commit:

```bash
git rev-parse HEAD
cat /Volumes/USB/bitcoin-risk-brief-server-kit/manifest.txt
cd /Volumes/USB/bitcoin-risk-brief-server-kit
shasum -a 256 -c SHA256SUMS
```

The manifest `source_commit` must match the release commit you mean to install. If it does not, return to the repository
checkout, select the correct commit, and rerun `bash server-kit/prepare-usb-kit.sh /Volumes/USB`.

The kit contains:

- deployment docs;
- `deploy-from-usb.sh` as the default one-command deploy entrypoint;
- ordered server scripts;
- a filtered `project/bitcoin-risk-brief/` snapshot;
- `manifest.txt` with source revision and copied file categories;
- `SHA256SUMS` for kit integrity checks.

The kit does not contain local `.env`, `.git`, backups, dependency caches, build output, browser artifacts, container
images, or an offline package mirror.

## Contents

- `docs/operations/server-msi-cubi5-ubuntu-26.04.md` - full server setup guide.
- `deploy-from-usb.sh` - default server entrypoint for checksum verification, deploy, restart, and health checks.
- `project/bitcoin-risk-brief/` - project copy without `.env`, `.git`, container data, dependencies, build output, and backups.
- `scripts/` - ordered scripts for finishing setup.
- `manifest.txt` - package timestamp, source commit, source path, kit path, entrypoints, copied docs, copied scripts, and project snapshot path.
- `SHA256SUMS` - checksums for every regular file in the kit.

Expected script list:

- `deploy-from-usb.sh`
- `scripts/01-bootstrap-host.sh`
- `scripts/02-install-cloudflared-from-usb.sh`
- `scripts/03-deploy-bitcoin-risk-brief.sh`
- `scripts/04-enable-bitcoin-risk-service.sh`
- `scripts/05-health-check.sh`
- `scripts/06-debug-bitcoin-risk-service.sh`
- `scripts/07-update-bitcoin-risk-brief-from-usb.sh`
- `scripts/08-install-turnstile-env-from-usb.sh`
- `scripts/turnstile-env-preflight.py`
- `scripts/09-install-telegram-env-from-usb.sh`
- `scripts/telegram-env-preflight.py`

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
sudo install -d -o apps -g apps -m 750 /srv/projects/bitcoin-risk-brief
sudo install -o apps -g apps -m 600 project/bitcoin-risk-brief/.env.production.example /srv/projects/bitcoin-risk-brief/.env
sudo bash scripts/08-install-turnstile-env-from-usb.sh
sudo bash scripts/09-install-telegram-env-from-usb.sh
sudoedit /srv/projects/bitcoin-risk-brief/.env
bash scripts/03-deploy-bitcoin-risk-brief.sh
bash scripts/04-enable-bitcoin-risk-service.sh
bash scripts/05-health-check.sh
```

`08-install-turnstile-env-from-usb.sh` only replaces `VITE_TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET`, and
`TURNSTILE_HOSTNAMES` in the existing production `.env`; it does not deploy or restart the application. It expects the
separate `bitcoin-risk-brief-turnstile.env` file beside the `bitcoin-risk-brief-server-kit` directory in the USB root.

`09-install-telegram-env-from-usb.sh` only replaces `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHANNEL_ID` in the existing
production `.env`; it does not deploy or restart the application. It expects the separate
`bitcoin-risk-brief-telegram.env` file beside the `bitcoin-risk-brief-server-kit` directory in the USB root:

```env
TELEGRAM_BOT_TOKEN=<real-telegram-bot-token>
TELEGRAM_CHANNEL_ID=@bitcoinriskbrief
```

Before running `03-deploy-bitcoin-risk-brief.sh`, those commands create the production `.env` from the placeholder-only
template already in the USB project snapshot. The installers add the Turnstile and Telegram values; use `sudoedit` to fill in the
remaining production values below. The deploy script validates the Turnstile values without printing them, before it
copies the project, builds, or restarts anything:

```env
CORS_ORIGINS=https://your-production-domain.example
COINMARKETCAP_API_KEY=
```

Set `VITE_TURNSTILE_SITE_KEY` to the public sitekey in the operator-controlled widget record and
`TURNSTILE_SECRET` to its matching private secret. Set `TURNSTILE_HOSTNAMES` exactly to
`bitcoinriskbrief.minihub.app`; do not add local or test hostnames. The site key and secret must be real production
values, not Cloudflare test credentials or example placeholders.

Set `TELEGRAM_BOT_TOKEN` only through the operator-controlled fragment or directly in the server `.env`. Keep it out of
Git, docs, shell history, and the checksummed project snapshot. Leave it empty to disable channel publication. Set
`TELEGRAM_CHANNEL_ID` to `@bitcoinriskbrief`; the installer rejects other targets to avoid posting to the wrong channel.

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

For production updates, prefer the backup-gated path so the database and canonical BTC CSV are backed up and verified
before the project snapshot is replaced.

1. Mount the USB if Ubuntu did not mount it automatically:

```bash
lsblk -f
sudo mkdir -p /mnt/deploy-usb
sudo mount /dev/sdX1 /mnt/deploy-usb
```

Replace `/dev/sdX1` with the actual USB partition from `lsblk -f`.

2. Go to the kit and confirm the package is the intended version:

```bash
cd /mnt/deploy-usb/bitcoin-risk-brief-server-kit
cat manifest.txt
sha256sum -c SHA256SUMS
```

Check that `source_commit` in `manifest.txt` matches the release commit you intended to deploy.

3. Confirm the existing production environment file is present:

```bash
sudo test -f /srv/projects/bitcoin-risk-brief/.env
```

Before the backup-gated update, set the same three Turnstile values in the existing `.env`: a real production
`VITE_TURNSTILE_SITE_KEY`, its matching `TURNSTILE_SECRET`, and
`TURNSTILE_HOSTNAMES` exactly to `bitcoinriskbrief.minihub.app`. If the deployed collector should publish daily channel
posts, put `bitcoin-risk-brief-telegram.env` beside the kit and run:

```bash
sudo bash scripts/09-install-telegram-env-from-usb.sh
```

Leave `TELEGRAM_BOT_TOKEN` empty to keep publication disabled. The update runs the Turnstile no-output preflight before
any backup, project copy, build, or restart work.

4. Run the backup-gated update:

```bash
bash deploy-from-usb.sh --with-backup https://bitcoinriskbrief.minihub.app
```

That command verifies the USB kit, creates a backup, verifies backup checksums, copies the verified backup to
`BACKUP_COPY_DEST` or the USB kit default `backups-from-server/`, verifies the copied backup, deploys the project
snapshot while preserving production `.env` and the database volume, restarts the user service, runs migrations, and
checks local and public health/readiness.

If the PostgreSQL dump is legitimately slow, rerun with a larger timeout:

```bash
BACKUP_DUMP_TIMEOUT_SECONDS=900 bash deploy-from-usb.sh --with-backup https://bitcoinriskbrief.minihub.app
```

Use the top-level deploy script without `--with-backup` only when you intentionally want the faster no-database-backup
path:

```bash
cd /mnt/deploy-usb/bitcoin-risk-brief-server-kit
bash deploy-from-usb.sh
```

For a public readiness check after Cloudflare Tunnel is configured:

```bash
bash deploy-from-usb.sh https://bitcoinriskbrief.minihub.app
```

The default path verifies `SHA256SUMS`, deploys the USB project snapshot, preserves the existing production `.env` and
database volume, recreates/restarts the user service, and runs local health/readiness plus optional public readiness
checks. It does not run `pg_dump`.

In backup-gated mode, the backup wrapper runs from the USB project snapshot while the deployed project remains the
working directory. The copy step intentionally does not preserve POSIX owner, group, or permission bits because common
USB filesystems such as FAT and exFAT do not support them; backup integrity is verified with `SHA256SUMS`.

## Diagnostics

If `04-enable-bitcoin-risk-service.sh` or `05-health-check.sh` fails, collect a report:

```bash
cd /mnt/deploy-usb/bitcoin-risk-brief-server-kit
sudo bash scripts/06-debug-bitcoin-risk-service.sh
```

The script prints a report path like `/tmp/bitcoin-risk-debug-YYYYMMDDTHHMMSSZ.log`. Send the report content without extra manual shortening; secrets from `.env` are masked.
