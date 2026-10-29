"""Configuration, default paths, and endpoints for Antigravity suite."""

import os
import platform
from pathlib import Path

# Base directories
HOME_DIR = Path.home()
LOCAL_DIR = HOME_DIR / ".local"
SHARE_DIR = LOCAL_DIR / "share"
BIN_DIR = LOCAL_DIR / "bin"
APPLICATIONS_DIR = SHARE_DIR / "applications"
ICONS_DIR = SHARE_DIR / "icons" / "hicolor"

# Application installation roots
APP_INSTALL_DIR = SHARE_DIR / "antigravity" / "app"
IDE_INSTALL_DIR = SHARE_DIR / "antigravity-ide" / "app"

# State and cache directories
STATE_DIR = SHARE_DIR / "antigravity-installer"
STATE_FILE = STATE_DIR / "state.json"
CACHE_DIR = HOME_DIR / ".cache" / "antigravity-installer"
DOWNLOADS_CACHE_DIR = CACHE_DIR / "downloads"

# Upstream Google endpoints
DOWNLOAD_PAGE_URL = "https://antigravity.google/download"
CLI_MANIFEST_BASE_URL = "https://antigravity-cli-auto-updater-974169037036.us-central1.run.app/manifests"
CLI_INSTALL_SCRIPT_URL = "https://antigravity.google/cli/install.sh"
OFFICIAL_FAVICON_URL = "https://antigravity.google/favicon.svg"

# Known fallback URLs if network scraping fails or offline
FALLBACKS = {
    "x64": {
        "app": {
            "version": "2.28.1",
            "full_version": "2.28.1-6709500728705024",
            "url": "https://storage.googleapis.com/antigravity-public/antigravity-hub/2.28.1-6709500728705024/linux-x64/Antigravity.tar.gz",
            "binary_name": "antigravity",
            "root_prefix": "Antigravity-x64",
        },
        "ide": {
            "version": "2.6.0",
            "full_version": "2.6.0-5526304964083712",
            "url": "https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/2.6.0-5526304964083712/linux-x64/Antigravity%20IDE.tar.gz",
            "binary_name": "antigravity-ide",
            "root_prefix": "Antigravity IDE",
        },
        "cli": {
            "version": "1.4.10",
            "url": "https://storage.googleapis.com/antigravity-public/antigravity-cli/1.4.10-5501573669978112/linux-x64/cli_linux_x64.tar.gz",
            "sha512": "3a14c21697e86349ce8402e0b1889cbd1d3a5f4e2cb4dc43aae1c48c404240c2ccff9f775eec277e1f759234a33ec026645c63ed22ab6f6ebede561eda7c38b6",
            "binary_name": "agy",
        },
    },
    "arm64": {
        "app": {
            "version": "2.28.1",
            "full_version": "2.28.1-6709500728705024",
            "url": "https://storage.googleapis.com/antigravity-public/antigravity-hub/2.28.1-6709500728705024/linux-arm/Antigravity.tar.gz",
            "binary_name": "antigravity",
            "root_prefix": "Antigravity-arm64",
        },
        "ide": {
            "version": "2.6.0",
            "full_version": "2.6.0-5526304964083712",
            "url": "https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/2.6.0-5526304964083712/linux-arm/Antigravity%20IDE.tar.gz",
            "binary_name": "antigravity-ide",
            "root_prefix": "Antigravity IDE",
        },
        "cli": {
            "version": "1.4.10",
            "url": "https://storage.googleapis.com/antigravity-public/antigravity-cli/1.4.10-5501573669978112/linux-arm64/cli_linux_arm64.tar.gz",
            "binary_name": "agy",
        },
    },
}


def get_system_arch() -> str:
    """Determine normalized system architecture for Google Antigravity downloads."""
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64", "x64"):
        return "x64"
    elif machine in ("aarch64", "arm64", "armv8l"):
        return "arm64"
    else:
        raise RuntimeError(f"Unsupported processor architecture: {machine}")


def get_cli_platform_key() -> str:
    """Return platform key for the CLI auto-updater manifest."""
    arch = get_system_arch()
    cli_arch = "amd64" if arch == "x64" else "arm64"
    return f"linux_{cli_arch}"
