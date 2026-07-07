# USB One-Command Deploy Design

## Context

The USB kit already supports a strict update wrapper that creates and verifies a PostgreSQL backup before copying code.
That is safer for a fully managed production update, but it is a poor default when the operator is physically at the
server without remote access: `pg_dump` can appear silent or stuck and block the whole deploy before any code is copied.

## Decision

Add a top-level `deploy-from-usb.sh` entrypoint to the packaged USB kit. The default path verifies the kit checksums,
deploys the project snapshot, preserves the existing production `.env` and database volume, restarts the user service,
and runs local plus optional public health checks. It does not run `pg_dump`.

Keep the existing backup-gated update wrapper available as an explicit safe mode through:

```bash
bash deploy-from-usb.sh --with-backup https://bitcoinriskbrief.minihub.app
```

## Operator Flow

Workstation:

```bash
bash server-kit/prepare-usb-kit.sh /Volumes/USB
```

Server:

```bash
cd /mnt/deploy-usb/bitcoin-risk-brief-server-kit
bash deploy-from-usb.sh https://bitcoinriskbrief.minihub.app
```

## Requirements

- The packaged kit includes executable `deploy-from-usb.sh` at the kit root.
- `deploy-from-usb.sh` verifies `SHA256SUMS` before deploying.
- The default path calls the existing deploy, service, restart, and health-check scripts in order.
- The default path must not call `scripts/backup.sh`.
- The existing backup-gated wrapper remains available and unchanged for explicit use.
- Documentation should present the no-backup path as the normal physical-server USB deploy path.

## Risk

Skipping a database dump before deploy means rollback relies on the latest existing backup or unchanged database volume.
That tradeoff is intentional for the default physical USB deploy path; the explicit `--with-backup` mode remains the
safer option when the operator can tolerate a slower backup step.
