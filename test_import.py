"""
测试脚本：验证dstreader模块是否可以正确导入
"""
import sys
import os
from pathlib import Path

# 添加src到路径
script_dir = Path(__file__).parent
src_path = script_dir / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

print(f"Python路径: {sys.path[:3]}")
print(f"src路径: {src_path}")
print(f"src路径存在: {src_path.exists()}")

try:
    import dstreader
    print(f"✓ 成功导入 dstreader")
    print(f"  dstreader路径: {dstreader.__file__}")
    
    try:
        from dstreader.gui import main
        print(f"✓ 成功导入 dstreader.gui.main")
    except ImportError as e:
        print(f"✗ 导入 dstreader.gui.main 失败: {e}")
        
    try:
        from dstreader.parser import DSTParser
        print(f"✓ 成功导入 dstreader.parser.DSTParser")
    except ImportError as e:
        print(f"✗ 导入 dstreader.parser 失败: {e}")
        
    try:
        from dstreader.models import DSTFile
        print(f"✓ 成功导入 dstreader.models.DSTFile")
    except ImportError as e:
        print(f"✗ 导入 dstreader.models 失败: {e}")
        
except ImportError as e:
    print(f"✗ 导入 dstreader 失败: {e}")
    import traceback
    traceback.print_exc()

