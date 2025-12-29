"""
PyInstaller hook for dstreader module
"""
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import os
import sys

# 获取项目src目录
hook_dir = os.path.dirname(__file__)
src_path = os.path.join(hook_dir, 'src')

# 添加到路径
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 收集所有子模块
try:
    hiddenimports = collect_submodules('dstreader')
except:
    # 如果collect_submodules失败，手动列出
    hiddenimports = [
        'dstreader',
        'dstreader.parser',
        'dstreader.models',
        'dstreader.visualizer',
        'dstreader.gui',
    ]

# 收集数据文件（如果有）
datas = []

