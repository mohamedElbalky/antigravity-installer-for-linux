"""Command-line interface for Antigravity installer and updater."""

import argparse
import logging
import sys
from pathlib import Path

from . import __version__
from .config import (
    APPLICATIONS_DIR,
    APP_INSTALL_DIR,
    BIN_DIR,
    ICONS_DIR,
    IDE_INSTALL_DIR,
)
from .installer import InstallerState
from .updater import (
    check_updates,
    ensure_updater_symlink,
    print_status_table,
    run_update,
)


def uninstall_components(components=None) -> None:
    """Cleanly uninstall specified or all components."""
    comps = components or ["app", "ide", "cli"]
    state = InstallerState()

    print(f"🗑️  Uninstalling components: {comps}...")
    if "app" in comps:
        import shutil

        if APP_INSTALL_DIR.parent.exists():
            shutil.rmtree(APP_INSTALL_DIR.parent, ignore_errors=True)
        (BIN_DIR / "antigravity").unlink(missing_ok=True)
        (APPLICATIONS_DIR / "antigravity.desktop").unlink(missing_ok=True)
        (ICONS_DIR / "scalable" / "apps" / "antigravity.svg").unlink(missing_ok=True)
        state.remove("app")
        print("  ✓ Antigravity App removed")

    if "ide" in comps:
        import shutil

        if IDE_INSTALL_DIR.parent.exists():
            shutil.rmtree(IDE_INSTALL_DIR.parent, ignore_errors=True)
        (BIN_DIR / "antigravity-ide").unlink(missing_ok=True)
        (BIN_DIR / "code-antigravity").unlink(missing_ok=True)
        (APPLICATIONS_DIR / "antigravity-ide.desktop").unlink(missing_ok=True)
        (ICONS_DIR / "scalable" / "apps" / "antigravity-ide.svg").unlink(missing_ok=True)
        state.remove("ide")
        print("  ✓ Antigravity IDE removed")

    if "cli" in comps:
        (BIN_DIR / "agy").unlink(missing_ok=True)
        state.remove("cli")
        print("  ✓ Antigravity CLI removed")

    print("✨ Uninstallation complete.")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="antigravity-update",
        description="Google Antigravity & Antigravity IDE Installer and One-Command Updater",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommand to execute")

    # Update subcommand (also default)
    p_update = subparsers.add_parser("update", help="Update all components to latest version")
    _add_shared_options(p_update)

    # Install subcommand
    p_install = subparsers.add_parser("install", help="Install components")
    _add_shared_options(p_install)

    # Check subcommand
    p_check = subparsers.add_parser("check", help="Check for available updates without installing")

    # Status subcommand
    p_status = subparsers.add_parser("status", help="Show installed versions and status")

    # Uninstall subcommand
    p_uninstall = subparsers.add_parser("uninstall", help="Uninstall components")
    p_uninstall.add_argument(
        "--component",
        "-c",
        choices=["all", "app", "ide", "cli"],
        default="all",
        help="Specific component to uninstall",
    )

    # Shared root options when no subcommand is specified
    _add_shared_options(parser)

    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    repo_root = Path(__file__).resolve().parent.parent

    # Determine targeted components
    selected_comp = getattr(args, "component", "all")
    no_cli = getattr(args, "no_cli", False)

    if selected_comp == "all":
        target_comps = ["app", "ide"] if no_cli else ["app", "ide", "cli"]
    else:
        target_comps = [selected_comp]

    # Dispatch commands
    cmd = args.subcommand or "update"

    if cmd == "check" or cmd == "status":
        status_data = check_updates()
        print_status_table(status_data)
        return 0

    elif cmd == "uninstall":
        uninstall_components(target_comps)
        return 0

    elif cmd in ("update", "install"):
        success = run_update(
            components=target_comps,
            force=args.force,
            dry_run=args.dry_run,
            install_missing=True,
            repo_root=repo_root,
        )
        return 0 if success else 1

    return 0


def _add_shared_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force re-download and re-install even if up-to-date",
    )
    parser.add_argument(
        "--component",
        "-c",
        choices=["all", "app", "ide", "cli"],
        default="all",
        help="Specific component to target (default: all)",
    )
    parser.add_argument(
        "--no-cli",
        action="store_true",
        help="Skip CLI (agy) and only manage Desktop App and IDE",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Display what would be downloaded and installed without applying changes",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable detailed logging output",
    )


if __name__ == "__main__":
    sys.exit(main())
