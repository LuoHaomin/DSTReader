# DST Reader

一个基于 PyQt5 的现代化 GUI 应用程序，用于查看和分析 DST 刺绣文件。

## 特性

- **交互式图案查看**: 缩放、平移、鼠标操作
- **实时动画播放**: 逐针显示刺绣过程
- **文件浏览器**: 浏览和选择 DST 文件
- **详细信息显示**: 文件元数据和统计信息
- **高性能解析**: 多线程处理大文件

## 快速开始

### Windows 用户
```bash
# 双击运行
run_dstreader.bat

# 或命令行
python launch.py
```

### Linux/macOS 用户
```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
python launch.py
```

## 使用方法

1. **打开 DST 文件**: 点击 "Open DST File" 或使用 Ctrl+O
2. **浏览文件夹**: 点击 "Open Folder" 或使用 Ctrl+Shift+O
3. **查看图案**: 使用鼠标滚轮缩放，左键拖拽平移
4. **播放动画**: 点击 "Play" 按钮，调整速度滑块
5. **查看信息**: 切换到 "File Information" 标签

## 控制说明

- **鼠标滚轮**: 缩放图案
- **左键拖拽**: 平移视图
- **Ctrl+F**: 适应窗口大小
- **Ctrl+O**: 打开文件
- **Ctrl+Shift+O**: 打开文件夹

## 项目结构

```
DSTReader/
├── launch.py              # 推荐启动脚本
├── main.py                # 主入口点
├── run_dstreader.bat      # Windows 批处理
├── requirements.txt       # 依赖列表
├── setup.py               # pip 安装配置
├── README.md              # 项目文档
└── src/dstreader/         # 核心包
    ├── __init__.py       # 包初始化
    ├── models.py         # 数据模型
    ├── parser.py         # DST 文件解析器
    ├── visualizer.py     # Matplotlib 可视化
    └── gui/__init__.py   # PyQt5 GUI 应用
```

## 技术特点

- **多线程解析**: 大文件自动使用多线程加速
- **NumPy 优化**: 位运算使用 NumPy 加速
- **文件缓存**: 避免重复解析
- **错误处理**: 智能处理各种 DST 文件格式问题

## 安装

```bash
# 开发模式安装
pip install -e .

# 或直接运行
pip install -r requirements.txt
python launch.py
```

## 依赖

- Python 3.7+
- PyQt5
- NumPy
- Matplotlib

## 许可证

开源项目，详见 LICENSE 文件。