#!/bin/bash
set -e

# Configuration
APP_NAME="media-dashboard"
VERSION="1.1.3"
ARCH="amd64"
BUILD_DIR="build/deb"
DEB_NAME="${APP_NAME}_${VERSION}_${ARCH}.deb"
PROJECT_ROOT=$(pwd)

# Ensure we are in the project root
if [ ! -f "media-dashboard.spec" ]; then
    echo "Error: Please run this script from the project root directory."
    exit 1
fi

echo "Cleaning up previous builds..."
rm -rf "$BUILD_DIR"
rm -f "$DEB_NAME"

echo "Building executable with PyInstaller..."
# Activate venv if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

pyinstaller --clean --noconfirm media-dashboard.spec

echo "Creating Debian package structure..."
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/lib/systemd/user"
mkdir -p "$BUILD_DIR/usr/bin"


echo "Copying configuration files..."
cp packaging/debian/control "$BUILD_DIR/DEBIAN/control"
cp packaging/debian/postinst "$BUILD_DIR/DEBIAN/postinst"
cp packaging/debian/prerm "$BUILD_DIR/DEBIAN/prerm"

chmod 755 "$BUILD_DIR/DEBIAN/postinst"
chmod 755 "$BUILD_DIR/DEBIAN/prerm"


cp packaging/debian/media-dashboard.service "$BUILD_DIR/usr/lib/systemd/user/"


echo "Copying executable..."
cp "dist/$APP_NAME" "$BUILD_DIR/usr/bin/"
chmod 755 "$BUILD_DIR/usr/bin/$APP_NAME"


if command -v dpkg-deb >/dev/null 2>&1; then
    echo "Building .deb package with dpkg-deb..."
    dpkg-deb --build "$BUILD_DIR" "dist/$DEB_NAME"
else
    echo "dpkg-deb not found. Using internal python script..."
    python3 packaging/create_deb.py "$BUILD_DIR" "dist/$DEB_NAME"
fi

echo "Package created: dist/$DEB_NAME"
echo "To install: sudo dpkg -i dist/$DEB_NAME"

