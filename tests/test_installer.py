"""Unit tests for Antigravity installer and updater."""

import json
import tempfile
import unittest
from pathlib import Path

from antigravity_installer.config import (
    FALLBACKS,
    get_cli_platform_key,
    get_system_arch,
)
from antigravity_installer.desktop import (
    OFFICIAL_ANTIGRAVITY_IDE_SVG,
    OFFICIAL_ANTIGRAVITY_SVG,
    create_app_desktop_file,
    create_ide_desktop_file,
)
from antigravity_installer.installer import InstallerState
from antigravity_installer.resolver import (
    ReleaseInfo,
    _extract_version_from_url,
    resolve_app_release,
    resolve_cli_release,
    resolve_ide_release,
)


class TestConfig(unittest.TestCase):
    def test_get_system_arch(self):
        arch = get_system_arch()
        self.assertIn(arch, ["x64", "arm64"])

    def test_get_cli_platform_key(self):
        key = get_cli_platform_key()
        self.assertIn(key, ["linux_amd64", "linux_arm64"])

    def test_fallbacks_structure(self):
        for arch in ["x64", "arm64"]:
            self.assertIn(arch, FALLBACKS)
            for comp in ["app", "ide", "cli"]:
                self.assertIn(comp, FALLBACKS[arch])
                self.assertTrue(FALLBACKS[arch][comp]["version"])
                self.assertTrue(FALLBACKS[arch][comp]["url"])


class TestResolver(unittest.TestCase):
    def test_extract_version_from_url(self):
        hub_url = (
            "https://storage.googleapis.com/antigravity-public/antigravity-hub/"
            "2.28.1-6709500728705024/linux-x64/Antigravity.tar.gz"
        )
        short_ver, full_ver = _extract_version_from_url(hub_url)
        self.assertEqual(short_ver, "2.28.1")
        self.assertEqual(full_ver, "2.28.1-6709500728705024")

        ide_url = (
            "https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/"
            "2.6.0-5526304964083712/linux-x64/Antigravity%20IDE.tar.gz"
        )
        short_ver, full_ver = _extract_version_from_url(ide_url)
        self.assertEqual(short_ver, "2.6.0")
        self.assertEqual(full_ver, "2.6.0-5526304964083712")

    def test_resolve_fallback(self):
        # Test that resolution always returns valid objects even if offline
        app_rel = resolve_app_release("x64")
        self.assertIsInstance(app_rel, ReleaseInfo)
        self.assertEqual(app_rel.component, "app")
        self.assertTrue(app_rel.version)
        self.assertTrue(app_rel.url.startswith("https://"))

        ide_rel = resolve_ide_release("x64")
        self.assertIsInstance(ide_rel, ReleaseInfo)
        self.assertEqual(ide_rel.component, "ide")
        self.assertTrue(ide_rel.version)

        cli_rel = resolve_cli_release("x64")
        self.assertIsInstance(cli_rel, ReleaseInfo)
        self.assertEqual(cli_rel.component, "cli")


class TestDesktop(unittest.TestCase):
    def test_svg_content(self):
        self.assertTrue(OFFICIAL_ANTIGRAVITY_SVG.startswith("<svg"))
        self.assertTrue(OFFICIAL_ANTIGRAVITY_SVG.endswith("</svg>"))
        self.assertTrue(OFFICIAL_ANTIGRAVITY_IDE_SVG.startswith("<svg"))
        self.assertTrue(OFFICIAL_ANTIGRAVITY_IDE_SVG.endswith("</svg>"))


class TestInstallerState(unittest.TestCase):
    def test_state_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_file = Path(tmp_dir) / "state.json"
            state = InstallerState(state_file)

            # Initial empty
            self.assertIsNone(state.get_version("app"))

            # Set installed
            fake_rel = ReleaseInfo(
                component="app",
                version="2.28.1",
                full_version="2.28.1-1234",
                url="https://example.com/app.tar.gz",
                binary_name="antigravity",
                root_prefix="Antigravity",
            )
            state.set_installed("app", fake_rel, Path(tmp_dir) / "app")
            self.assertEqual(state.get_version("app"), "2.28.1")

            # Reload from disk
            reloaded = InstallerState(state_file)
            self.assertEqual(reloaded.get_version("app"), "2.28.1")

            # Remove
            state.remove("app")
            self.assertIsNone(state.get_version("app"))


if __name__ == "__main__":
    unittest.main()
