# Ubuntu and Cloudflare Tunnel Deployment

This guide covers the intended production-pilot deployment for a local Ubuntu server on a ByFly home or office connection in Belarus. The recommended public ingress is Cloudflare Tunnel, not direct router port forwarding.

## Target Topology

```text
Internet user
  -> Cloudflare DNS / TLS / WAF / rate limiting
  -> Cloudflare Tunnel
  -> Ubuntu server on ByFly
  -> http://127.0.0.1:3001
  -> frontend nginx
  -> backend API
  -> TimescaleDB
```

Cloudflare Tunnel is a good fit for this environment because the server does not need a publicly routable static IP address. `cloudflared` opens outbound-only connections from the Ubuntu host to Cloudflare, while the frontend stays bound to `127.0.0.1`.

## Assumptions

- Ubuntu LTS server with SSH access.
- Podman and `podman-compose` are available on the host.
- The repository is deployed under `/opt/bitcoin-risk-brief`.
- A Cloudflare-managed DNS zone is available for the public hostname, for example `risk.example.com`.
- Either a production CoinMarketCap API key is available for the optional API refresh path, or operators will use the
  documented downloaded CSV refresh path.

## Host Preparation

Install baseline packages:

```bash
sudo apt update
sudo apt install -y git curl ca-certificates ufw podman podman-compose
```

Lock down inbound access. Keep SSH available, but do not expose the app port publicly:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw enable
sudo ufw status verbose
```

If the server uses a different SSH port, allow that port before enabling UFW.

## Application Setup

Prepare the working directory:

```bash
sudo mkdir -p /opt/bitcoin-risk-brief
sudo chown "$USER:$USER" /opt/bitcoin-risk-brief
cd /opt/bitcoin-risk-brief
```

Clone or copy the repository into this directory, then create the production environment file:

```bash
cp .env.production.example .env
```

Minimum production values to change:

```env
APP_ENV=production
DB_PASSWORD=replace-with-a-long-random-password
FRONTEND_BIND_IP=127.0.0.1
FRONTEND_PORT=3001
CORS_ORIGINS=https://risk.example.com
COINMARKETCAP_API_KEY=
DATA_FRESHNESS_MAX_AGE_DAYS=2
WAITLIST_RATE_LIMIT_PER_HOUR=20
```

Set `COINMARKETCAP_API_KEY` only when using the optional API refresh path. Without a paid API account, leave it empty and
refresh the canonical BTC CSV through the documented downloaded CSV workflow.

Generate a database password on the server:

```bash
openssl rand -base64 48
```

Start and verify the stack:

```bash
./scripts/manage.sh validate
./scripts/manage.sh start
./scripts/manage.sh migrate
./scripts/manage.sh run-now
curl -fsS http://127.0.0.1:3001/api/health
curl -fsS http://127.0.0.1:3001/api/readiness
```

`/api/readiness` should return HTTP 200 before the public hostname is opened.

If `COINMARKETCAP_API_KEY` is empty and the canonical CSV is stale, first try the automatic public CoinMarketCap
download before the readiness check:

```bash
EXPECTED_END_DATE="$(date -u -d 'yesterday' +%F)"
./scripts/manage.sh download-cmc-csv "${EXPECTED_END_DATE}"
curl -fsS http://127.0.0.1:3001/api/readiness
```

If the public endpoint automation is unavailable, download the Bitcoin historical CSV from CoinMarketCap, stage it under
`collector/btc-csv/incoming/`, and import it manually:

```bash
EXPECTED_END_DATE="$(date -u -d 'yesterday' +%F)"
mkdir -p collector/btc-csv/incoming
cp ~/Downloads/bitcoin-historical-data.csv collector/btc-csv/incoming/
./scripts/manage.sh import-cmc-csv collector/btc-csv/incoming/bitcoin-historical-data.csv "${EXPECTED_END_DATE}"
curl -fsS http://127.0.0.1:3001/api/readiness
```

## Cloudflare Tunnel Option A: Host Service

This is the recommended setup for a single local server. `cloudflared` runs as a host-level systemd service and forwards traffic to the frontend port bound on localhost.

In the Cloudflare dashboard:

1. Open Zero Trust or Cloudflare One.
2. Create a remotely-managed Tunnel.
3. Add a public hostname such as `risk.example.com`.
4. Set the service URL to `http://127.0.0.1:3001`.
5. Copy the generated Linux service install command.

On Ubuntu, install the service with the tunnel token from Cloudflare:

