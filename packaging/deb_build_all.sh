#!/bin/bash
set -e

# Configuration
APP_NAME="media-dashboard"
VERSION="1.1.6"
ARCH="all"
BUILD_DIR="build/deb-all"
DEB_NAME="${APP_NAME}_${VERSION}_${ARCH}.deb"
INSTALL_DIR="/usr/share/media-dashboard"

echo "Cleaning up previous builds..."
rm -rf "$BUILD_DIR"
rm -f "dist/$DEB_NAME"

echo "Creating Debian package structure..."
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR$INSTALL_DIR"
mkdir -p "$BUILD_DIR/usr/lib/systemd/user"

echo "Copying application files..."
# Copy python source files
cp -r execution/* "$BUILD_DIR$INSTALL_DIR/"

# Create launcher script
LAUNCHER="$BUILD_DIR/usr/bin/$APP_NAME"
cat > "$LAUNCHER" <<EOF
#!/bin/bash
cd $INSTALL_DIR
exec python3 app.py "\$@"
EOF
chmod 755 "$LAUNCHER"

echo "Creating control file..."
cat > "$BUILD_DIR/DEBIAN/control" <<EOF
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: Greg <greg@example.com>
Depends: python3, python3-flask, python3-dotenv
Description: Home Media Dashboard (Universal)
 A dashboard for Plex, Sonarr, Radarr, and Qbittorrent.
 Runs on Python 3 (Architecture Independent).
EOF

echo "Copying scripts and service..."
# Reuse existing postinst/prerm if available, essentially just systemd reload
# We can use the ones from packaging/debian if they are generic enough.
# Let's check them? Assuming they are standard systemd reload calls.
cp packaging/debian/postinst "$BUILD_DIR/DEBIAN/postinst"
cp packaging/debian/prerm "$BUILD_DIR/DEBIAN/prerm"
chmod 755 "$BUILD_DIR/DEBIAN/postinst"
chmod 755 "$BUILD_DIR/DEBIAN/prerm"

cp packaging/debian/media-dashboard.service "$BUILD_DIR/usr/lib/systemd/user/"

echo "Building .deb package..."
mkdir -p dist

if command -v dpkg-deb >/dev/null 2>&1; then
    dpkg-deb --build "$BUILD_DIR" "dist/$DEB_NAME"
else
    echo "dpkg-deb not found. Using internal python script..."
    python3 packaging/create_deb.py "$BUILD_DIR" "dist/$DEB_NAME"
fi

echo "Package created: dist/$DEB_NAME"
