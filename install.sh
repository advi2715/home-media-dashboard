#!/usr/bin/env bash
# ============================================================================
# Media Dashboard — Universal Installer
# Supports: Debian/Ubuntu (amd64, arm64), Arch/CachyOS (amd64, arm64)
# Usage:
#   Install/Update: curl -fsSL <url>/install.sh | bash
#   Uninstall:      curl -fsSL <url>/install.sh | bash -s -- --uninstall
#   Version:        install.sh --version
# ============================================================================
set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
APP_NAME="media-dashboard"
INSTALL_DIR="/opt/media-dashboard"
LAUNCHER_PATH="/usr/local/bin/media-dashboard"
SERVICE_FILE="/usr/lib/systemd/user/media-dashboard.service"
CONFIG_DIR="${HOME}/.config/media-dashboard"
CONFIG_FILE="${CONFIG_DIR}/env"
VERSION_FILE="${INSTALL_DIR}/version.txt"
GITHUB_REPO="advi2715/home-media-dashboard"

# ── Colors & Output ─────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# ── Detect OS Family ────────────────────────────────────────────────────────
detect_os() {
    if [ -f /etc/debian_version ]; then
        OS_FAMILY="debian"
    elif [ -f /etc/arch-release ]; then
        OS_FAMILY="arch"
    elif [ -f /etc/fedora-release ]; then
        OS_FAMILY="fedora"
    else
        error "Unsupported OS. This installer supports Debian/Ubuntu and Arch-based systems."
        error "If you're on another distro, install Python 3 + venv manually and run:"
        error "  python3 -m venv ${INSTALL_DIR}/.venv"
        error "  ${INSTALL_DIR}/.venv/bin/pip install -r ${INSTALL_DIR}/requirements.txt"
        exit 1
    fi
    info "Detected OS family: ${BOLD}${OS_FAMILY}${NC}"
}

# ── Detect Architecture ─────────────────────────────────────────────────────
detect_arch() {
    local machine
    machine=$(uname -m)
    case "$machine" in
        x86_64)  ARCH="amd64" ;;
        aarch64) ARCH="arm64" ;;
        armv7l)  ARCH="armhf" ;;
        *)       ARCH="$machine" ;;
    esac
    info "Detected architecture: ${BOLD}${ARCH}${NC} ($machine)"
}

# ── Check for Existing Package Installations ─────────────────────────────────
check_existing_packages() {
    # Check for .deb package
    if command -v dpkg &>/dev/null; then
        if dpkg -l "$APP_NAME" 2>/dev/null | grep -q "^ii"; then
            warn "Found existing .deb package '${APP_NAME}' installed."
            echo ""
            read -rp "  Remove the old .deb package before continuing? [Y/n] " reply < /dev/tty
            reply=${reply:-Y}
            if [[ "$reply" =~ ^[Yy]$ ]]; then
                info "Removing .deb package..."
                sudo apt remove -y "$APP_NAME" 2>/dev/null || true
                success "Old .deb package removed."
            else
                warn "Keeping old .deb package. This may cause conflicts."
            fi
            echo ""
        fi
    fi

    # Check for Arch package
    if command -v pacman &>/dev/null; then
        if pacman -Q "$APP_NAME" 2>/dev/null; then
            warn "Found existing Arch package '${APP_NAME}' installed."
            echo ""
            read -rp "  Remove the old Arch package before continuing? [Y/n] " reply < /dev/tty
            reply=${reply:-Y}
            if [[ "$reply" =~ ^[Yy]$ ]]; then
                info "Removing Arch package..."
                sudo pacman -R --noconfirm "$APP_NAME" 2>/dev/null || true
                success "Old Arch package removed."
            else
                warn "Keeping old Arch package. This may cause conflicts."
            fi
            echo ""
        fi
    fi
}

# ── Install System Dependencies ──────────────────────────────────────────────
install_system_deps() {
    info "Checking system dependencies..."

    case "$OS_FAMILY" in
        debian)
            if ! command -v python3 &>/dev/null || ! python3 -m venv --help &>/dev/null 2>&1; then
                info "Installing Python 3 and venv..."
                sudo apt update -qq
                sudo apt install -y -qq python3 python3-venv python3-pip
            else
                success "Python 3 and venv already installed."
            fi
            ;;
        arch)
            if ! command -v python3 &>/dev/null; then
                info "Installing Python 3..."
                sudo pacman -S --needed --noconfirm python python-pip
            else
                success "Python 3 already installed."
            fi
            ;;
        fedora)
            if ! command -v python3 &>/dev/null; then
                info "Installing Python 3..."
                sudo dnf install -y python3 python3-pip
            else
                success "Python 3 already installed."
            fi
            ;;
    esac
}

