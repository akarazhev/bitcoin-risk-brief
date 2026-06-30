#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

log() {
  printf '\n==> %s\n' "$*"
}

warn() {
  printf 'WARN: %s\n' "$*" >&2
}

as_root() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

run_as_app() {
  if [[ "${EUID}" -eq 0 ]]; then
    runuser -u apps -- "$@"
  else
    sudo -u apps "$@"
  fi
}

ensure_line() {
  local line="$1"
  local file="$2"

  if ! as_root grep -qxF "${line}" "${file}" 2>/dev/null; then
    printf '%s\n' "${line}" | as_root tee -a "${file}" >/dev/null
  fi
}

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This script expects Ubuntu/Debian with apt-get." >&2
  exit 1
fi

if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  if [[ "${ID:-}" != "ubuntu" ]]; then
    warn "Detected ${PRETTY_NAME:-unknown OS}; the documented target is Ubuntu Server 26.04 LTS."
  fi
fi

log "Updating apt metadata"
as_root apt-get update

log "Enabling Ubuntu universe repository when available"
as_root apt-get install -y software-properties-common
if command -v add-apt-repository >/dev/null 2>&1; then
  as_root add-apt-repository -y universe || true
  as_root apt-get update
fi

log "Installing baseline packages"
packages=(
  aardvark-dns
  ca-certificates
  curl
  dnsutils
  fuse-overlayfs
  git
  gnupg
  htop
  jq
  lsb-release
  net-tools
  netavark
  netcat-openbsd
  openssl
  passt
  podman
  podman-compose
  rsync
  tmux
  ufw
  uidmap
  unattended-upgrades
)
as_root apt-get install -y "${packages[@]}"

log "Disabling and removing OpenSSH server if it exists"
as_root systemctl disable --now ssh.service ssh.socket 2>/dev/null || true
if dpkg-query -W -f='${Status}' openssh-server 2>/dev/null | grep -q 'install ok installed'; then
  as_root apt-get purge -y openssh-server
  as_root apt-get autoremove --purge -y
fi

log "Creating rootless application user and project directories"
if ! id apps >/dev/null 2>&1; then
  as_root adduser --disabled-password --gecos "" apps
fi
as_root loginctl enable-linger apps

as_root mkdir -p /srv/projects /srv/backups /srv/incoming-usb
as_root chown apps:apps /srv/projects /srv/backups
as_root chmod 750 /srv/projects /srv/backups
as_root chmod 755 /srv/incoming-usb

ensure_line 'apps:100000:65536' /etc/subuid
ensure_line 'apps:100000:65536' /etc/subgid

log "Configuring UFW: deny incoming, allow outgoing"
as_root sed -i 's/^IPV6=.*/IPV6=yes/' /etc/default/ufw
as_root ufw default deny incoming
as_root ufw default allow outgoing
as_root ufw logging on
as_root ufw --force enable

log "Configuring unattended upgrades without automatic reboot"
as_root tee /etc/apt/apt.conf.d/20auto-upgrades >/dev/null <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF

as_root tee /etc/apt/apt.conf.d/52local-no-auto-reboot >/dev/null <<'EOF'
Unattended-Upgrade::Automatic-Reboot "false";
EOF

log "Applying conservative host hardening that preserves rootless Podman"
as_root tee /etc/sysctl.d/99-local-hardening.conf >/dev/null <<'EOF'
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
as_root sysctl --system

log "Limiting persistent systemd journal size"
as_root mkdir -p /etc/systemd/journald.conf.d
as_root tee /etc/systemd/journald.conf.d/limits.conf >/dev/null <<'EOF'
[Journal]
SystemMaxUse=1G
MaxRetentionSec=30day
EOF
as_root systemctl restart systemd-journald

if [[ "${DISABLE_RADIOS:-false}" == "true" ]]; then
  log "Disabling Bluetooth and blocking Wi-Fi/Bluetooth through rfkill"
  as_root systemctl disable --now bluetooth 2>/dev/null || true
  as_root rfkill block wifi 2>/dev/null || true
  as_root rfkill block bluetooth 2>/dev/null || true
else
  warn "Wi-Fi/Bluetooth were not disabled by this script. Set DISABLE_RADIOS=true to apply that hardening step."
fi

log "Checking Podman for apps user"
if ! run_as_app podman info >/dev/null 2>&1; then
  warn "Rootless Podman check failed for user apps. Re-login or reboot may be needed before first container run."
fi

log "Bootstrap complete"
printf '%s\n' "Next: run scripts/02-install-cloudflared-from-usb.sh if cloudflared is needed, then scripts/03-deploy-bitcoin-risk-brief.sh."
