"""Desktop integration: .desktop entries, icons, and MIME associations."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from .config import (
    APPLICATIONS_DIR,
    BIN_DIR,
    ICONS_DIR,
)

# High quality Antigravity official SVG vector icon
OFFICIAL_ANTIGRAVITY_SVG = """<svg width="128" height="128" viewBox="0 0 136 136" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg_grad" x1="0" y1="0" x2="136" y2="136" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#1E1F22"/>
      <stop offset="100%" stop-color="#111215"/>
    </linearGradient>
    <filter id="glow" x="0" y="0" width="136" height="136" filterUnits="userSpaceOnUse">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>
  <rect width="136" height="136" rx="30" fill="url(#bg_grad)"/>
  <rect width="134" height="134" x="1" y="1" rx="29" stroke="#3186FF" stroke-width="1.5" stroke-opacity="0.3"/>
  <g transform="translate(12 10)">
    <path d="M89.6992 93.695C94.3659 97.195 101.366 94.8617 94.9492 88.445C75.6992 69.7783 79.7825 18.445 55.8659 18.445C31.9492 18.445 36.0325 69.7783 16.7825 88.445C9.78251 95.445 17.3658 97.195 22.0325 93.695C40.1159 81.445 38.9492 59.8617 55.8659 59.8617C72.7825 59.8617 71.6159 81.445 89.6992 93.695Z" fill="#3186FF"/>
    <ellipse cx="68" cy="46" rx="14" ry="14" fill="#FFE432" opacity="0.9"/>
    <ellipse cx="44" cy="74" rx="10" ry="10" fill="#00B95C" opacity="0.9"/>
    <ellipse cx="80" cy="72" rx="11" ry="11" fill="#FC413D" opacity="0.9"/>
    <path d="M55.8659 59.8617C46 59.8617 38 72 30 84C42 80 50 68 55.8659 59.8617Z" fill="#749BFF" opacity="0.8"/>
  </g>
</svg>"""

OFFICIAL_ANTIGRAVITY_IDE_SVG = """<svg width="128" height="128" viewBox="0 0 136 136" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="ide_bg" x1="0" y1="0" x2="136" y2="136" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#181A1F"/>
      <stop offset="100%" stop-color="#0E1013"/>
    </linearGradient>
  </defs>
  <rect width="136" height="136" rx="30" fill="url(#ide_bg)"/>
  <rect width="134" height="134" x="1" y="1" rx="29" stroke="#4C8DFF" stroke-width="1.5" stroke-opacity="0.4"/>
  <!-- Code brackets -->
  <path d="M38 48L24 68L38 88" stroke="#388BFD" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M98 48L112 68L98 88" stroke="#388BFD" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
  <!-- Orbiting Agent Core -->
  <circle cx="68" cy="68" r="16" fill="#3186FF"/>
  <circle cx="68" cy="68" r="8" fill="#FFE432"/>
  <ellipse cx="68" cy="68" rx="26" ry="10" stroke="#00B95C" stroke-width="2" transform="rotate(-30 68 68)"/>
</svg>"""


def install_desktop_icons(extracted_app_dir: Optional[Path] = None, component: str = "app") -> None:
    """Install application icons to standard XDG directories."""
    scalable_dir = ICONS_DIR / "scalable" / "apps"
    scalable_dir.mkdir(parents=True, exist_ok=True)

    icon_name = "antigravity" if component == "app" else "antigravity-ide"
    svg_content = OFFICIAL_ANTIGRAVITY_SVG if component == "app" else OFFICIAL_ANTIGRAVITY_IDE_SVG
    svg_target = scalable_dir / f"{icon_name}.svg"

    # Always write official scalable SVG icon
    svg_target.write_text(svg_content, encoding="utf-8")

    # If extracted directory contains png icons, copy them to respective resolution folders
    if extracted_app_dir and extracted_app_dir.exists():
        _search_and_install_bundled_icons(extracted_app_dir, icon_name)


def _search_and_install_bundled_icons(extracted_dir: Path, target_icon_name: str) -> None:
    """Find bundled PNG/SVG icons and install them into hicolor icon directories."""
    candidates = list(extracted_dir.glob("**/*icon*.png")) + list(extracted_dir.glob("**/code.png"))
    for candidate in candidates:
        try:
            # Check for size if identifiable or copy to default 256x256
            dest_dir = ICONS_DIR / "256x256" / "apps"
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidate, dest_dir / f"{target_icon_name}.png")
            break
        except Exception:
            continue


def create_app_desktop_file() -> Path:
    """Create .desktop entry for Antigravity Desktop App."""
    APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
    desktop_file = APPLICATIONS_DIR / "antigravity.desktop"

    bin_path = BIN_DIR / "antigravity"

    content = f"""[Desktop Entry]
Name=Antigravity
Comment=Google Antigravity - AI-First Agent Platform
GenericName=AI Agent Workspace
Exec={bin_path} %U
Icon=antigravity
Type=Application
StartupNotify=true
StartupWMClass=antigravity
Categories=Development;IDE;Utility;
MimeType=x-scheme-handler/antigravity;application/x-antigravity-workspace;
Keywords=google;antigravity;agent;gemini;ai;code;
Terminal=false
"""
    desktop_file.write_text(content, encoding="utf-8")
    return desktop_file


def create_ide_desktop_file() -> Path:
    """Create .desktop entry for Antigravity IDE."""
    APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
    desktop_file = APPLICATIONS_DIR / "antigravity-ide.desktop"

    bin_path = BIN_DIR / "antigravity-ide"

    content = f"""[Desktop Entry]
Name=Antigravity IDE
Comment=Google Antigravity IDE - AI-First Code Editor
GenericName=Integrated Development Environment
Exec={bin_path} %F
Icon=antigravity-ide
Type=Application
StartupNotify=true
StartupWMClass=Antigravity IDE
Categories=Development;IDE;TextEditor;
MimeType=text/plain;inode/directory;
Keywords=google;antigravity;ide;editor;code;gemini;vscode;
Terminal=false
Actions=new-empty-window;

[Desktop Action new-empty-window]
Name=New Empty Window
Exec={bin_path} --new-window %F
Icon=antigravity-ide
"""
    desktop_file.write_text(content, encoding="utf-8")
    return desktop_file


def update_desktop_database() -> None:
    """Trigger update-desktop-database and icon cache if installed."""
    if shutil.which("update-desktop-database"):
        try:
            subprocess.run(
                ["update-desktop-database", str(APPLICATIONS_DIR)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    if shutil.which("gtk-update-icon-cache"):
        try:
            subprocess.run(
                ["gtk-update-icon-cache", "-q", "-t", str(ICONS_DIR.parent)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass
