# MSI Cubi 5 12M Home Server Setup with Ubuntu 26.04 LTS

> **Operational log.** These entries record what was verified and when. They are not claims about product capability.

This document describes installation and initial hardening for an MSI Cubi 5 12M with 32 GB DDR4 and a 1 TB NVMe drive running Ubuntu Server 26.04 LTS. The goal is a local server for Podman Compose projects published through Cloudflare Tunnel from a ByFly home or office connection in Belarus.

Default approach:

- inbound traffic is closed on the router and on the server;
- router port forwarding is not used;
- OpenSSH server is not installed and remote SSH is not used;
- projects are deployed physically through a USB drive;
- Cloudflare Tunnel runs as an outbound connection from the server;
- before buying a domain, only temporary Cloudflare Quick Tunnel is used.

## 1. Important Limitations

Cloudflare Tunnel without your own domain is suitable only for tests. TryCloudflare/Quick Tunnel issues a random URL like `https://*.trycloudflare.com`; Cloudflare documents this mode for development and testing, not for production. After buying a domain, add the domain to Cloudflare DNS and create a normal remotely-managed tunnel with a public hostname.

Topology before buying a domain:

```text
User
  -> random *.trycloudflare.com URL
  -> Cloudflare Quick Tunnel
  -> outbound cloudflared connection from MSI Cubi
  -> http://127.0.0.1:<project-port>
```

Topology after buying a domain:

```text
User
  -> https://project.example.com
  -> Cloudflare DNS / TLS / WAF / rate limiting
  -> Cloudflare Tunnel
  -> outbound cloudflared connection from MSI Cubi
  -> http://127.0.0.1:<project-port>
  -> Podman Compose containers
```

ByFly, dynamic IP addresses, and possible CG-NAT do not block this design because the server opens the outbound connection to Cloudflare. A public static IP address and port forwarding are not required.

## 2. Prepare in Advance

Download Ubuntu Server 26.04 LTS `amd64` from the official Ubuntu Server page or from `https://releases.ubuntu.com/`. MSI Cubi 5 12M uses a 64-bit Intel platform, so you need the `amd64` server install image.

Verify the ISO before writing it to a USB drive:

```bash
cd ~/Downloads
gpg --keyid-format long --verify SHA256SUMS.gpg SHA256SUMS
sha256sum -c SHA256SUMS 2>&1 | grep 'ubuntu-26.04.*server.*amd64.*OK'
```

If the check does not print `OK`, download the ISO again. Do not install the system from an unverified image.

Prepare:

- an 8 GB or larger USB drive for the Ubuntu installer;
- a separate USB drive for project deployment;
- monitor, keyboard, and Ethernet cable;
- access to the ByFly/ONT router web interface;
- a strong password for the Ubuntu user;
- separate passwords/secrets for project `.env` files;
- a UPS if the server will be important continuously.

For the deployment USB drive, prefer encryption. The minimum approach is to keep secrets outside the repository in a separate encrypted archive. A stronger approach is a LUKS/VeraCrypt drive that is not left connected to the server permanently.

## 3. BIOS/UEFI on MSI Cubi

Connect monitor, keyboard, Ethernet, and power. On boot, normally:

- `Del` opens BIOS/UEFI Setup;
- `F11` opens the boot menu.

If the keys differ, follow the prompt on the first MSI boot screen.

In BIOS:

1. Load `Optimized Defaults`.
2. If the BIOS is very old, update it through official MSI support/M-FLASH. Do not update BIOS during unstable power.
3. Enable `UEFI Only`; disable `CSM/Legacy Boot` if available.
4. Keep or enable `Secure Boot`. If Ubuntu does not boot after installation, temporarily disable Secure Boot and investigate separately.
5. Enable `TPM`/`fTPM`/`Intel PTT` if available.
6. Enable `Intel Virtualization Technology` and `VT-d`. Podman does not require this, but it is useful for future VMs.
7. Confirm that the 1 TB NVMe drive is visible in BIOS.
8. For SATA, use `AHCI` if there is a choice.
9. Disable PXE/network boot after installation if you do not need it.
10. Disable Wi-Fi and Bluetooth in BIOS if the server will use Ethernet only.
11. Disable Thunderbolt or set the strictest security mode if Thunderbolt is not needed.
12. Configure recovery after power loss:
    - `Power On` - the server powers on after a power failure;
    - `Last State` - the server returns to the previous state.
