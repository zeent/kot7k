#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: $0 [--help]"
  echo "Interactive KOT7K installer for Ubuntu 24.04+ / Debian 13+, with systemd."
  echo "Uses this checkout, asks for domain and initial administrator, installs PostgreSQL, Nginx and HTTPS."
  exit 0
fi
[[ $# -eq 0 ]] || { echo "Unknown arguments. Use --help." >&2; exit 1; }
[[ "$(uname -s)" == Linux ]] || { echo "This installer requires Linux." >&2; exit 1; }
if [[ $EUID -ne 0 ]]; then
  exec sudo bash "$SCRIPT_DIR/install.sh"
fi
command -v python3 >/dev/null || { apt-get update; apt-get install -y python3; }
exec python3 "$SCRIPT_DIR/install.py"
