@echo off
chcp 65001 >nul
echo ========================================
echo DST Reader - 打包为便携式EXE文件
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] 检查并安装依赖...
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo 正在安装PyQt5...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

REM 以开发模式安装dstreader包，确保PyInstaller能找到它
echo 安装dstreader包（开发模式）...
pip install -e . >nul 2>&1
if errorlevel 1 (
    echo 警告: 无法以开发模式安装包，将尝试其他方法...
)

REM 检查PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo 正在安装PyInstaller...
    pip install pyinstaller>=5.0.0
    if errorlevel 1 (
        echo [错误] PyInstaller安装失败
        pause
        exit /b 1
    )
)

echo [2/4] 清理之前的构建文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo [3/4] 开始打包...
echo 这可能需要几分钟时间，请耐心等待...
echo.

REM 注意：使用.spec文件时不能使用--paths参数，路径已在spec文件中配置
pyinstaller --clean dstreader.spec

if errorlevel 1 (
    echo.
    echo [错误] 打包失败，请检查上面的错误信息
    pause
    exit /b 1
)

echo.
echo [4/4] 打包完成！
echo.
echo EXE文件位置: dist\DSTReader.exe
echo.
echo 提示：
echo - 可以将 DSTReader.exe 复制到任何位置使用
echo - 首次运行可能需要几秒钟加载
echo - 如果遇到问题，请检查dist文件夹中的完整文件
echo.

pause
