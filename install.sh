#!/bin/bash
#
# Google Antigravity & Antigravity IDE - Setup & Initial Installer
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"

echo "=========================================================="
echo "  Google Antigravity & Antigravity IDE Installer"
echo "=========================================================="

mkdir -p "$BIN_DIR"

# Ensure ~/.local/bin is in PATH in common shell profiles
export PATH="$BIN_DIR:$PATH"
for profile in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$profile" ] && ! grep -q 'PATH.*\.local/bin' "$profile"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$profile"
        echo "  ✓ Added ~/.local/bin to $profile"
    fi
done

# Create global command symlink: antigravity-update
ln -sf "$SCRIPT_DIR/bin/antigravity-update" "$BIN_DIR/antigravity-update"
echo "  ✓ Registered global command: $BIN_DIR/antigravity-update"

# Run initial update/install
exec "$SCRIPT_DIR/update.sh" "$@"
