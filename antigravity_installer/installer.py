"""Installation, extraction, atomic updates, and symlink management."""

import json
import os
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .config import (
    APP_INSTALL_DIR,
    BIN_DIR,
    CLI_INSTALL_SCRIPT_URL,
    IDE_INSTALL_DIR,
    STATE_DIR,
    STATE_FILE,
)
from .desktop import (
    create_app_desktop_file,
    create_ide_desktop_file,
    install_desktop_icons,
    update_desktop_database,
)
from .downloader import download_file
from .resolver import ReleaseInfo


class InstallerState:
    """Manages persistent metadata about installed Antigravity components."""

    def __init__(self, state_file: Path = STATE_FILE):
        self.state_file = state_file
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def save(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def get_version(self, component: str) -> Optional[str]:
        # First check recorded state
        recorded = self.data.get(component, {}).get("version")
        if recorded:
            return recorded

        # Otherwise check if binary exists and detect version dynamically
        return self._detect_installed_version(component)

    def set_installed(self, component: str, release: ReleaseInfo, install_path: Path) -> None:
        if component not in self.data:
            self.data[component] = {}
        self.data[component].update(
            {
                "version": release.version,
                "full_version": release.full_version,
                "url": release.url,
                "install_path": str(install_path),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
        self.save()

    def remove(self, component: str) -> None:
        if component in self.data:
            del self.data[component]
            self.save()

    def _detect_installed_version(self, component: str) -> Optional[str]:
        """Inspect local binary if state.json is missing or outdated."""
        if component == "cli":
            cli_bin = BIN_DIR / "agy"
            if cli_bin.exists():
                try:
                    res = subprocess.run([str(cli_bin), "--version"], capture_output=True, text=True, timeout=3)
                    if res.returncode == 0:
                        ver = res.stdout.strip()
                        if ver:
                            return ver
                except Exception:
                    pass

        elif component == "app":
            bin_path = APP_INSTALL_DIR / "antigravity"
            if bin_path.exists():
                # Check package.json inside resources/app if present
                pkg_json = APP_INSTALL_DIR / "resources" / "app" / "package.json"
                if pkg_json.exists():
                    try:
                        d = json.loads(pkg_json.read_text(encoding="utf-8"))
                        return d.get("version")
                    except Exception:
                        pass
                return "installed"

        elif component == "ide":
            bin_path = IDE_INSTALL_DIR / "antigravity-ide"
            if bin_path.exists():
                pkg_json = IDE_INSTALL_DIR / "resources" / "app" / "package.json"
                if pkg_json.exists():
                    try:
                        d = json.loads(pkg_json.read_text(encoding="utf-8"))
                        return d.get("version")
                    except Exception:
                        pass
                return "installed"

        return None


def _make_executable(path: Path) -> None:
    """Ensure a file has execute permissions."""
    if path.exists():
        st = path.stat()
        path.chmod(st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def install_archive(
    archive_path: Path,
    target_install_dir: Path,
    expected_binary_name: str,
) -> Path:
    """Extract a .tar.gz archive and atomically install it into target directory.

    Returns the Path to the main executable.
    """
    target_install_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_extract_dir = target_install_dir.parent / f".tmp_extract_{int(time.time())}"

    if temp_extract_dir.exists():
        shutil.rmtree(temp_extract_dir, ignore_errors=True)
    temp_extract_dir.mkdir(parents=True, exist_ok=True)

    try:
        print(f"  ⠋ Extracting {archive_path.name}...")
        with tarfile.open(archive_path, "r:*") as tar:
            # Safer extraction on Python 3.12+
            if hasattr(tarfile, "data_filter"):
                tar.extractall(path=temp_extract_dir, filter="data")
            else:
                tar.extractall(path=temp_extract_dir)

        # Find the root folder inside the extracted directory
        extracted_entries = list(temp_extract_dir.iterdir())
        if len(extracted_entries) == 1 and extracted_entries[0].is_dir():
            payload_dir = extracted_entries[0]
        else:
            payload_dir = temp_extract_dir

        # Verify executable exists
        binary_candidates = list(payload_dir.glob(f"**/{expected_binary_name}"))
        if not binary_candidates:
            # Fallback search any executable matching binary name
            binary_candidates = [
                f for f in payload_dir.rglob("*") if f.name == expected_binary_name and f.is_file()
            ]

        if not binary_candidates:
            raise RuntimeError(
                f"Binary '{expected_binary_name}' was not found in extracted archive {archive_path.name}"
            )

        # Make all binaries and .so files executable
        for f in payload_dir.rglob("*"):
            if f.is_file() and (f.suffix == "" or f.suffix in (".sh", ".so")):
                _make_executable(f)

        # Atomic replacement: rename target_install_dir if it exists
        backup_dir = target_install_dir.parent / f".backup_{int(time.time())}"
        if target_install_dir.exists():
            target_install_dir.rename(backup_dir)

        # Move new payload into target_install_dir
        payload_dir.rename(target_install_dir)

        # Remove backup directory
        if backup_dir.exists():
            shutil.rmtree(backup_dir, ignore_errors=True)

        final_binary = target_install_dir / expected_binary_name
        if not final_binary.exists():
            # If binary was located in a subdirectory
            for b in target_install_dir.glob(f"**/{expected_binary_name}"):
                final_binary = b
                break

        _make_executable(final_binary)
        return final_binary

    finally:
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir, ignore_errors=True)


def install_symlink(source_bin: Path, symlink_name: str) -> Path:
    """Create a symlink in ~/.local/bin pointing to the application binary."""
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    symlink_path = BIN_DIR / symlink_name

    if symlink_path.exists() or symlink_path.is_symlink():
        symlink_path.unlink()

    symlink_path.symlink_to(source_bin)
    return symlink_path


def install_app(release: ReleaseInfo, force: bool = False) -> Path:
    """Download, extract, and install Google Antigravity Desktop App."""
    print(f"\n🚀 Installing Antigravity Desktop App (v{release.version})...")
    archive_path = download_file(
        url=release.url,
        force=force,
        description="Downloading Antigravity App",
    )

    binary_path = install_archive(
        archive_path=archive_path,
        target_install_dir=APP_INSTALL_DIR,
        expected_binary_name=release.binary_name,
    )

    # Setup symlink in ~/.local/bin/antigravity
    install_symlink(binary_path, "antigravity")

    # Install icons and desktop entry
    install_desktop_icons(APP_INSTALL_DIR, component="app")
    create_app_desktop_file()
    update_desktop_database()

    # Update state
    state = InstallerState()
    state.set_installed("app", release, APP_INSTALL_DIR)
    print(f"  ✓ Antigravity Desktop App installed to {APP_INSTALL_DIR}")
    print(f"  ✓ Launcher created: {BIN_DIR / 'antigravity'}")
    return binary_path


def install_ide(release: ReleaseInfo, force: bool = False) -> Path:
    """Download, extract, and install Google Antigravity IDE."""
    print(f"\n💻 Installing Antigravity IDE (v{release.version})...")
    archive_path = download_file(
        url=release.url,
        force=force,
        description="Downloading Antigravity IDE",
    )

    binary_path = install_archive(
        archive_path=archive_path,
        target_install_dir=IDE_INSTALL_DIR,
        expected_binary_name=release.binary_name,
    )

    # Setup symlinks in ~/.local/bin/
    install_symlink(binary_path, "antigravity-ide")
    # Also create convenient alias 'code-antigravity'
    install_symlink(binary_path, "code-antigravity")

    # Install icons and desktop entry
    install_desktop_icons(IDE_INSTALL_DIR, component="ide")
    create_ide_desktop_file()
    update_desktop_database()

    # Update state
    state = InstallerState()
    state.set_installed("ide", release, IDE_INSTALL_DIR)
    print(f"  ✓ Antigravity IDE installed to {IDE_INSTALL_DIR}")
    print(f"  ✓ Launcher created: {BIN_DIR / 'antigravity-ide'}")
    return binary_path


def install_cli(release: ReleaseInfo, force: bool = False) -> Path:
    """Install or update Antigravity CLI (agy)."""
    print(f"\n⚡ Installing Antigravity CLI 'agy' (v{release.version})...")
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    target_bin = BIN_DIR / "agy"

    # If agy already exists and force is True, we remove it first as official script checks for it
    if target_bin.exists() and force:
        target_bin.unlink()

    # Use official Google install script if curl and bash are available
    if shutil.which("curl") and shutil.which("bash"):
        cmd = f"curl -fsSL '{CLI_INSTALL_SCRIPT_URL}' | bash -s -- --dir '{BIN_DIR}'"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            print("  ✓ CLI installer completed successfully.")
        else:
            # Fallback to direct tarball download
            _install_cli_from_tarball(release, target_bin, force)
    else:
        _install_cli_from_tarball(release, target_bin, force)

    _make_executable(target_bin)
    state = InstallerState()
    state.set_installed("cli", release, target_bin)
    print(f"  ✓ CLI binary ready at {target_bin}")
    return target_bin


def _install_cli_from_tarball(release: ReleaseInfo, target_bin: Path, force: bool) -> None:
    """Fallback manual extraction of agy binary from tarball."""
    archive = download_file(
        url=release.url,
        expected_sha512=release.sha512,
        force=force,
        description="Downloading CLI archive",
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        with tarfile.open(archive, "r:*") as tar:
            tar.extractall(path=tmp_dir)
        found = list(Path(tmp_dir).glob("**/antigravity")) + list(Path(tmp_dir).glob("**/agy"))
        if not found:
            raise RuntimeError(f"Could not find 'agy' or 'antigravity' binary in {archive.name}")
        shutil.copy2(found[0], target_bin)
