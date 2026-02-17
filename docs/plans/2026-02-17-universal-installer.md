# Universal Shell Installer — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace per-distro packaging (.deb, Arch, Windows) with a single `install.sh` that works on any Linux system.

**Architecture:** A universal bash installer that detects the OS/arch, installs Python 3 + venv via the system package manager, downloads a release tarball from GitHub, creates an isolated venv with pip dependencies, and sets up a systemd user service. The app source + pre-built frontend assets are architecture-independent.

**Tech Stack:** Bash, Python 3 venv, systemd, GitHub Releases

---

### Task 1: Create `requirements.txt`

**Files:**
- Create: `requirements.txt`

**Step 1: Create the file**

```txt
quart
aiohttp
python-dotenv
```

These are the only third-party imports used across `execution/app.py` and `execution/fetch_*.py`. All are pure Python (no C extensions), so they work on any architecture.

**Step 2: Verify deps resolve**

```bash
cd /home/greg/Desktop/Home\ Media\ Dashboard\ Workspace/.worktrees/nextjs-hybrid
python3 -m venv /tmp/test-venv
/tmp/test-venv/bin/pip install -r requirements.txt
/tmp/test-venv/bin/python -c "import quart; import aiohttp; import dotenv; print('OK')"
rm -rf /tmp/test-venv
```

Expected: `OK`

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "feat: add requirements.txt for pip-based install"
```

---

### Task 2: Move systemd service to repo root

**Files:**
- Create: `media-dashboard.service` (repo root)

**Step 1: Create the unified service file**

The service file needs one change from the current version: `ExecStart` now points to `/usr/local/bin/media-dashboard` instead of `/usr/bin/media-dashboard`.

```ini
[Unit]
Description=Home Media Dashboard
After=network.target

[Service]
ExecStart=/usr/local/bin/media-dashboard
EnvironmentFile=-%h/.config/media-dashboard/env
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

**Step 2: Commit**

```bash
git add media-dashboard.service
git commit -m "feat: add unified systemd service file at repo root"
```

---

### Task 3: Create `install.sh`

**Files:**
- Create: `install.sh`

This is the main deliverable. The script must handle:

**Step 1: Write the installer script**

The script structure:

```bash
#!/usr/bin/env bash
set -euo pipefail
```

**Sections in order:**

1. **Configuration constants** — `APP_NAME`, `INSTALL_DIR=/opt/media-dashboard`, `SERVICE_NAME`, `GITHUB_REPO`, `LAUNCHER_PATH=/usr/local/bin/media-dashboard`

2. **Color/output helpers** — `info()`, `warn()`, `error()`, `success()` with color codes

3. **`detect_os()`** — Sets `OS_FAMILY` to `debian` or `arch` by checking for `/etc/debian_version` or `/etc/arch-release`. Exits with helpful error on unsupported OS.

4. **`detect_arch()`** — Maps `uname -m` output: `x86_64` → `amd64`, `aarch64` → `arm64`. (Informational only since the app is arch-independent, but logged for debugging.)

5. **`check_existing_deb()`** — Runs `dpkg -l media-dashboard 2>/dev/null`. If installed, prompts user: "Found existing .deb package. Remove it? [Y/n]". On yes: `sudo apt remove -y media-dashboard`.

6. **`check_existing_arch()`** — Runs `pacman -Q media-dashboard 2>/dev/null`. If installed: `sudo pacman -R --noconfirm media-dashboard`.

7. **`install_system_deps()`** — Based on `OS_FAMILY`:
   - debian: `sudo apt update && sudo apt install -y python3 python3-venv python3-pip`
   - arch: `sudo pacman -S --needed --noconfirm python python-pip`

8. **`get_latest_version()`** — Hits GitHub API: `https://api.github.com/repos/$GITHUB_REPO/releases/latest` to get tag name. Falls back to a hardcoded version if offline.

9. **`download_and_extract()`** — Downloads release tarball to `/tmp`, extracts to `/opt/media-dashboard/`. Uses `curl` or `wget`.

10. **`setup_venv()`** — `python3 -m venv /opt/media-dashboard/.venv`, then `/opt/media-dashboard/.venv/bin/pip install -r /opt/media-dashboard/requirements.txt`.

11. **`install_launcher()`** — Creates `/usr/local/bin/media-dashboard`:
    ```bash
    #!/usr/bin/env bash
    source /opt/media-dashboard/.venv/bin/activate
    cd /opt/media-dashboard/execution
    exec python3 app.py "$@"
    ```

12. **`install_service()`** — Copies `media-dashboard.service` to `/usr/lib/systemd/user/`.

13. **`scaffold_config()`** — If `~/.config/media-dashboard/env` doesn't exist, creates it with a template. If it does exist, prints "Config found, keeping existing."

14. **`write_version()`** — Writes installed version to `/opt/media-dashboard/version.txt`.

15. **`do_uninstall()`** — Removes `/opt/media-dashboard`, `/usr/local/bin/media-dashboard`, `/usr/lib/systemd/user/media-dashboard.service`. Tells user their config at `~/.config/media-dashboard/env` is preserved.

16. **`main()`** — Parses `--uninstall` / `--version` flags. Runs the install sequence. Prints final instructions.

**Step 2: Make executable and test basic invocation**

```bash
chmod +x install.sh
bash install.sh --help  # Should show usage / not crash
```

