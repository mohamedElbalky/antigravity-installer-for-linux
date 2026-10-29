#!/bin/bash
#
# Google Antigravity & Antigravity IDE - One-Command Updater
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$(command -v python3 || command -v python || true)"

if [ -z "$PYTHON_BIN" ]; then
    echo "Error: Python 3 is required to run antigravity-update." >&2
    exit 1
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/bin/antigravity-update" "$@"
