#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/../.." && pwd -P)"
UI_DIR="$ROOT_DIR/clients/web"
DIST_DIR="$ROOT_DIR/api/ui_dist"

echo "==> Building KOT7K UI"

cd "$UI_DIR"

npm ci
npm run build

echo "==> UI deployed successfully to $DIST_DIR"
