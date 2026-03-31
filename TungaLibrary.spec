# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for TungaLibrary Attendance Manager
# Build command:  pyinstaller TungaLibrary.spec
#
# Output: dist/TungaLibrary/TungaLibrary.exe  (one-folder mode)
# One-folder is chosen over one-file because:
#   - Qt apps load many DLLs; one-file extracts to %TEMP% on every run (slow + AV flags)
#   - Installer (Inno Setup) will package the whole folder anyway

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ── Bundled read-only assets (go into _MEIPASS inside the exe folder) ──
bundled_datas = [
    ('assets',  'assets'),   # logo.png, logo.ico, default_avatar.png, fonts/
    ('themes',  'themes'),   # light.qss, dark.qss
]

# reportlab ships its own data files (fonts, etc.) – collect them all
bundled_datas += collect_data_files('reportlab')

# ── Hidden imports that PyInstaller's static analysis misses ──
hidden = [
    # PySide6 internals
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtNetwork',
    # pynput on Windows
    'pynput.keyboard._win32',
    'pynput.mouse._win32',
    # reportlab sub-packages
    'reportlab.graphics',
    'reportlab.platypus',
    'reportlab.lib',
    'reportlab.pdfgen',
    # openpyxl
    'openpyxl',
    'openpyxl.cell._writer',
]
hidden += collect_submodules('reportlab')

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=bundled_datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Not used at runtime
        # NOTE: do NOT exclude urllib/http/email — openpyxl->mimetypes needs them
        'matplotlib',
        'tkinter',
        'unittest',
        'distutils',
        'setuptools',
        'pip',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,          # one-folder mode
    name='TungaLibrary',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                      # UPX can break Qt DLLs; leave off
    console=False,                  # no console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/logo.ico',
    version=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='TungaLibrary',            # output folder: dist/TungaLibrary/
)
