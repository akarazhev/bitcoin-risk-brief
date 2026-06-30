#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '\n==> %s\n' "$*"
}

as_root() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
kit_dir="$(cd "${script_dir}/.." && pwd)"

deb_path="${1:-}"
if [[ -z "${deb_path}" ]]; then
  mapfile -t debs < <(find "${kit_dir}" -maxdepth 3 -type f -name 'cloudflared-linux-amd64.deb' | sort)
  if [[ "${#debs[@]}" -gt 0 ]]; then
    deb_path="${debs[0]}"
  fi
fi

if [[ -n "${deb_path}" ]]; then
  if [[ ! -f "${deb_path}" ]]; then
    echo "cloudflared .deb not found: ${deb_path}" >&2
    exit 1
  fi

  log "Installing cloudflared from ${deb_path}"
  as_root apt-get install -y "${deb_path}"
elif [[ "${ALLOW_DOWNLOAD:-false}" == "true" ]]; then
  log "Downloading latest cloudflared .deb from GitHub"
  tmp_deb="/tmp/cloudflared-linux-amd64.deb"
  curl -L --fail --output "${tmp_deb}" \
    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
  as_root apt-get install -y "${tmp_deb}"
else
  cat >&2 <<'EOF'
cloudflared-linux-amd64.deb was not found in this USB kit.

Either:
  1. copy cloudflared-linux-amd64.deb into this kit or kit/packages/ and re-run this script; or
  2. allow direct download:
       ALLOW_DOWNLOAD=true bash scripts/02-install-cloudflared-from-usb.sh
EOF
  exit 1
fi

log "Installed cloudflared version"
cloudflared --version
