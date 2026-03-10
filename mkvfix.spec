# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['mkvfix.py'],
    pathex=[],
    binaries=[
        ('/opt/homebrew/bin/mkvmerge', 'bin'),
        ('/opt/homebrew/bin/mkvpropedit', 'bin'),
    ],
    datas=[],
    hiddenimports=['language_data'],
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
    [],
    exclude_binaries=True,
    name='mkvfix',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    clean=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='mkvfix',
)
app = BUNDLE(
    coll,
    name='mkvfix.app',
    icon='mkvfix.icns',
    bundle_identifier=None,
)