13. Set a BIOS administrator/supervisor password and store it offline.
14. During installation, put USB first in the boot order or use `F11`.

A BIOS password does not protect against all attacks with physical access, but it reduces the risk of accidental or quick boot setting changes.

## 4. Install Ubuntu Server 26.04 LTS

Boot from the installer USB through `F11`.

Recommended installer choices:

- installer language: English is fine, so system messages and errors are easier to search;
- keyboard: your preferred layout;
- network: Ethernet through DHCP;
- proxy: empty unless ByFly/your network requires a proxy;
- mirror: default or the nearest reliable mirror;
- OpenSSH: do not install;
- snaps: do not select anything extra.

### Disk Layout

There are two reasonable options.

Option A, safer for data on disk: `Use entire disk` + LVM + LUKS encryption if the installer offers encryption. Downside: after every full shutdown, power failure, or reboot, the server will stop for the LUKS passphrase. This is acceptable if you always have physical access.

Option B, more autonomous: `Use entire disk` + LVM without encryption. Downside: if the disk is stolen, data and secrets are protected only by filesystem permissions, not cryptography. This is more convenient if the server must recover automatically after a power outage.

For a home server without remote SSH, choose option A if you are ready to enter the passphrase after reboots. If uptime matters more, choose option B and be especially careful with physical security and backups.

Profile:

- hostname: for example `cubi-prod-01`;
- admin user: not `admin`, not `root`; use a normal name;
- password: a long unique phrase.

After installation completes, remove the USB drive and reboot.

## 5. First Check After Installation

Log in locally on the console and check the base state:

```bash
lsb_release -a
uname -a
lsblk -f
free -h
df -h
ip address
timedatectl
```

Set the timezone:

```bash
sudo timedatectl set-timezone Europe/Minsk
sudo timedatectl set-ntp true
timedatectl
```

Update the system:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

After reboot, log in locally again.

## 6. Base Packages

Install the minimum package set for operations, containers, diagnostics, and updates:

```bash
sudo apt update
sudo apt install -y \
  ca-certificates \
  curl \
  git \
  gnupg \
  htop \
  jq \
  lsb-release \
  net-tools \
  openssl \
  podman \
  podman-compose \
  rsync \
  tmux \
  ufw \
  unattended-upgrades \
  uidmap \
  fuse-overlayfs \
  passt \
  netavark \
  aardvark-dns
```

If `apt` cannot find `podman` or `podman-compose`, enable the Ubuntu `universe` repository and repeat installation:

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo apt update
```

Check versions:

```bash
podman --version
podman-compose --version
```

If `podman-compose` is not available in the Ubuntu 26.04 repository, use `podman compose`, but remember that it is a wrapper around an external compose provider. For production, document and standardize one startup method per project.

## 7. Disable SSH Completely

OpenSSH should not have been installed during setup. Check explicitly:

```bash
systemctl status ssh || true
systemctl status ssh.socket || true
ss -tulpn
```

If SSH is installed anyway:

```bash
sudo systemctl disable --now ssh.service ssh.socket 2>/dev/null || true
sudo apt purge -y openssh-server
sudo apt autoremove --purge -y
```

Then check listening ports again:

```bash
ss -tulpn
```

The server should not have `0.0.0.0:22`, `[::]:22`, or other unexpected public listeners.

## 8. Users and Project Directories

The admin user is for system maintenance. Containers should run rootless under a separate non-sudo user, for example `apps`.

Create the user and directories:

```bash
sudo adduser --disabled-password --gecos "" apps
sudo loginctl enable-linger apps

