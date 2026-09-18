#!/usr/bin/env bash
# Sourced by install.sh and update.sh. Writes only the selected interpreter to stdout.
kot7k_python_candidate() {
  local candidate="$1" base
  [[ -x "$candidate" ]] || return 1
  base="$("$candidate" -c 'import sys; assert (3, 12) <= sys.version_info[:2] < (3, 15); print(getattr(sys, "_base_executable", sys.executable))' 2>/dev/null)" || return 1
  [[ -x "$base" ]] || return 1
  "$base" -c 'import sys, venv, ensurepip; assert (3, 12) <= sys.version_info[:2] < (3, 15)' 2>/dev/null || return 1
  printf '%s\n' "$base"
}

kot7k_python_runtime() {
  local root="$1" allow_install="${2:-no}" candidate name runtime uv
  local runtime_root="/opt/kot7k-runtimes"
  # Reuse the interpreter behind this checkout's venv; never nest virtualenvs.
  for candidate in "$root/api/.venv/bin/python" "$root/.venv/bin/python"; do
    if kot7k_python_candidate "$candidate"; then return 0; fi
  done
  for name in python3.13 python3.14 python3.12 python3; do
    candidate="$(command -v "$name" || true)"
    if kot7k_python_candidate "$candidate"; then return 0; fi
    if kot7k_python_candidate "/usr/local/bin/$name"; then return 0; fi
  done
  for candidate in "$runtime_root"/python/cpython-*/bin/python3*; do
    if kot7k_python_candidate "$candidate"; then return 0; fi
  done
  if [[ "$allow_install" != yes ]]; then
    echo "No compatible Python runtime found. Run install.sh to provision it." >&2
    return 1
  fi
  echo "==> Installing a private Python 3.13 runtime (system Python unchanged)" >&2
  apt-get update >&2 || return 1
  DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv ca-certificates >&2 || return 1
  mkdir -p "$runtime_root" || return 1
  # uv itself is installed in an isolated bootstrap environment, not system pip.
  if [[ ! -x "$runtime_root/uv-bootstrap/bin/uv" ]]; then
    /usr/bin/python3 -m venv "$runtime_root/uv-bootstrap" >&2 || return 1
    "$runtime_root/uv-bootstrap/bin/python" -m pip install uv >&2 || return 1
  fi
  uv="$runtime_root/uv-bootstrap/bin/uv"
  UV_PYTHON_INSTALL_DIR="$runtime_root/python" UV_PYTHON_BIN_DIR="$runtime_root/python-bin" \
    "$uv" --no-config python install 3.13 >&2 || return 1
  runtime="$(UV_PYTHON_INSTALL_DIR="$runtime_root/python" "$uv" --no-config python find --managed-python 3.13)" || return 1
  kot7k_python_candidate "$runtime"
}
