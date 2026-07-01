# PyInstaller spec for the Linux AppImage build (see .github/workflows/build.yml).
# Bundles the app, the web UI, assets, and the Qt WebEngine backend into a
# self-contained onedir that appimagetool wraps into Ripperdoc-x86_64.AppImage.
import os
from PyInstaller.utils.hooks import collect_all

# SPECPATH is the directory of this spec file (build/); the project root is its
# parent. Paths must be absolute because PyInstaller resolves script/data paths
# relative to the spec dir, not the working directory.
ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir))

datas = [(os.path.join(ROOT, "web"), "web"), (os.path.join(ROOT, "assets"), "assets")]
binaries = []
hiddenimports = ["lz4", "lz4.block", "server", "http.server", "webbrowser"]

# Pull in everything the Qt WebEngine backend needs (process, resources, libs).
for pkg in ("webview", "PyQt5", "PyQtWebEngine"):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

a = Analysis(
    [os.path.join(ROOT, "app.py")],
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ripperdoc",
    debug=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="ripperdoc",
)