# ── Determine Install Source ─────────────────────────────────────────────────
# The installer can run in two modes:
#   1. "Local" — run from within an extracted release tarball (files are next to this script)
#   2. "Remote" — run via curl|bash, downloads the latest release from GitHub
determine_source() {
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

    if [ -f "${SCRIPT_DIR}/execution/app.py" ] && [ -f "${SCRIPT_DIR}/requirements.txt" ]; then
        SOURCE_MODE="local"
        SOURCE_DIR="$SCRIPT_DIR"
        if [ -f "${SCRIPT_DIR}/version.txt" ]; then
            INSTALL_VERSION=$(cat "${SCRIPT_DIR}/version.txt")
        else
            INSTALL_VERSION="dev"
        fi
        info "Installing from local files (v${INSTALL_VERSION})"
    else
        SOURCE_MODE="remote"
        info "Downloading latest release from GitHub..."
        get_latest_version
        download_release
    fi
}

# ── Get Latest Version from GitHub ───────────────────────────────────────────
get_latest_version() {
    if command -v curl &>/dev/null; then
        INSTALL_VERSION=$(curl -fsSL "https://api.github.com/repos/${GITHUB_REPO}/releases/latest" \
            | grep '"tag_name"' | sed -E 's/.*"v?([^"]+)".*/\1/' ) || true
    fi

    if [ -z "${INSTALL_VERSION:-}" ]; then
        error "Could not determine latest version from GitHub."
        error "Check your internet connection, or download the release manually."
        exit 1
    fi

    info "Latest version: ${BOLD}v${INSTALL_VERSION}${NC}"
}

# ── Download Release ─────────────────────────────────────────────────────────
download_release() {
    local tarball_url="https://github.com/${GITHUB_REPO}/releases/download/v${INSTALL_VERSION}/${APP_NAME}-${INSTALL_VERSION}.tar.gz"
    local tmp_tarball="/tmp/${APP_NAME}-${INSTALL_VERSION}.tar.gz"

    info "Downloading: ${tarball_url}"

    if command -v curl &>/dev/null; then
        curl -fSL -o "$tmp_tarball" "$tarball_url"
    elif command -v wget &>/dev/null; then
        wget -q -O "$tmp_tarball" "$tarball_url"
    else
        error "Neither curl nor wget found. Please install one of them."
        exit 1
    fi

    SOURCE_DIR="/tmp/${APP_NAME}-${INSTALL_VERSION}"
    rm -rf "$SOURCE_DIR"
    tar xzf "$tmp_tarball" -C /tmp
    rm -f "$tmp_tarball"

    success "Downloaded and extracted v${INSTALL_VERSION}"
}

# ── Install Application ─────────────────────────────────────────────────────
install_app() {
    info "Installing to ${INSTALL_DIR}..."

    # Create install directory
    sudo mkdir -p "$INSTALL_DIR"

    # Copy application files
    sudo cp -r "${SOURCE_DIR}/execution" "$INSTALL_DIR/"
    sudo cp "${SOURCE_DIR}/requirements.txt" "$INSTALL_DIR/"

    # Write version marker
    echo "$INSTALL_VERSION" | sudo tee "$VERSION_FILE" > /dev/null

    success "Application files installed."
}

# ── Set Up Python Virtual Environment ────────────────────────────────────────
setup_venv() {
    info "Setting up Python virtual environment..."

    # Create or recreate venv
    if [ -d "${INSTALL_DIR}/.venv" ]; then
        info "Removing old virtual environment..."
        sudo rm -rf "${INSTALL_DIR}/.venv"
    fi

    sudo python3 -m venv "${INSTALL_DIR}/.venv"

    info "Installing Python dependencies..."
    sudo "${INSTALL_DIR}/.venv/bin/pip" install --quiet -r "${INSTALL_DIR}/requirements.txt"

    success "Virtual environment ready."
}

# ── Install Launcher Script ──────────────────────────────────────────────────
install_launcher() {
    info "Installing launcher at ${LAUNCHER_PATH}..."

    sudo tee "$LAUNCHER_PATH" > /dev/null << 'LAUNCHER'
#!/usr/bin/env bash
source /opt/media-dashboard/.venv/bin/activate
cd /opt/media-dashboard/execution
exec python3 app.py "$@"
LAUNCHER

    sudo chmod 755 "$LAUNCHER_PATH"
    success "Launcher installed."
}

# ── Install Systemd Service ──────────────────────────────────────────────────
install_service() {
    info "Installing systemd user service..."

    local service_src="${SOURCE_DIR}/media-dashboard.service"

    if [ ! -f "$service_src" ]; then
        # Generate service file if not in source (e.g. running from raw script)
        service_src="/tmp/media-dashboard.service"
        cat > "$service_src" << 'SERVICE'
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
SERVICE
    fi

    sudo mkdir -p "$(dirname "$SERVICE_FILE")"
    sudo cp "$service_src" "$SERVICE_FILE"

    success "Systemd service installed."
}

