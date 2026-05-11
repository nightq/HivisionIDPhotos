# -*- mode: python ; coding: utf-8 -*-
# 极速便携版 - 模型内置，启动最快
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 收集 gradio 相关数据文件
datas = collect_data_files('gradio_client')
datas += collect_data_files('gradio')
datas += collect_data_files('gradio_images')

# 项目数据文件
datas += [
    ('hivision', 'hivision'),
    ('demo', 'demo'),
    ('assets', 'assets'),
    ('scripts', 'scripts'),
]

# 隐藏导入
hiddenimports = [
    'onnxruntime',
    'cv2',
    'PIL',
    'numpy',
    'scipy',
    'skimage',
    'mediapipe',
    'tqdm',
    'fastapi',
    'uvicorn',
]
hiddenimports += collect_submodules('gradio')
hiddenimports += collect_submodules('hivision')
hiddenimports += collect_submodules('demo')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# 文件夹模式（便携版）
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HivisionIDPhotos',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HivisionIDPhotos-极速便携版',
)
