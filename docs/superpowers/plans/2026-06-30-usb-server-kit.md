# USB Server Kit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete USB server setup and deployment kit for `bitcoin-risk-brief`.

**Architecture:** Keep reusable kit templates in `server-kit/`, copy a filtered repo snapshot to `/Volumes/USB/bitcoin-risk-brief-server-kit/project/bitcoin-risk-brief`, and place server-run scripts under `/Volumes/USB/bitcoin-risk-brief-server-kit/scripts`. Scripts are ordered and idempotent where practical.

**Tech Stack:** Bash, Ubuntu `apt`, UFW, Podman, podman-compose, systemd user services, rsync.

---

### Task 1: Add Kit Templates

**Files:**
- Create: `server-kit/README-RUN-ON-SERVER.md`
- Create: `server-kit/scripts/01-bootstrap-host.sh`
- Create: `server-kit/scripts/02-install-cloudflared-from-usb.sh`
- Create: `server-kit/scripts/03-deploy-bitcoin-risk-brief.sh`
- Create: `server-kit/scripts/04-enable-bitcoin-risk-service.sh`
- Create: `server-kit/scripts/05-health-check.sh`

- [ ] **Step 1: Add the README and scripts**

Create the files listed above with the final implementation committed to the repository working tree.

- [ ] **Step 2: Check script syntax**

Run:

```bash
find server-kit/scripts -type f -name '*.sh' -print -exec bash -n {} \;
```

Expected: each script path is printed and `bash -n` exits with code 0.

### Task 2: Prepare USB Kit

**Files:**
- Copy: `docs/server-msi-cubi5-ubuntu-26.04.md`
- Copy: `server-kit/README-RUN-ON-SERVER.md`
- Copy: `server-kit/scripts/*.sh`
- Copy: filtered project snapshot to `/Volumes/USB/bitcoin-risk-brief-server-kit/project/bitcoin-risk-brief`

- [ ] **Step 1: Create target directories**

Run:

```bash
mkdir -p /Volumes/USB/bitcoin-risk-brief-server-kit/{docs,scripts,project}
```

Expected: target directories exist on the USB volume.

- [ ] **Step 2: Copy docs and scripts**

Run:

```bash
rsync -a docs/server-msi-cubi5-ubuntu-26.04.md /Volumes/USB/bitcoin-risk-brief-server-kit/docs/
rsync -a server-kit/README-RUN-ON-SERVER.md /Volumes/USB/bitcoin-risk-brief-server-kit/
rsync -a server-kit/scripts/ /Volumes/USB/bitcoin-risk-brief-server-kit/scripts/
chmod +x /Volumes/USB/bitcoin-risk-brief-server-kit/scripts/*.sh
```

Expected: README, doc, and executable scripts exist on the USB.

- [ ] **Step 3: Copy filtered project snapshot**

Run `rsync` from the repo root with excludes for `.git`, `.env`, `node_modules`, `dist`, `data`, `backups`, Python caches, test caches, logs, and local IDE files.

Expected: `/Volumes/USB/bitcoin-risk-brief-server-kit/project/bitcoin-risk-brief` contains the deployable source and `.env.production.example`, but no local `.env`.

### Task 3: Verify USB Contents

**Files:**
- Inspect: `/Volumes/USB/bitcoin-risk-brief-server-kit`

- [ ] **Step 1: Verify no local secret file was copied**

Run:

```bash
find /Volumes/USB/bitcoin-risk-brief-server-kit/project/bitcoin-risk-brief -maxdepth 2 -name '.env' -print
```

Expected: no output.

- [ ] **Step 2: Verify key files exist**

Run:

```bash
test -f /Volumes/USB/bitcoin-risk-brief-server-kit/docs/server-msi-cubi5-ubuntu-26.04.md
test -f /Volumes/USB/bitcoin-risk-brief-server-kit/project/bitcoin-risk-brief/podman-compose.yml
test -x /Volumes/USB/bitcoin-risk-brief-server-kit/scripts/01-bootstrap-host.sh
test -x /Volumes/USB/bitcoin-risk-brief-server-kit/scripts/05-health-check.sh
```

Expected: all `test` commands exit with code 0.
