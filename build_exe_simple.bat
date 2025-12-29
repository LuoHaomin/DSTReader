@echo off
chcp 65001 >nul
echo ========================================
echo DST Reader - 简化打包脚本
echo ========================================
echo.

REM 清理
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo 开始打包（使用--onefile模式）...
echo.

REM 使用--onefile模式，明确指定路径
pyinstaller --clean ^
    --name=DSTReader ^
    --onefile ^
    --windowed ^
    --paths=src ^
    --hidden-import=dstreader ^
    --hidden-import=dstreader.parser ^
    --hidden-import=dstreader.models ^
    --hidden-import=dstreader.visualizer ^
    --hidden-import=dstreader.gui ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtGui ^
    --hidden-import=PyQt5.QtWidgets ^
    --hidden-import=matplotlib.backends.backend_qt5agg ^
    launch.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo 打包完成！EXE文件位置: dist\DSTReader.exe
pause

