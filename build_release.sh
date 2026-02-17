#!/usr/bin/env bash
# ============================================================================
# Media Dashboard — Release Builder
# Builds the Next.js frontend, bundles it with the Python backend,
# and creates a release tarball ready for GitHub Releases.
#
# Usage: build_release.sh <version>
# Example: build_release.sh 2.0.0
# Output: dist/media-dashboard-<version>.tar.gz
# ============================================================================
set -euo pipefail

VERSION="${1:?Usage: build_release.sh <version>}"
APP_NAME="media-dashboard"
DIST_DIR="dist"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "════════════════════════════════════════════"
echo "  Building Media Dashboard v${VERSION}"
echo "════════════════════════════════════════════"
echo ""

# ── 1. Build Next.js Frontend ────────────────────────────────────────────────
echo "[1/4] Building Next.js frontend..."
cd "${PROJECT_ROOT}/frontend"

if [ ! -d "node_modules" ]; then
    echo "  Installing npm dependencies..."
    npm ci --silent
fi

export NEXT_TELEMETRY_DISABLED=1
npm run build

if [ ! -d "out" ]; then
    echo "ERROR: Next.js build did not produce 'out' directory."
    echo "Make sure next.config.ts has output: 'export'"
    exit 1
fi

echo "  Frontend built successfully."
echo ""

# ── 2. Copy Frontend Assets to Backend ───────────────────────────────────────
echo "[2/4] Copying frontend assets to backend..."
cd "$PROJECT_ROOT"

rm -rf execution/static/* execution/templates/*
mkdir -p execution/static execution/templates

cp -r frontend/out/* execution/static/
mv execution/static/index.html execution/templates/index.html

# Move 404 page if it exists
if [ -f execution/static/404.html ]; then
    mv execution/static/404.html execution/templates/404.html
fi

echo "  Assets copied."
echo ""

# ── 3. Assemble Release Directory ───────────────────────────────────────────
echo "[3/4] Assembling release..."

RELEASE_DIR="/tmp/${APP_NAME}-${VERSION}"
rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

# Copy application source (with frontend assets baked in)
cp -r execution "$RELEASE_DIR/"

# Copy installer and config files
cp install.sh "$RELEASE_DIR/"
cp requirements.txt "$RELEASE_DIR/"
cp media-dashboard.service "$RELEASE_DIR/"

# Write version marker
echo "$VERSION" > "$RELEASE_DIR/version.txt"

# Clean up __pycache__
find "$RELEASE_DIR" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
find "$RELEASE_DIR" -name "*.pyc" -delete 2>/dev/null || true

echo "  Release directory assembled."
echo ""

# ── 4. Create Tarball ────────────────────────────────────────────────────────
echo "[4/4] Creating tarball..."

mkdir -p "${PROJECT_ROOT}/${DIST_DIR}"
TARBALL="${PROJECT_ROOT}/${DIST_DIR}/${APP_NAME}-${VERSION}.tar.gz"

tar -czf "$TARBALL" -C /tmp "${APP_NAME}-${VERSION}"
rm -rf "$RELEASE_DIR"

echo ""
echo "════════════════════════════════════════════"
echo "  Release built successfully!"
echo ""
echo "  Tarball: ${TARBALL}"
ls -lh "$TARBALL"
echo ""
echo "  Upload to GitHub Releases:"
echo "  gh release create v${VERSION} ${TARBALL} --title 'v${VERSION}'"
echo "════════════════════════════════════════════"
