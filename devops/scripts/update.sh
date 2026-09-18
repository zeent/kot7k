#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: $0 [--help]"
  echo "Update an install.sh-managed checkout from its Git upstream and verify services and HTTPS."
  exit 0
fi
[[ $# -eq 0 ]] || { echo "Unknown arguments. Use --help." >&2; exit 1; }
[[ "$(uname -s)" == Linux ]] || { echo "This updater requires Linux." >&2; exit 1; }
if [[ $EUID -ne 0 ]]; then
  exec sudo bash "$SCRIPT_DIR/update.sh"
fi
exec python3 "$SCRIPT_DIR/update.py"
