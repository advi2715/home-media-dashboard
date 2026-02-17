# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['execution/app.py', 'execution/fetch_plex.py', 'execution/fetch_qbittorrent.py', 'execution/fetch_sonarr.py', 'execution/fetch_radarr.py'],
    pathex=['/home/greg/Desktop/Home Media Dashboard Workspace/execution'],
    binaries=[],
    datas=[('execution/templates', 'templates'), ('execution/static', 'static')],
    hiddenimports=['gzip', 'zlib', 'encodings', 'requests', 'urllib3', 'charset_normalizer', 'idna', 'fetch_plex', 'fetch_qbittorrent', 'fetch_sonarr', 'fetch_radarr'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='media-dashboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