sudo mkdir -p /srv/projects /srv/backups /srv/incoming-usb
sudo chown apps:apps /srv/projects /srv/backups
sudo chmod 750 /srv/projects /srv/backups
sudo chmod 755 /srv/incoming-usb
```

Check subuid/subgid for rootless Podman:

```bash
grep '^apps:' /etc/subuid /etc/subgid
```

If entries are missing, add them:

```bash
echo 'apps:100000:65536' | sudo tee -a /etc/subuid
echo 'apps:100000:65536' | sudo tee -a /etc/subgid
```

Check rootless Podman:

```bash
sudo -iu apps podman info
```

Do not disable `kernel.unprivileged_userns_clone`; rootless Podman depends on user namespaces.

## 9. UFW Firewall

Because SSH is not used, no inbound allow rules are needed.

Enable UFW:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw logging on
sudo ufw enable
sudo ufw status verbose
```

Check that IPv6 is enabled in UFW too:

```bash
grep '^IPV6=' /etc/default/ufw
```

Expected:

```text
IPV6=yes
```

If it says `no`, change it to `yes` and restart UFW:

```bash
sudo sed -i 's/^IPV6=.*/IPV6=yes/' /etc/default/ufw
sudo ufw disable
sudo ufw enable
sudo ufw status verbose
```

Do not open application ports to the outside. In compose files, publish services only on loopback, for example:

```yaml
ports:
  - "127.0.0.1:3001:3000"
```

Check:

```bash
ss -tulpn
```

Project ports should listen on `127.0.0.1:<port>`, not on `0.0.0.0:<port>`.

## 10. ByFly/ONT Router

In the router web interface:

1. Change the router admin password.
2. Disable remote administration from the internet side.
3. Disable UPnP unless needed.
4. Do not enable DMZ.
5. Do not create port forwarding to the server.
6. Reserve a stable DHCP lease for the server by MAC address.
7. Update router firmware only if the ISP or vendor provides a safe official process.
8. If router Wi-Fi is used, enable WPA2/WPA3 and a long password.

Cloudflare Tunnel should work behind NAT and CG-NAT. The key requirement is that the server can make outbound connections.

Check access to Cloudflare Tunnel endpoints:

```bash
sudo apt install -y dnsutils netcat-openbsd
dig A region1.v2.argotunnel.com
nc -vz region1.v2.argotunnel.com 7844
nc -vz region2.v2.argotunnel.com 7844
```

If TCP 7844 is unavailable, check the router, ISP filtering, and local firewall. With normal UFW `allow outgoing`, the server does not block this itself.

## 11. Automatic Security Updates

Ubuntu usually enables security updates through `unattended-upgrades`, but verify explicitly:

```bash
sudo apt install -y unattended-upgrades
cat /etc/apt/apt.conf.d/20auto-upgrades
```

Expected base configuration:

```text
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
```

For a server with LUKS encryption, do not enable automatic reboot: after reboot, physical passphrase entry is required. Check `/etc/apt/apt.conf.d/50unattended-upgrades`:

```text
Unattended-Upgrade::Automatic-Reboot "false";
```

Check pending reboot:

```bash
test -f /var/run/reboot-required && cat /var/run/reboot-required || true
```

Weekly or monthly, connect physically, update the system, and reboot:

```bash
sudo apt update
sudo apt full-upgrade -y
test -f /var/run/reboot-required && sudo reboot
```

## 12. Additional Hardening

Check AppArmor:

```bash
sudo systemctl status apparmor
sudo aa-status
```

AppArmor should be active. Do not disable it for Podman without a specific reason.

Disable Bluetooth if it is not needed:

```bash
sudo systemctl disable --now bluetooth 2>/dev/null || true
rfkill list || true
```

If Wi-Fi is not used, prefer disabling it in BIOS. If disabling through the OS:

