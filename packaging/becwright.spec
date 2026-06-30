# PyInstaller spec for a standalone `becwright` binary (one file, no Python needed).
# Build from the repo root after `pip install .`:
#     pyinstaller packaging/becwright.spec
import os

from PyInstaller.utils.hooks import collect_submodules

root = os.path.dirname(SPECPATH)  # noqa: F821 - SPECPATH is injected by PyInstaller
entry = os.path.join(SPECPATH, "becwright_entry.py")  # noqa: F821

# Checks are loaded dynamically via importlib (`becwright run <name>`), so
# PyInstaller's static analysis cannot find them. Collect them all explicitly.
hiddenimports = collect_submodules("becwright.checks")

# On macOS we build a single universal2 binary (Intel + Apple Silicon) by setting
# BECWRIGHT_TARGET_ARCH=universal2 in CI; elsewhere it stays the host arch.
target_arch = os.environ.get("BECWRIGHT_TARGET_ARCH") or None

a = Analysis(
    [entry],
    pathex=[os.path.join(root, "src")],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="becwright",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=target_arch,
    codesign_identity=None,
    entitlements_file=None,
)
