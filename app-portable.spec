# -*- mode: python ; coding: utf-8 -*-
# 便携版配置 - 文件夹模式，启动更快
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 收集 gradio 相关数据文件
datas = collect_data_files('gradio_client')
datas += collect_data_files('gradio')
datas += collect_data_files('gradio_images')

# 项目数据文件 - 排除模型文件（首次启动自动下载）
hivision_files = []
for root, dirs, files in os.walk('hivision'):
    for file in files:
        # 跳过模型文件
        if 'weights' in root and (file.endswith('.onnx') or file.endswith('.mnn')):
            continue
        src_path = os.path.join(root, file)
        dst_path = root
        hivision_files.append((src_path, dst_path))

datas += hivision_files
datas += [
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
    name='HivisionIDPhotos-portable',
)
