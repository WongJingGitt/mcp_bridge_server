@echo off
chcp 65001 >nul
REM MCP Bridge Server 启动脚本 (Windows)

echo ========================================
echo MCP Bridge Server 启动器
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo 选择启动模式:
echo.
echo   1. 默认启动 (交互式，端口 3849)
echo   2. 自动结束占用进程 (端口 3849)
echo   3. 自定义端口启动
echo   4. 查看帮助
echo   5. 退出
echo.

set /p choice="请输入选项 (1-5): "

if "%choice%"=="1" (
    echo.
    echo 正在以交互模式启动...
    python utils\mcp_bridge.py
) else if "%choice%"=="2" (
    echo.
    echo 正在启动并自动处理端口占用...
    python utils\mcp_bridge.py --auto-kill-port
) else if "%choice%"=="3" (
    echo.
    set /p port="请输入端口号: "
    set /p auto_kill="是否自动结束占用进程? (y/n): "
    
    if /i "%auto_kill%"=="y" (
        python utils\mcp_bridge.py --port %port% --auto-kill-port
    ) else (
        python utils\mcp_bridge.py --port %port%
    )
) else if "%choice%"=="4" (
    echo.
    python utils\mcp_bridge.py --help
    echo.
    pause
    goto :eof
) else if "%choice%"=="5" (
    exit /b 0
) else (
    echo.
    echo [错误] 无效的选项
    pause
    exit /b 1
)

pause
