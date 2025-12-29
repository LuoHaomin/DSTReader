# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for DST Reader
"""

block_cipher = None

import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_all

# 获取项目根目录和src目录
project_root = os.path.dirname(SPECPATH)
src_path = os.path.join(project_root, 'src')

# 添加src目录到路径，确保PyInstaller能找到模块
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 尝试导入dstreader以确保它可以被找到
try:
    # 先添加src到路径
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    import dstreader
    dstreader_path = os.path.dirname(dstreader.__file__)
    print(f"找到dstreader模块: {dstreader_path}")
except ImportError as e:
    # 如果导入失败，使用src路径
    dstreader_path = os.path.join(src_path, 'dstreader')
    print(f"无法导入dstreader，使用路径: {dstreader_path}")

# 收集dstreader的所有子模块
# 先确保模块可以被导入
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    # 尝试收集子模块
    dstreader_submodules = collect_submodules('dstreader')
    print(f"收集到dstreader子模块: {dstreader_submodules}")
except Exception as e:
    # 如果collect_submodules失败，手动列出所有模块
    print(f"collect_submodules失败: {e}，使用手动列表")
    dstreader_submodules = [
        'dstreader',
        'dstreader.parser',
        'dstreader.models',
        'dstreader.visualizer',
        'dstreader.gui',
    ]

# 收集PyQt5的数据文件
try:
    pyqt5_datas = collect_data_files('PyQt5', includes=['**/*.dll', '**/*.pyd'])
except:
    pyqt5_datas = []

# 收集matplotlib的数据文件
try:
    matplotlib_datas = collect_data_files('matplotlib')
except:
    matplotlib_datas = []

a = Analysis(
    ['launch.py'],
    pathex=[src_path, project_root, dstreader_path],
    binaries=[],
    datas=pyqt5_datas + matplotlib_datas,
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'numpy',
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'dstreader',
        'dstreader.parser',
        'dstreader.models',
        'dstreader.gui',
        'dstreader.visualizer',
    ] + dstreader_submodules,
    hookspath=[project_root],  # 使用项目根目录作为hook路径
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DSTReader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口（GUI应用）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以在这里指定图标文件路径，例如: 'icon.ico'
)

