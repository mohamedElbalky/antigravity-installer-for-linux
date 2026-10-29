"""Resilient downloader with progress reporting and checksum verification."""

import hashlib
import os
import shutil
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Optional

from .config import DOWNLOADS_CACHE_DIR


def _format_size(bytes_num: float) -> str:
    """Format bytes into human-readable string (MB, KB, GB)."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_num < 1024.0:
            return f"{bytes_num:3.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} TB"


def render_progress_bar(
    transferred: int,
    total: int,
    start_time: float,
    description: str = "Downloading",
    bar_width: int = 30,
) -> None:
    """Render an interactive terminal progress bar."""
    elapsed = max(time.time() - start_time, 0.001)
    speed = transferred / elapsed

    if total > 0:
        percent = min(100.0, (transferred / total) * 100.0)
        filled = int(bar_width * transferred // total)
        bar = "█" * filled + "░" * (bar_width - filled)
        line = (
            f"\r  {description}: [{bar}] {percent:5.1f}% "
            f"({_format_size(transferred)} / {_format_size(total)}) "
            f"{_format_size(speed)}/s"
        )
    else:
        line = (
            f"\r  {description}: {_format_size(transferred)} transferred "
            f"({_format_size(speed)}/s)"
        )

    sys.stdout.write(line)
    sys.stdout.flush()


def download_file(
    url: str,
    target_path: Optional[Path] = None,
    expected_sha512: Optional[str] = None,
    force: bool = False,
    description: str = "Downloading",
    progress_callback: Optional[Callable[[int, int, float, str], None]] = render_progress_bar,
) -> Path:
    """Download a file with streaming progress and validation.

    Returns the Path to the downloaded file.
    """
    DOWNLOADS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if target_path is None:
        # Extract filename from URL
        parsed = urllib.parse.urlparse(url)
        filename = Path(urllib.parse.unquote(parsed.path)).name or "download.tar.gz"
        target_path = DOWNLOADS_CACHE_DIR / filename

    # Check if existing cached file matches
    if target_path.exists() and not force:
        if expected_sha512:
            current_hash = compute_sha512(target_path)
            if current_hash == expected_sha512:
                print(f"  ✓ Using valid cached archive: {target_path.name}")
                return target_path
        else:
            # Check non-zero size
            if target_path.stat().st_size > 10 * 1024 * 1024:  # At least 10MB for packages
                print(f"  ✓ Using existing cached archive: {target_path.name}")
                return target_path

    temp_path = target_path.with_suffix(".part")
    if temp_path.exists():
        temp_path.unlink()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    req = urllib.request.Request(url, headers=headers)

    start_time = time.time()
    hasher = hashlib.sha512() if expected_sha512 else None

    try:
        with urllib.request.urlopen(req, timeout=30) as response, open(temp_path, "wb") as out_file:
            content_length = response.headers.get("Content-Length")
            total_size = int(content_length) if content_length and content_length.isdigit() else 0
            transferred = 0
            chunk_size = 128 * 1024  # 128 KB chunks

            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                if hasher:
                    hasher.update(chunk)
                transferred += len(chunk)

                if progress_callback:
                    progress_callback(transferred, total_size, start_time, description)

        if progress_callback:
            sys.stdout.write("\n")
            sys.stdout.flush()

        # Checksum validation
        if expected_sha512:
            computed = hasher.hexdigest()
            if computed.lower() != expected_sha512.lower():
                temp_path.unlink(missing_ok=True)
                raise ValueError(
                    f"Checksum mismatch for {url}!\nExpected: {expected_sha512}\nGot:      {computed}"
                )

        temp_path.replace(target_path)
        return target_path

    except Exception:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise


def compute_sha512(path: Path) -> str:
    """Compute SHA-512 hex digest of a local file."""
    hasher = hashlib.sha512()
    with open(path, "rb") as f:
        while chunk := f.read(256 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()