```bash
sudo cloudflared service install <TUNNEL_TOKEN>
sudo systemctl status cloudflared
```

After DNS propagates, verify the public origin:

```bash
curl -fsS https://risk.example.com/api/health
curl -fsS https://risk.example.com/api/readiness
```

If the public health check works but readiness fails, troubleshoot the application data pipeline first, not Cloudflare.

## Cloudflare Tunnel Option B: Compose-Managed Connector

Use this option if you want `cloudflared` to be managed together with the application containers. The overlay file is `podman-compose.cloudflare.yml`.

Set these values in `.env`:

```env
CLOUDFLARE_TUNNEL_TOKEN=replace-with-cloudflare-tunnel-token
CLOUDFLARED_IMAGE=cloudflare/cloudflared:2026.6.1
```

In the Cloudflare dashboard, set the public hostname service URL to:

```text
http://frontend:3000
```

Start with both compose files:

```bash
podman-compose -f podman-compose.yml -f podman-compose.cloudflare.yml up -d --build
podman-compose -f podman-compose.yml -f podman-compose.cloudflare.yml logs -f cloudflared
```

Validate public endpoints:

```bash
curl -fsS https://risk.example.com/api/health
curl -fsS https://risk.example.com/api/readiness
```

The compose-managed option stores the tunnel token in `.env` and passes it to the container as `TUNNEL_TOKEN`; keep `.env` private, never commit it, and rotate the token if it is exposed.

## Cloudflare Edge Settings

Recommended initial settings:

- Public HTTPS at the Cloudflare edge: enabled for the hostname.
- Local service URL: keep `http://127.0.0.1:3001` for host-service tunnel, or `http://frontend:3000` for compose-managed tunnel.
- Always Use HTTPS: enabled.
- HTTP Strict Transport Security: enable after the hostname is confirmed stable.
- WAF managed rules: enabled.
- Rate limiting: start with conservative limits on `/api/waitlist` and `/api/*`.
- Bot/spam controls: start in a low-friction mode and tighten if waitlist spam or abusive traffic appears.
- Cache: do not cache API responses unless explicit cache headers and invalidation behavior are added.

## Backups

Run a backup after the first successful production import:

```bash
./scripts/backup.sh
```

The backup contains a compressed PostgreSQL custom-format dump and the canonical BTC CSV. Store a copy off the server; a backup that only lives on the same ByFly machine does not protect against disk failure. TimescaleDB may print circular foreign-key warnings during backup; treat them as informational only when `scripts/backup.sh` exits with code 0.

Example daily cron:

```cron
0 3 * * * cd /opt/bitcoin-risk-brief && BACKUP_RETENTION_DAYS=30 ./scripts/backup.sh >> /var/log/bitcoin-risk-brief-backup.log 2>&1
```

## Restore Drill

Test restores on a separate staging copy, not on the live production directory.

For a clean database container:

```bash
podman-compose -f podman-compose.yml exec -T timescaledb pg_restore --clean --if-exists --no-owner --no-privileges -U postgres -d bitcoin_risk_brief < backups/<timestamp>/postgres_<timestamp>.dump
cp backups/<timestamp>/btc_usd_daily_<timestamp>.csv collector/btc-csv/btc_usd_daily.csv
./scripts/manage.sh run-now
curl -fsS http://127.0.0.1:3001/api/readiness
```

Do not restore a dump into a live database with active user traffic unless you have taken the app offline and confirmed the target state.

## Monitoring

Minimum checks:

- Public uptime check: `https://risk.example.com/api/health`.
- Production gate check: `https://risk.example.com/api/readiness`.
- Daily collector logs after the configured UTC schedule.
- Backup log freshness and backup file age.
- Cloudflare Tunnel connector health in the Cloudflare dashboard.

Alert immediately when `/api/readiness` is non-200 after the daily collector window.

## Update Procedure

```bash
cd /opt/bitcoin-risk-brief
git pull --ff-only
./scripts/manage.sh validate
./scripts/manage.sh start
./scripts/manage.sh migrate
./scripts/manage.sh run-now
curl -fsS http://127.0.0.1:3001/api/readiness
curl -fsS https://risk.example.com/api/readiness
```

Run `./scripts/backup.sh` before updates that include migrations.

## Rollback

For code-only changes:

```bash
git log --oneline -5
git checkout <previous-good-commit>
./scripts/manage.sh start
curl -fsS http://127.0.0.1:3001/api/readiness
```

For database-impacting changes, restore only from a verified backup and only after taking the app offline.
