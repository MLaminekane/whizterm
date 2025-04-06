# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['whizterm.py'],
    pathex=[],
    binaries=[],
    datas=[('.env', '.')],
    hiddenimports=['typer', 'rich', 'requests', 'dotenv', 'python-dotenv'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    exclude_binaries=True,  
    name='WhizTerm',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # False pour une application GUI
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WhizTerm',
)

app = BUNDLE(
    coll,  # Utilisez la collection plutôt que exe directement
    name='WhizTerm.app',
    icon=None,  # Remplacez par le chemin vers votre icône .icns si disponible
    bundle_identifier='com.darkgunther.whizterm',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': 'True',
        'NSPrincipalClass': 'NSApplication',
        'LSBackgroundOnly': False,
    },
)
