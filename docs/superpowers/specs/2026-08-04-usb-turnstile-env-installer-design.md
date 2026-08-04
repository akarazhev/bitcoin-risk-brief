# USB Turnstile Environment Installer Design

**Date:** 2026-08-04
**Status:** Approved for implementation planning

## Objective

Add one operator-run script to the Bitcoin Risk Brief USB server kit that installs the three production Turnstile
assignments into the existing server environment file. The script changes configuration only; it does not deploy,
restart, migrate, or run application health checks.

## Operator Interface

The script is shipped as `server-kit/scripts/08-install-turnstile-env-from-usb.sh` and is run from the mounted USB kit:

```bash
sudo bash scripts/08-install-turnstile-env-from-usb.sh
```

It locates `bitcoin-risk-brief-turnstile.env` in the USB root relative to its own installed location. The production
target is `/srv/projects/bitcoin-risk-brief/.env`, and all target-file mutation runs as the existing `apps` user.

## Data Flow

1. Require root execution, the `apps` account, the existing production `.env`, the USB fragment, and the bundled
   no-output Turnstile preflight validator.
2. Validate the USB fragment before preparing any target change.
3. As `apps`, create a temporary file beside the production `.env`.
4. Copy every existing assignment except `VITE_TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET`, and `TURNSTILE_HOSTNAMES` into
   the temporary file.
5. Append the three validated assignments from the USB fragment with `cat`.
6. Validate the complete temporary environment file, set mode `0600`, and atomically replace the original `.env`.
7. Print a success message containing paths and key names only, never values.

Removing the three existing assignments before appending prevents duplicate-key failures when the target came from
`.env.production.example` or was configured previously.

## Failure And Security Behavior

- Any missing file, account, malformed fragment, duplicate fragment key, placeholder, Cloudflare dummy credential, or
  non-production hostname fails before the production `.env` is replaced.
- A temporary file is removed on failure.
- The Turnstile secret and site key are never printed, passed as command-line arguments, or committed.
- The plaintext fragment remains outside the checksummed `bitcoin-risk-brief-server-kit` directory. This preserves the
  package's no-secret guarantee while honoring the operator's explicit decision to carry the separate fragment on a
  physically controlled USB drive.
- The script does not copy the Cloudflare API token.

## Testing

Focused server-kit tests must prove that the script:

- is included in prepared USB kits;
- finds the fragment relative to the USB root rather than assuming a mount path;
- validates before target mutation;
- runs the merge as `apps`;
- removes only the three Turnstile assignments, appends the fragment, applies mode `0600`, and atomically replaces the
  target;
- does not invoke deployment, backup, restart, migration, or health-check commands;
- never prints credential values.

Run the complete server-kit unit-test suite, shell syntax validation, USB package preparation, package checksum
verification, and a final secret-exclusion check before copying the refreshed kit to the physical USB drive.

## Success Criteria

- One documented command safely updates the existing production `.env` from the attached USB drive.
- The resulting file has exactly one effective value for each required Turnstile key and retains every unrelated
  environment assignment.
- All changes are performed as `apps`, the final file is mode `0600`, and invalid input leaves the original unchanged.
- No application deployment or secret output occurs.
