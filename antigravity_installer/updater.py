"""Unified one-command updater orchestration for Google Antigravity Suite."""

import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import (
    BIN_DIR,
    get_system_arch,
)
from .installer import (
    InstallerState,
    install_app,
    install_cli,
    install_ide,
    install_symlink,
)
from .resolver import ReleaseInfo, resolve_all_releases


def ensure_updater_symlink(repo_root: Path) -> Path:
    """Ensure ~/.local/bin/antigravity-update symlink points to the project runner."""
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    target_bin = BIN_DIR / "antigravity-update"
    source_script = repo_root / "bin" / "antigravity-update"

    if source_script.exists():
        if target_bin.exists() or target_bin.is_symlink():
            target_bin.unlink()
        target_bin.symlink_to(source_script.resolve())
    return target_bin


def check_updates(arch: Optional[str] = None) -> Dict[str, Dict[str, Optional[str]]]:
    """Check currently installed versions vs latest upstream versions."""
    if arch is None:
        arch = get_system_arch()

    state = InstallerState()
    releases = resolve_all_releases(arch)

    results = {}
    for comp in ["app", "ide", "cli"]:
        rel = releases[comp]
        installed_ver = state.get_version(comp)
        available_ver = rel.version

        needs_update = False
        if installed_ver is None:
            status = "Not installed"
            needs_update = True
        elif installed_ver == "installed":
            # Present but version unknown
            status = "Installed (unknown version)"
            needs_update = False
        elif installed_ver != available_ver:
            status = "Update available"
            needs_update = True
        else:
            status = "Up to date"
            needs_update = False

        results[comp] = {
            "installed": installed_ver or "Not installed",
            "available": available_ver,
            "status": status,
            "needs_update": needs_update,
            "release": rel,
        }

    return results


def print_status_table(status_data: Dict[str, Dict[str, Any]]) -> None:
    """Display a formatted ASCII/Unicode status table."""
    labels = {
        "app": "Antigravity App (Desktop)",
        "ide": "Antigravity IDE (Editor)",
        "cli": "Antigravity CLI (agy)",
    }

    print("\n" + "=" * 70)
    print(f"{'Component':<28} {'Installed':<15} {'Latest':<12} {'Status':<15}")
    print("-" * 70)

    for comp in ["app", "ide", "cli"]:
        data = status_data[comp]
        label = labels.get(comp, comp)
        installed = str(data["installed"])
        latest = str(data["available"])
        status = str(data["status"])

        if data["status"] == "Up to date":
            status_icon = f"✓ {status}"
        elif data["status"] == "Update available":
            status_icon = f"⚡ {status}"
        else:
            status_icon = f"○ {status}"

        print(f"{label:<28} {installed:<15} {latest:<12} {status_icon:<15}")

    print("=" * 70 + "\n")


def run_update(
    components: Optional[List[str]] = None,
    force: bool = False,
    dry_run: bool = False,
    install_missing: bool = True,
    repo_root: Optional[Path] = None,
) -> bool:
    """Orchestrate the one-command update/install process.

    Returns True if operations succeeded.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent

    # Always ensure the global command symlink exists
    ensure_updater_symlink(repo_root)

    print("🔍 Checking upstream releases for Google Antigravity Suite...")
    arch = get_system_arch()
    print(f"   Architecture detected: {arch} (Linux)")

    status_data = check_updates(arch)
    print_status_table(status_data)

    target_comps = components or ["app", "ide", "cli"]

    tasks_to_run = []
    for comp in target_comps:
        info = status_data.get(comp)
        if not info:
            continue
        if force or info["needs_update"]:
            if info["status"] == "Not installed" and not install_missing and not force:
                continue
            tasks_to_run.append((comp, info["release"]))

    if not tasks_to_run:
        print("✨ Everything is up to date! No updates required.\n")
        return True

    if dry_run:
        print(f"Dry run mode: Would install/update: {[c for c, _ in tasks_to_run]}\n")
        return True

    print(f"📦 Updating {len(tasks_to_run)} component(s)...")

    for comp, release in tasks_to_run:
        try:
            if comp == "app":
                install_app(release, force=force)
            elif comp == "ide":
                install_ide(release, force=force)
            elif comp == "cli":
                install_cli(release, force=force)
        except Exception as exc:
            print(f"❌ Failed to install/update {comp}: {exc}", file=sys.stderr)
            return False

    print("\n🎉 Update completed successfully!")
    print("\nAvailable commands:")
    print("  • antigravity       : Launch Google Antigravity Desktop App")
    print("  • antigravity-ide   : Launch Google Antigravity IDE")
    print("  • agy               : Run Google Antigravity CLI")
    print("  • antigravity-update: Check and update all components anytime\n")
    return True
