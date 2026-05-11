# -*- mode: python ; coding: utf-8 -*-
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
]

# 隐藏导入（处理动态导入的模块）
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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HivisionIDPhotos',
    debug=False,
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
    # icon='assets/icon.ico',  # 如有.ico图标文件可取消注释
)
