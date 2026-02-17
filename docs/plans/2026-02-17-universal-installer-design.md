# Universal Shell Installer — Design Document

## Problem

The current packaging approach maintains **3 separate build pipelines** (Debian, Arch, Windows/Wine) with architecture-specific PyInstaller binaries. This is fragile, has version drift between files, and makes updates manual for end users. The actual target audience is 2 users on 2 platforms (CachyOS/amd64, Ubuntu-on-Pi/arm64).

## Solution

Replace all per-distro packaging with a **single `install.sh`** that works on any Linux system. Since all Python dependencies (`quart`, `aiohttp`, `python-dotenv`) are pure Python, the app is inherently architecture-independent — we don't need PyInstaller at all.

## Architecture

```
GitHub Release (tagged tarball)
    └── media-dashboard-<version>.tar.gz
        ├── install.sh          ← The universal installer
        ├── requirements.txt    ← Python pip deps
        ├── execution/          ← Python source + pre-built frontend assets
        │   ├── app.py
        │   ├── fetch_*.py
        │   ├── static/         ← Next.js built output
        │   └── templates/      ← index.html
        └── media-dashboard.service  ← Systemd unit file
```

### Install flow

```
User runs: curl -fsSL <raw-url>/install.sh | bash
                    │
                    ▼
        ┌─ Detect OS family (apt/pacman) & arch ─┐
        │                                         │
        ▼                                         ▼
  Detect old .deb?  ───yes──►  Prompt: remove it?
        │no                         │
        ▼                           ▼
  Install system deps         apt remove media-dashboard
  (python3, python3-venv)           │
        │                           │
        ▼◄──────────────────────────┘
  Download release tarball from GitHub
        │
        ▼
  Extract to /opt/media-dashboard/
  Create venv, pip install deps
        │
        ▼
  Install launcher → /usr/local/bin/media-dashboard
  Install systemd user service
  Scaffold config if missing (~/.config/media-dashboard/env)
        │
        ▼
  Done. "Run: systemctl --user enable --now media-dashboard"
```

### Installed file layout

| Path | Purpose |
|------|---------|
| `/opt/media-dashboard/` | App root (source + venv) |
| `/opt/media-dashboard/.venv/` | Isolated Python venv |
| `/opt/media-dashboard/execution/` | Python source + frontend assets |
| `/opt/media-dashboard/requirements.txt` | Pinned pip deps |
| `/opt/media-dashboard/version.txt` | Installed version marker |
| `/usr/local/bin/media-dashboard` | Launcher script (activates venv, runs app) |
| `/usr/lib/systemd/user/media-dashboard.service` | Systemd user unit |
| `~/.config/media-dashboard/env` | User config (never touched on update) |

### Script modes

- **`install.sh`** (no args) — Install or update
- **`install.sh --uninstall`** — Remove everything except user config
- **`install.sh --version`** — Show installed version

### Update flow

Re-running `install.sh` detects the existing install, downloads the latest release, replaces the source code, and recreates the venv. Config is preserved. The systemd service is restarted.

## What gets removed

- `packaging/` directory (all .deb, Arch, Windows build scripts)
- `media-dashboard.spec` (PyInstaller spec)
- `deploy.sh` (folded into `build_release.sh`)

## What gets added

- `install.sh` — The universal installer (in repo root)
- `requirements.txt` — `quart`, `aiohttp`, `python-dotenv`
- `build_release.sh` — Builds frontend + creates release tarball
- `media-dashboard.service` — Moved to repo root (single copy)

## Dependencies

**Third-party pip packages (all pure Python, arch-independent):**
- `quart` — async web framework
- `aiohttp` — async HTTP client
- `python-dotenv` — .env file loading

**System packages installed by the script:**
- `python3`, `python3-venv` (via `apt` or `pacman`)