```bash
sudo rfkill block wifi
sudo rfkill block bluetooth
```

Add conservative sysctl settings that do not break rootless Podman:

```bash
sudo tee /etc/sysctl.d/99-local-hardening.conf >/dev/null <<'EOF'
kernel.kptr_restrict = 2
kernel.dmesg_restrict = 1
kernel.unprivileged_bpf_disabled = 1
net.ipv4.tcp_syncookies = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
EOF
sudo sysctl --system
```

Limit persistent journal size:

```bash
sudo mkdir -p /etc/systemd/journald.conf.d
sudo tee /etc/systemd/journald.conf.d/limits.conf >/dev/null <<'EOF'
[Journal]
SystemMaxUse=1G
MaxRetentionSec=30day
EOF
sudo systemctl restart systemd-journald
```

Periodically inspect running services:

```bash
systemctl --type=service --state=running
ss -tulpn
```

Remove packages and services that you actually do not use. Do not add third-party apt repositories unless necessary.

## 13. Install cloudflared

You can install `cloudflared` directly on the server or bring the `.deb` through USB.

Download on the server:

```bash
curl -L --output /tmp/cloudflared-linux-amd64.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo apt install -y /tmp/cloudflared-linux-amd64.deb
cloudflared --version
```

USB option:

1. On a trusted computer, download `cloudflared-linux-amd64.deb` from the official Cloudflare Downloads page.
2. Copy it to the deployment USB drive.
3. On the server, install it:

```bash
sudo apt install -y /media/$USER/DEPLOY/cloudflared-linux-amd64.deb
cloudflared --version
```

Replace `DEPLOY` with the actual USB volume label if it differs.

## 14. Temporary Launch Without a Domain: Quick Tunnel

First confirm that the project listens locally, for example:

```bash
curl -fsS http://127.0.0.1:3001/api/health || curl -I http://127.0.0.1:3001
```

Start a temporary tunnel:

```bash
cloudflared tunnel --url http://127.0.0.1:3001
```

`cloudflared` prints a random `trycloudflare.com` URL. Use this URL for a short test or demo.

Quick Tunnel limitations:

- the URL is random and temporary;
- the mode is not intended for production;
- there is no normal DNS binding for your hostname;
- do not publish sensitive forms or real user data there;
- after the process stops, the URL disappears.

For a longer test, keep the process in `tmux`:

```bash
tmux new -s tunnel
cloudflared tunnel --url http://127.0.0.1:3001
```

Detach from `tmux`: `Ctrl-b`, then `d`. Return:

```bash
tmux attach -t tunnel
```

## 15. Production Design After Buying a Domain

After buying a domain:

1. Add the domain to Cloudflare.
2. Change registrar nameservers to Cloudflare nameservers.
3. In Cloudflare Zero Trust, open `Networks` -> `Tunnels`.
4. Create a remotely-managed tunnel.
5. Select Linux and copy the service install command.
6. On the server, run a command like:

```bash
sudo cloudflared service install 'PASTE_TUNNEL_TOKEN_HERE'
sudo systemctl status cloudflared
```

7. In Routes/Published application, add a hostname, for example `risk.example.com`.
8. In `Service URL`, set the local application address, for example:

```text
http://127.0.0.1:3001
```

9. Verify:

```bash
curl -fsS http://127.0.0.1:3001/api/health || curl -I http://127.0.0.1:3001
curl -I https://risk.example.com
```

Recommended Cloudflare edge settings for a public project:

- TLS/HTTPS enabled;
- Always Use HTTPS enabled;
- WAF managed rules enabled;
- rate limiting for sensitive endpoints, for example `POST /api/waitlist`;
- Bot/Challenge controls enabled carefully so normal users are not blocked;
- enable Cloudflare Access for private admin applications, but do not create SSH access if you intentionally avoid remote SSH.

The tunnel token is a secret. If it is exposed, remove the tunnel connector or rotate the token in Cloudflare.

## 16. Deploy Projects Through USB