**Step 3: Commit**

```bash
git add install.sh
git commit -m "feat: add universal install.sh"
```

---

### Task 4: Create `build_release.sh`

**Files:**
- Create: `build_release.sh`

This replaces `deploy.sh` + the build steps from the old packaging scripts.

**Step 1: Write the build script**

```bash
#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:?Usage: build_release.sh <version>}"
APP_NAME="media-dashboard"

echo "Building release v${VERSION}..."

# 1. Build Next.js frontend
cd frontend
npm ci
npm run build
cd ..

# 2. Copy frontend assets to execution
rm -rf execution/static/* execution/templates/*
mkdir -p execution/static execution/templates
cp -r frontend/out/* execution/static/
mv execution/static/index.html execution/templates/index.html
[ -f execution/static/404.html ] && mv execution/static/404.html execution/templates/404.html

# 3. Create release tarball
RELEASE_DIR="/tmp/${APP_NAME}-${VERSION}"
rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

cp -r execution "$RELEASE_DIR/"
cp requirements.txt "$RELEASE_DIR/"
cp media-dashboard.service "$RELEASE_DIR/"
cp install.sh "$RELEASE_DIR/"
echo "$VERSION" > "$RELEASE_DIR/version.txt"

# Remove __pycache__
find "$RELEASE_DIR" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true

# Create tarball
TARBALL="dist/${APP_NAME}-${VERSION}.tar.gz"
mkdir -p dist
tar -czf "$TARBALL" -C /tmp "${APP_NAME}-${VERSION}"
rm -rf "$RELEASE_DIR"

echo "Release tarball: $TARBALL"
ls -lh "$TARBALL"
```

**Step 2: Commit**

```bash
git add build_release.sh
git commit -m "feat: add build_release.sh for creating release tarballs"
```

---

### Task 5: Clean up old packaging files

**Files:**
- Delete: `packaging/` (entire directory)
- Delete: `media-dashboard.spec`
- Delete: `deploy.sh`

**Step 1: Remove old files**

```bash
rm -rf packaging/
rm -f media-dashboard.spec
rm -f deploy.sh
```

**Step 2: Update `.gitignore`**

Remove the Arch build artifact entries (no longer relevant):

```diff
-.tmp/
-.env
-credentials.json
-token.json
-.venv/
-build/
-dist/
-__pycache__/
-*.spec
-
-# Arch build artifacts
-packaging/arch/pkg/
-packaging/arch/src/
-packaging/arch/execution/
-packaging/arch/media-dashboard/
-*.pkg.tar.zst
-
-# Development & Documentation
-directives/
-walkthrough.md
-.vscode/
-.worktrees/
+.tmp/
+.env
+credentials.json
+token.json
+.venv/
+build/
+dist/
+__pycache__/
+
+# Development & Documentation
+directives/
+walkthrough.md
+.vscode/
+.worktrees/
```

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove old packaging files (deb, arch, windows, pyinstaller)"
```

---

### Task 6: Update `README.md`

**Files:**
- Modify: `README.md`

**Step 1: Rewrite installation section**

Replace the Arch/Debian-specific install instructions with the universal approach. Keep the Configuration and Service sections as-is (they're still accurate).

New Installation section:

```markdown
## Installation

### Quick Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/asdghsas35/home-media-dashboard/main/install.sh | bash
```

### Manual Install

1. Download the latest release tarball from [Releases](https://github.com/asdghsas35/home-media-dashboard/releases)
2. Extract and run the installer:
   ```bash
   tar xzf media-dashboard-*.tar.gz
   cd media-dashboard-*/
   bash install.sh
   ```

### Upgrading from .deb/.pkg

If you previously installed via `.deb` or Arch package, the installer will detect and offer to remove the old package automatically. Your configuration is preserved.

### Uninstalling

```bash
curl -fsSL https://raw.githubusercontent.com/asdghsas35/home-media-dashboard/main/install.sh | bash -s -- --uninstall
```
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README with universal installer instructions"
```

---

## Verification Plan

### Automated Tests

Since this is a shell script (not Python logic), automated unit tests aren't practical. Instead we verify via integration testing:

**Test 1: Build a release tarball**

```bash
cd /home/greg/Desktop/Home\ Media\ Dashboard\ Workspace/.worktrees/nextjs-hybrid
bash build_release.sh 2.0.0
ls -lh dist/media-dashboard-2.0.0.tar.gz
tar tzf dist/media-dashboard-2.0.0.tar.gz | head -20
```

Expected: Tarball exists, contains `install.sh`, `requirements.txt`, `execution/`, `media-dashboard.service`, `version.txt`.

**Test 2: Dry-run the installer locally**

Since we can't install to `/opt` without sudo during development, test by extracting the tarball and verifying the script parses correctly:

```bash
bash install.sh --version
bash install.sh --help
```

### Manual Verification

**Test 3: Full install on the local system**

Run the installer on your CachyOS machine (uses pacman path):

```bash
sudo bash install.sh
```

Then verify:
- `/opt/media-dashboard/` exists with venv and source
- `/usr/local/bin/media-dashboard` exists and is executable
- `systemctl --user status media-dashboard` shows the service
- The dashboard is accessible on the configured port

**Test 4: Verify the app runs from the new install**

```bash
/usr/local/bin/media-dashboard
# Should start the Quart server on the configured port
```
