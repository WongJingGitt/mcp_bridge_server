@echo off
chcp 65001 >nul
REM MCP Bridge Server 打包脚本 (Windows)

echo ========================================
echo MCP Bridge Server 打包工具
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python
    pause
    exit /b 1
)

REM 检查 PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [警告] 未安装 PyInstaller，正在安装...
    pip install pyinstaller
)

echo 选择打包选项:
echo.
echo   1. 单文件打包 (推荐，便于分发)
echo   2. 目录打包 (启动更快)
echo   3. 使用 spec 文件打包 (包含所有优化)
echo   4. 清理构建文件
echo   5. 退出
echo.

set /p choice="请输入选项 (1-5): "

if "%choice%"=="1" (
    echo.
    echo 正在进行单文件打包...
    echo.
    
    REM 清理旧文件
    if exist build rmdir /s /q build
    if exist dist rmdir /s /q dist
    
    REM 打包
    pyinstaller --onefile ^
        --name mcp-bridge-server ^
        --add-data "README.md;." ^
        --add-data "docs;docs" ^
        --hidden-import mcp ^
        --hidden-import mcp.client.stdio ^
        --hidden-import mcp.client.sse ^
        --hidden-import uvicorn.logging ^
        --hidden-import uvicorn.loops.auto ^
        --hidden-import uvicorn.protocols.http.auto ^
        --exclude-module tkinter ^
        --exclude-module matplotlib ^
        utils\mcp_bridge.py
    
    echo.
    echo ✓ 打包完成！
    echo 输出文件: dist\mcp-bridge-server.exe
    
) else if "%choice%"=="2" (
    echo.
    echo 正在进行目录打包...
    echo.
    
    REM 清理旧文件
    if exist build rmdir /s /q build
    if exist dist rmdir /s /q dist
    
    REM 打包
    pyinstaller --onedir ^
        --name mcp-bridge-server ^
        --add-data "README.md;." ^
        --add-data "docs;docs" ^
        --hidden-import mcp ^
        --hidden-import mcp.client.stdio ^
        --hidden-import mcp.client.sse ^
        --hidden-import uvicorn.logging ^
        --hidden-import uvicorn.loops.auto ^
        --hidden-import uvicorn.protocols.http.auto ^
        utils\mcp_bridge.py
    
    echo.
    echo ✓ 打包完成！
    echo 输出目录: dist\mcp-bridge-server\
    
) else if "%choice%"=="3" (
    echo.
    echo 使用 spec 文件打包...
    echo.
    
    REM 清理旧文件
    if exist build rmdir /s /q build
    if exist dist rmdir /s /q dist
    
    REM 打包
    pyinstaller mcp_bridge.spec
    
    echo.
    echo ✓ 打包完成！
    echo 输出文件: dist\mcp-bridge-server.exe
    
) else if "%choice%"=="4" (
    echo.
    echo 正在清理构建文件...
    
    if exist build (
        rmdir /s /q build
        echo ✓ 已删除 build 目录
    )
    
    if exist dist (
        rmdir /s /q dist
        echo ✓ 已删除 dist 目录
    )
    
    if exist *.spec (
        del *.spec
        echo ✓ 已删除临时 spec 文件
    )
    
    echo.
    echo ✓ 清理完成
    
) else if "%choice%"=="5" (
    exit /b 0
) else (
    echo.
    echo [错误] 无效的选项
)

echo.
echo ========================================
echo.

REM 询问是否测试
if exist dist\mcp-bridge-server.exe (
    set /p test="是否测试打包后的程序? (y/n): "
    if /i "%test%"=="y" (
        echo.
        echo 正在启动程序...
        echo 按 Ctrl+C 停止测试
        echo.
        dist\mcp-bridge-server.exe --help
    )
)

pause