# ── Scaffold Configuration ───────────────────────────────────────────────────
scaffold_config() {
    if [ -f "$CONFIG_FILE" ]; then
        success "Existing config found at ${CONFIG_FILE} — keeping it."
        return
    fi

    info "Creating config template at ${CONFIG_FILE}..."
    mkdir -p "$CONFIG_DIR"

    cat > "$CONFIG_FILE" << 'CONFIG'
# Media Dashboard Configuration
# Edit these values to match your setup.

# Server Configuration
PORT=7152

# Plex
PLEX_URL=http://localhost:32400
PLEX_TOKEN=your_plex_token_here

# Qbittorrent
QBITTORRENT_URL=http://localhost:8080
QBITTORRENT_USERNAME=admin
QBITTORRENT_PASSWORD=adminadmin

# Sonarr
SONARR_URL=http://localhost:8989
SONARR_API_KEY=your_sonarr_api_key

# Radarr
RADARR_URL=http://localhost:7878
RADARR_API_KEY=your_radarr_api_key

# Overseerr
OVERSEERR_URL=http://localhost:5055
OVERSEERR_API_KEY=your_overseerr_api_key
CONFIG

    success "Config template created. Edit it with your details:"
    echo "  nano ${CONFIG_FILE}"
}

# ── Uninstall ────────────────────────────────────────────────────────────────
do_uninstall() {
    echo ""
    echo -e "${BOLD}Uninstalling Media Dashboard${NC}"
    echo "──────────────────────────────────────────"

    # Stop and disable service
    if systemctl --user is-active "$APP_NAME" &>/dev/null; then
        info "Stopping service..."
        systemctl --user stop "$APP_NAME" 2>/dev/null || true
    fi
    if systemctl --user is-enabled "$APP_NAME" &>/dev/null; then
        info "Disabling service..."
        systemctl --user disable "$APP_NAME" 2>/dev/null || true
    fi

    # Remove files
    if [ -d "$INSTALL_DIR" ]; then
        info "Removing ${INSTALL_DIR}..."
        sudo rm -rf "$INSTALL_DIR"
    fi

    if [ -f "$LAUNCHER_PATH" ]; then
        info "Removing ${LAUNCHER_PATH}..."
        sudo rm -f "$LAUNCHER_PATH"
    fi

    if [ -f "$SERVICE_FILE" ]; then
        info "Removing systemd service..."
        sudo rm -f "$SERVICE_FILE"
        systemctl --user daemon-reload 2>/dev/null || true
    fi

    echo ""
    success "Media Dashboard uninstalled."

    if [ -f "$CONFIG_FILE" ]; then
        info "Your config is preserved at: ${CONFIG_FILE}"
        info "To remove it: rm -rf ${CONFIG_DIR}"
    fi
}

# ── Show Version ─────────────────────────────────────────────────────────────
show_version() {
    if [ -f "$VERSION_FILE" ]; then
        echo "Media Dashboard v$(cat "$VERSION_FILE")"
    else
        echo "Media Dashboard is not installed."
    fi
}

# ── Show Usage ───────────────────────────────────────────────────────────────
show_usage() {
    echo "Media Dashboard Installer"
    echo ""
    echo "Usage:"
    echo "  install.sh              Install or update Media Dashboard"
    echo "  install.sh --uninstall  Remove Media Dashboard (preserves config)"
    echo "  install.sh --version    Show installed version"
    echo "  install.sh --help       Show this message"
}

# ── Main ─────────────────────────────────────────────────────────────────────
main() {
    case "${1:-}" in
        --uninstall)
            do_uninstall
            exit 0
            ;;
        --version)
            show_version
            exit 0
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
    esac

    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║     Media Dashboard — Installer          ║${NC}"
    echo -e "${BOLD}╚══════════════════════════════════════════╝${NC}"
    echo ""

    detect_os
    detect_arch
    check_existing_packages
    install_system_deps
    determine_source
    install_app
    setup_venv
    install_launcher
    install_service
    scaffold_config

    # Reload systemd
    systemctl --user daemon-reload 2>/dev/null || true

    echo ""
    echo "──────────────────────────────────────────"
    success "Media Dashboard v${INSTALL_VERSION} installed!"
    echo ""
    info "Next steps:"
    echo "  1. Edit your config:    nano ${CONFIG_FILE}"
    echo "  2. Enable the service:  systemctl --user enable --now ${APP_NAME}"
    echo "  3. Check status:        systemctl --user status ${APP_NAME}"
    echo "  4. View logs:           journalctl --user -u ${APP_NAME} -f"
    echo ""

    # Clean up remote source if downloaded
    if [ "${SOURCE_MODE:-}" = "remote" ]; then
        rm -rf "/tmp/${APP_NAME}-${INSTALL_VERSION}"
    fi
}

main "$@"
