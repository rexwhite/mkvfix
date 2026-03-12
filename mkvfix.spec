# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['mkvfix.py'],
    pathex=[],
    binaries=[
        ('binaries/mkvmerge', 'bin'),
        ('binaries/mkvpropedit', 'bin'),
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
    name='MKV Fix',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch='arm64',
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
    name='MKV Fix',
)
app = BUNDLE(
    coll,
    name='MKV Fix.app',
    icon='mkvfix.icns',
    bundle_identifier='com.mkvfix.app',
    info_plist={
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Matroska Video File',
                'CFBundleTypeRole': 'Editor',
                'CFBundleTypeIconFile': 'mkvfix.icns',
                'CFBundleTypeExtensions': ['mkv'],
                'LSItemContentTypes': ['io.matroska.mkv'],
                'LSHandlerRank': 'Owner',
            }
        ],
        'UTExportedTypeDeclarations': [
            {
                'UTTypeIdentifier': 'io.matroska.mkv',
                'UTTypeConformsTo': ['public.movie'],
                'UTTypeDescription': 'Matroska Video File',
                'UTTypeTagSpecification': {
                    'public.filename-extension': ['mkv'],
                    'public.mime-type': ['video/x-matroska']
                }
            }
        ]
    }
)
