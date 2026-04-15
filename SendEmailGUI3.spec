import sys

block_cipher = None

hiddenimports = []
if sys.platform == 'win32':
    hiddenimports = [
        'win32com', 'win32com.client', 'win32com.shell',
        'win32com.shell.shell', 'pythoncom', 'pywintypes',
    ]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pywin32'] if sys.platform != 'win32' else [],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == 'darwin':
    # macOS: onedir mode — COLLECT + BUNDLE (required for .app)
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='SendEmailGUI3',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='SendEmailGUI3',
    )
    app = BUNDLE(
        coll,
        name='SendEmailGUI3.app',
        icon=None,
        bundle_identifier='hu.gov.kk.SendEmailGUI3',
        info_plist={
            'NSHighResolutionCapable': True,
        },
    )
else:
    # Windows: onefile .exe
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='SendEmailGUI3',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,
    )
