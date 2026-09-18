#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: $0 [--help]"
  echo "Interactive KOT7K installer for Debian/Ubuntu with systemd; provisions Python if needed."
  echo "Uses this checkout, asks for domain and initial administrator, installs PostgreSQL, Nginx and HTTPS."
  exit 0
fi
[[ $# -eq 0 ]] || { echo "Unknown arguments. Use --help." >&2; exit 1; }
[[ "$(uname -s)" == Linux ]] || { echo "This installer requires Linux." >&2; exit 1; }
if [[ $EUID -ne 0 ]]; then
  exec sudo bash "$SCRIPT_DIR/install.sh"
fi
source "$SCRIPT_DIR/python-runtime.sh"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/../.." && pwd -P)"
PYTHON_RUNTIME="$(kot7k_python_runtime "$ROOT_DIR" yes)"
exec "$PYTHON_RUNTIME" "$SCRIPT_DIR/install.py"
