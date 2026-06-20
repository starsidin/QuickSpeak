# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['app\\main.py'],
    pathex=['app'],
    binaries=[],
    datas=[
        ('app\\icon.ico', '.'),
        ('app\\icon.png', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch', 'torchaudio', 'torchvision', 'transformers',
        'sklearn', 'scipy', 'pandas', 'fastapi', 'uvicorn',
        'qwen_asr', 'modelscope', 'huggingface_hub',
        'IPython', 'matplotlib', 'Cython', 'notebook', 'jupyter',
        'pytest', 'setuptools', 'pip', 'wheel',
        'PIL', 'cv2', 'tensorflow', 'keras', 'xarray',
        'statsmodels', 'seaborn', 'plotly', 'bokeh', 'dash',
        'streamlit', 'sphinx', 'docutils', 'pygments',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QuickSpeak',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon='app\\icon.ico',
    version='app\\version_info.txt',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='QuickSpeak',
)