Projects live under `/srv/projects/project-name` and belong to the `apps` user.

Example structure:

```text
/srv/projects/
  bitcoin-risk-brief/
    podman-compose.yml
    .env
    backend/
    frontend/
```

### Bitcoin Risk Brief USB Kit

Prepare the v2 project kit on the workstation:

```bash
cd /path/to/bitcoin-risk-brief
bash server-kit/prepare-usb-kit.sh /Volumes/USB
```

The command creates `/Volumes/USB/bitcoin-risk-brief-server-kit` with deployment docs, a top-level
`deploy-from-usb.sh` entrypoint, ordered server scripts, a filtered `project/bitcoin-risk-brief/` snapshot,
`manifest.txt`, and `SHA256SUMS`. It replaces only that kit directory when rerun. The kit must not contain local `.env`,
`.git`, backups, dependency caches, build output, browser artifacts, container images, or an offline package mirror.

Connect the USB drive to the server and find the device:

```bash
lsblk -f
```

If it is not automounted:

```bash
sudo mkdir -p /mnt/deploy-usb
sudo mount /dev/sdX1 /mnt/deploy-usb
```

For a fresh install:

```bash
cd /mnt/deploy-usb/bitcoin-risk-brief-server-kit
bash scripts/01-bootstrap-host.sh
bash scripts/02-install-cloudflared-from-usb.sh
bash scripts/03-deploy-bitcoin-risk-brief.sh
sudoedit /srv/projects/bitcoin-risk-brief/.env
bash scripts/04-enable-bitcoin-risk-service.sh
bash scripts/05-health-check.sh
```

For an existing deployment, run the top-level deploy entrypoint:

```bash
cd /mnt/deploy-usb/bitcoin-risk-brief-server-kit
bash deploy-from-usb.sh
```

For the public readiness check after Cloudflare Tunnel is configured:

```bash
bash deploy-from-usb.sh https://bitcoinriskbrief.minihub.app
```

The default path verifies `SHA256SUMS`, deploys the project snapshot, preserves the existing production `.env` and
database volume, restarts the service, and runs health/readiness checks. It does not run `pg_dump`.

For the stricter backup-gated path, run:

```bash
bash deploy-from-usb.sh --with-backup https://bitcoinriskbrief.minihub.app
```

That mode runs a backup before copying new code, verifies the backup, copies the verified backup to the USB default
`backups-from-server/` or an operator-provided `BACKUP_COPY_DEST`, verifies the copied backup, then deploys and checks
the service.

Automatic live restore is not part of the kit. Restore only from a verified backup and only after taking the app offline
or using a staging/empty restore target.

## 17. Autostart Podman Compose Projects

For each project, create a rootless systemd user service under `apps`.

Example:

```bash
sudo -iu apps mkdir -p /home/apps/.config/systemd/user
sudo -iu apps tee /home/apps/.config/systemd/user/bitcoin-risk-brief.service >/dev/null <<'EOF'
[Unit]
Description=bitcoin-risk-brief Podman Compose stack
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/srv/projects/bitcoin-risk-brief
ExecStart=/usr/bin/podman-compose up -d --remove-orphans
ExecStop=/usr/bin/podman-compose down
RemainAfterExit=yes
TimeoutStartSec=900

[Install]
WantedBy=default.target
EOF

sudo -iu apps systemctl --user daemon-reload
sudo -iu apps systemctl --user enable --now bitcoin-risk-brief.service
sudo -iu apps systemctl --user status bitcoin-risk-brief.service
```

If the project builds images on startup, the first start can take a while. `TimeoutStartSec=900` gives up to 15 minutes.

Logs:

```bash
sudo -iu apps journalctl --user -u bitcoin-risk-brief.service -e
sudo -iu apps bash -lc 'cd /srv/projects/bitcoin-risk-brief && podman-compose logs --tail=200'
```

## 18. Backups

A 1 TB NVMe drive is not a backup. Minimum design:

- a local server copy for quick rollbacks;
- an external USB copy that is not always connected;
- periodic restore verification.

For `bitcoin-risk-brief`, use the project script:

```bash
cd /srv/projects/bitcoin-risk-brief
./scripts/backup.sh
```

Then copy the backup to external storage:

```bash
sudo rsync -a /srv/projects/bitcoin-risk-brief/backups/ /mnt/deploy-usb/backups/bitcoin-risk-brief/
sync
sudo umount /mnt/deploy-usb
```

For other projects, create separate database dumps and copies of important volumes. Do not consider a backup valid until you have tested restore at least once on a separate copy.

## 19. Regular Maintenance

Weekly:

```bash
sudo apt update
apt list --upgradable
test -f /var/run/reboot-required && cat /var/run/reboot-required || true
sudo ufw status verbose
ss -tulpn
sudo systemctl status cloudflared --no-pager
sudo -iu apps podman ps
sudo -iu apps podman system df
```

Monthly:

```bash
sudo apt full-upgrade -y
sudo apt autoremove --purge -y
sudo journalctl --vacuum-time=30d
sudo reboot
```

If LUKS is enabled, do the monthly reboot only when you are near the server and ready to enter the passphrase.

## 20. Emergency Public Shutdown

If you need to remove all projects from public access quickly:

```bash
sudo systemctl stop cloudflared
```

If you need to stop one project:

```bash
sudo -iu apps systemctl --user stop bitcoin-risk-brief.service
```

If you suspect `.env` or Cloudflare token exposure:

1. Stop `cloudflared`.
2. Stop the project.
3. Rotate the tunnel token in Cloudflare.
4. Change project passwords and API keys.
5. Check `ss -tulpn`, `podman ps`, application logs, and Cloudflare events.

## 21. Final Checklist

Before first public launch:

- BIOS updated only through the official process and protected with an administrator password.
- Boot mode: UEFI.
- Secure Boot enabled or intentionally disabled with a documented reason.
- Wi-Fi/Bluetooth/Thunderbolt disabled if unused.
- Ubuntu Server 26.04 LTS installed from a verified ISO.
- OpenSSH server is not installed.
- UFW enabled: deny incoming, allow outgoing.
- Router has no port forwarding, DMZ, or remote admin.
- Projects listen only on `127.0.0.1`.
- Podman runs projects rootless as `apps`.
- `.env` has mode `600` and is not stored in git.
- `unattended-upgrades` enabled.
- External backup exists and the restore plan has been tested.
- Quick Tunnel is used only temporarily.
- For production, a domain has been bought, added to Cloudflare DNS, and WAF/rate limiting are configured.

## 22. Useful Primary Sources

- Ubuntu Server documentation: `https://ubuntu.com/server/docs/`
- Ubuntu Server basic installation: `https://ubuntu.com/server/docs/tutorial/basic-installation/`
- Ubuntu ISO verification: `https://ubuntu.com/tutorials/how-to-verify-ubuntu`
- Ubuntu firewall/UFW: `https://ubuntu.com/server/docs/how-to/security/firewalls/`
- Ubuntu automatic updates: `https://ubuntu.com/server/docs/how-to/software/automatic-updates/`
- Ubuntu security suggestions: `https://ubuntu.com/server/docs/explanation/security/security_suggestions/`
- MSI Cubi 5 12M specifications: `https://www.msi.com/Business-Productivity-PC/Cubi-5-12M/Specification`
- Cloudflare Tunnel dashboard setup: `https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel/`
- Cloudflare Quick Tunnels: `https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/`
- Cloudflare Tunnel firewall requirements: `https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/tunnel-with-firewall/`
- Cloudflare cloudflared downloads: `https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/`
- Podman installation: `https://podman.io/docs/installation`
- Podman Compose wrapper: `https://docs.podman.io/en/latest/markdown/podman-compose.1.html`
- Podman Quadlet/systemd reference: `https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html`
