# USB Kit for Server Setup

This directory is intended to be run on the new Ubuntu server after installing the system according to `docs/server-msi-cubi5-ubuntu-26.04.md`.

## Contents

- `docs/server-msi-cubi5-ubuntu-26.04.md` - full server setup guide.
- `project/bitcoin-risk-brief/` - project copy without `.env`, `.git`, container data, dependencies, build output, and backups.
- `scripts/` - ordered scripts for finishing setup.

## Run on the Server

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

Run the steps in order:

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

## Redeploy

To update the project from USB:

```bash
cd /mnt/deploy-usb/bitcoin-risk-brief-server-kit
bash scripts/03-deploy-bitcoin-risk-brief.sh
bash scripts/04-enable-bitcoin-risk-service.sh
bash scripts/05-health-check.sh
```

The existing `/srv/projects/bitcoin-risk-brief/.env` is not overwritten.

## Diagnostics

If `04-enable-bitcoin-risk-service.sh` or `05-health-check.sh` fails, collect a report:

```bash
cd /mnt/deploy-usb/bitcoin-risk-brief-server-kit
sudo bash scripts/06-debug-bitcoin-risk-service.sh
```

The script prints a report path like `/tmp/bitcoin-risk-debug-YYYYMMDDTHHMMSSZ.log`. Send the report content without extra manual shortening; secrets from `.env` are masked.
