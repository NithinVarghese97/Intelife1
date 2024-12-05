# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['run.py'],
    pathex=['C:\\ComputerCore\\CSER_Interpreter\\Client_Side_EasyRead_NDIS\\poppler-24.08.0\\Library\\bin', 'C:\\ComputerCore\\CSER_Interpreter\\Client_Side_EasyRead_NDIS\\mingw64\\bin'],
    binaries=[
        ('C:\\ComputerCore\\CSER_Interpreter\\Client_Side_EasyRead_NDIS\\mingw64\\bin\\libglib-2.0-0.dll', 'libglib-2.0-0.dll'),
        ('C:\\ComputerCore\\CSER_Interpreter\\Client_Side_EasyRead_NDIS\\mingw64\\bin\\libgio-2.0-0.dll', 'libgio-2.0-0.dll'),
        ('C:\\ComputerCore\\CSER_Interpreter\\Client_Side_EasyRead_NDIS\\mingw64\\bin\\libgobject-2.0-0.dll', 'libgobject-2.0-0.dll'),
        ('C:\ComputerCore\CSER_Interpreter\Client_Side_EasyRead_NDIS\poppler-24.08.0\Library\\bin\\*.dll','poppler-24.08.0\Library\bin')
    ],
    datas=[
        ('app\\files', 'app\\files'),
        ('app\\text', 'app\\text'),
        ('app\\static', 'app\\static'),
        ('app\\templates', 'app\\templates'),
        ('tailwind.config.js','tailwind.config.js'),
        ('.env', '.env'),
        ('nltk_data', 'nltk_data'),
    ],
    hiddenimports=['MySQLdb'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pysqlite2', 'torch._inductor'],
    collect_submodules=['numpy.core'],
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
    name='Interpreter',
    debug=True,
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
