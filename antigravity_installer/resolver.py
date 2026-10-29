"""Release URL and version resolver for Google Antigravity, Antigravity IDE, and CLI."""

import json
import logging
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Optional, Tuple

from .config import (
    CLI_MANIFEST_BASE_URL,
    DOWNLOAD_PAGE_URL,
    FALLBACKS,
    get_cli_platform_key,
    get_system_arch,
)

logger = logging.getLogger(__name__)


@dataclass
class ReleaseInfo:
    component: str  # 'app', 'ide', or 'cli'
    version: str  # e.g. '2.28.1'
    full_version: str  # e.g. '2.28.1-6709500728705024'
    url: str  # Download URL
    binary_name: str  # Binary inside package
    root_prefix: str  # Expected directory name inside tarball
    sha512: Optional[str] = None


def _fetch_html(url: str, timeout: int = 10) -> str:
    """Fetch URL with browser User-Agent header."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _extract_version_from_url(url: str) -> Tuple[str, str]:
    """Extract display version and full version stamp from release URL."""
    # Pattern matching versions like 2.28.1-6709500728705024 or 2.6.0-5526304964083712
    match = re.search(r"/([0-9]+\.[0-9]+\.[0-9]+(?:-[0-9]+)?)/(?:linux|darwin|windows)", url)
    if not match:
        match = re.search(r"/([0-9]+\.[0-9]+\.[0-9]+(?:-[0-9]+)?)/", url)
    if match:
        full_ver = match.group(1)
        short_ver = full_ver.split("-")[0]
        return short_ver, full_ver
    # Fallback to simple semver
    m = re.search(r"([0-9]+\.[0-9]+\.[0-9]+)", url)
    if m:
        return m.group(1), m.group(1)
    return "unknown", "unknown"


def resolve_app_release(arch: Optional[str] = None) -> ReleaseInfo:
    """Resolve latest release information for Antigravity Desktop App."""
    if arch is None:
        arch = get_system_arch()

    fallback = FALLBACKS[arch]["app"]
    url_arch = "linux-x64" if arch == "x64" else "linux-arm"

    try:
        html = _fetch_html(DOWNLOAD_PAGE_URL)
        # Search for Antigravity (App) tarball link
        pattern = rf'(https://[^\s"\'<>]*linux-(?:x64|arm)[^\s"\'<>]*Antigravity\.tar\.gz)'
        candidates = re.findall(pattern, html, re.I)

        target_url = None
        for candidate in candidates:
            if url_arch in candidate:
                target_url = candidate
                break

        if target_url:
            short_ver, full_ver = _extract_version_from_url(target_url)
            return ReleaseInfo(
                component="app",
                version=short_ver,
                full_version=full_ver,
                url=target_url,
                binary_name=fallback["binary_name"],
                root_prefix=fallback["root_prefix"],
            )
    except Exception as exc:
        logger.warning("Failed to fetch live app release info from %s: %s", DOWNLOAD_PAGE_URL, exc)

    return ReleaseInfo(
        component="app",
        version=fallback["version"],
        full_version=fallback["full_version"],
        url=fallback["url"],
        binary_name=fallback["binary_name"],
        root_prefix=fallback["root_prefix"],
    )


def resolve_ide_release(arch: Optional[str] = None) -> ReleaseInfo:
    """Resolve latest release information for Antigravity IDE."""
    if arch is None:
        arch = get_system_arch()

    fallback = FALLBACKS[arch]["ide"]
    url_arch = "linux-x64" if arch == "x64" else "linux-arm"

    try:
        html = _fetch_html(DOWNLOAD_PAGE_URL)
        # Search for Antigravity IDE tarball link (with optional %20 or space)
        pattern = rf'(https://[^\s"\'<>]*linux-(?:x64|arm)[^\s"\'<>]*Antigravity(?:%20|\+)?IDE[^\s"\'<>]*\.tar\.gz)'
        candidates = re.findall(pattern, html, re.I)

        target_url = None
        for candidate in candidates:
            if url_arch in candidate:
                target_url = candidate
                break

        if target_url:
            short_ver, full_ver = _extract_version_from_url(target_url)
            return ReleaseInfo(
                component="ide",
                version=short_ver,
                full_version=full_ver,
                url=target_url,
                binary_name=fallback["binary_name"],
                root_prefix=fallback["root_prefix"],
            )
    except Exception as exc:
        logger.warning("Failed to fetch live IDE release info from %s: %s", DOWNLOAD_PAGE_URL, exc)

    return ReleaseInfo(
        component="ide",
        version=fallback["version"],
        full_version=fallback["full_version"],
        url=fallback["url"],
        binary_name=fallback["binary_name"],
        root_prefix=fallback["root_prefix"],
    )


def resolve_cli_release(arch: Optional[str] = None) -> ReleaseInfo:
    """Resolve latest release information for Antigravity CLI (agy)."""
    if arch is None:
        arch = get_system_arch()

    fallback = FALLBACKS[arch]["cli"]
    platform_key = get_cli_platform_key()
    manifest_url = f"{CLI_MANIFEST_BASE_URL}/{platform_key}.json"

    try:
        raw_json = _fetch_html(manifest_url, timeout=7)
        data = json.loads(raw_json)
        version = data.get("version", fallback["version"])
        url = data.get("url", fallback["url"])
        sha512 = data.get("sha512", fallback.get("sha512"))
        return ReleaseInfo(
            component="cli",
            version=version,
            full_version=version,
            url=url,
            binary_name=fallback["binary_name"],
            root_prefix="",
            sha512=sha512,
        )
    except Exception as exc:
        logger.warning("Failed to fetch CLI manifest from %s: %s", manifest_url, exc)

    return ReleaseInfo(
        component="cli",
        version=fallback["version"],
        full_version=fallback["version"],
        url=fallback["url"],
        binary_name=fallback["binary_name"],
        root_prefix="",
        sha512=fallback.get("sha512"),
    )


def resolve_all_releases(arch: Optional[str] = None):
    """Resolve releases for all components."""
    if arch is None:
        arch = get_system_arch()
    return {
        "app": resolve_app_release(arch),
        "ide": resolve_ide_release(arch),
        "cli": resolve_cli_release(arch),
    }
