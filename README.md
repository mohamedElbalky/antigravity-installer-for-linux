# Google Antigravity & Antigravity IDE Unified Installer & Updater

A production-grade, zero-dependency installation and update tool for the complete **Google Antigravity** suite on Linux:

* 🚀 **Google Antigravity** (Desktop Application / Parallel Multi-Agent Hub)
* 💻 **Google Antigravity IDE** (AI-First Integrated Development Environment built on VS Code)
* ⚡ **Google Antigravity CLI** (`agy`)

---

## 🌟 Key Features

* **One-Command Update (`antigravity-update`)**: Checks upstream releases from Google, downloads updates, performs atomic directory replacement, and refreshes desktop launchers with a single command.
* **Full Desktop Integration**: Installs standard XDG `.desktop` files, high-resolution vector and raster icons (`scalable`, `256x256`), URL handler schemes (`antigravity://`), and MIME associations.
* **Safe & Atomic Upgrades**: Downloads to cache, verifies integrity, extracts into staging, and atomically swaps installations to eliminate corruption risk.
* **User-Space Installation**: Installs cleanly under `~/.local/` (`~/.local/share/` and `~/.local/bin/`), requiring **no root / `sudo` permissions**.
* **Zero External Dependencies**: Built with pure Python 3 standard library (`urllib`, `tarfile`, `hashlib`, `json`, `pathlib`).
* **Multi-Architecture Support**: Supports `x86_64` (amd64) and `aarch64` (arm64).
* **Optional Systemd Automation**: Includes systemd user timer files for hands-off background checks and updates.

---

## 🚀 Quick Start

### 1. Initial Installation

Clone the repository and run `./install.sh`:

```bash
git clone https://github.com/your-username/antigravity-installer.git
cd antigravity-installer
./install.sh
```

This will:
1. Register `~/.local/bin/antigravity-update` in your `$PATH`.
2. Detect your architecture (`x64` or `arm64`).
3. Query the latest releases from `https://antigravity.google/download`.
4. Install **Antigravity**, **Antigravity IDE**, and **Antigravity CLI**.
5. Configure desktop icons and application launcher entries.

---

## ⚡ Update With One Command

Once installed, simply run:

```bash
antigravity-update
```

You can run this command from any terminal or working directory. It displays an interactive status summary and updates any outdated components:

```text
======================================================================
Component                    Installed       Latest       Status         
----------------------------------------------------------------------
Antigravity App (Desktop)    2.28.1          2.28.1       ✓ Up to date   
Antigravity IDE (Editor)     2.6.0           2.6.0        ✓ Up to date   
Antigravity CLI (agy)        1.4.10          1.4.10       ✓ Up to date   
======================================================================

✨ Everything is up to date! No updates required.
```

If an update is available:
```bash
antigravity-update
```
will automatically download the new release, atomically extract and replace the application files, and refresh launchers.

---

## 🖥️ Launching the Applications

After installation, you can launch each tool directly from your terminal or your application menu (GNOME, KDE, etc.):

| Component | Terminal Command | Desktop Menu Name |
| :--- | :--- | :--- |
| **Antigravity Desktop** | `antigravity` | *Antigravity* |
| **Antigravity IDE** | `antigravity-ide` *(or `code-antigravity`)* | *Antigravity IDE* |
| **Antigravity CLI** | `agy` | — |
| **Suite Updater** | `antigravity-update` | — |

---

## ⚙️ CLI Options & Subcommands

```text
usage: antigravity-update [-h] [--version] [--force] [--component {all,app,ide,cli}]
                          [--no-cli] [--dry-run] [--verbose]
                          {update,install,check,status,uninstall} ...

Commands:
  update       Update all components to latest version (default)
  install      Install components
  check        Check for available updates without downloading
  status       Show installed versions and file paths
  uninstall    Cleanly remove installed components and desktop entries

Options:
  -f, --force              Force re-download and reinstall even if up to date
  -c, --component {all,app,ide,cli}
                           Selectively target a specific component
  --no-cli                 Skip CLI (agy) and only manage App and IDE
  --dry-run                Simulate actions without modifying files
  -v, --verbose            Enable verbose debug logs
```

### Examples

* **Check for updates without downloading:**
  ```bash
  antigravity-update check
  ```

* **Force re-install or repair Antigravity IDE:**
  ```bash
  antigravity-update install --component ide --force
  ```

* **Update only the Desktop App:**
  ```bash
  antigravity-update update --component app
  ```

* **Uninstall the complete suite:**
  ```bash
  antigravity-update uninstall
  ```

---

## 📁 File System Layout

The suite installs completely inside the user's home directory following XDG standards:

```text
~/.local/
├── bin/
│   ├── antigravity          -> ~/.local/share/antigravity/app/antigravity
│   ├── antigravity-ide      -> ~/.local/share/antigravity-ide/app/antigravity-ide
│   ├── code-antigravity     -> ~/.local/share/antigravity-ide/app/antigravity-ide
│   ├── agy                  -> Antigravity CLI binary
│   └── antigravity-update   -> Unified updater entrypoint
├── share/
│   ├── antigravity/app/     -> Antigravity Desktop App installation root
│   ├── antigravity-ide/app/ -> Antigravity IDE installation root
│   ├── applications/
│   │   ├── antigravity.desktop
│   │   └── antigravity-ide.desktop
│   ├── icons/hicolor/
│   │   ├── scalable/apps/   -> antigravity.svg, antigravity-ide.svg
│   │   └── 256x256/apps/    -> antigravity.png, antigravity-ide.png
│   └── antigravity-installer/
│       └── state.json       -> Records installed versions and metadata
└── .cache/
    └── antigravity-installer/
        └── downloads/       -> Cached release archives (resumed/reused)
```

---

## ⏰ Optional: Daily Background Auto-Update

To automatically check and update Antigravity in the background every day:

```bash
mkdir -p ~/.config/systemd/user/
cp systemd/antigravity-update.* ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now antigravity-update.timer
```

Verify timer status:
```bash
systemctl --user list-timers --all | grep antigravity
```

---

## 🧪 Running Tests

```bash
make test
# or
python3 -m unittest discover -s tests -p "test_*.py"
```

---

## 📜 License

Apache-2.0 or MIT.
