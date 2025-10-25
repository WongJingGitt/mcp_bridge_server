#!/bin/bash
# MCP Bridge Server 打包脚本 (Linux/Mac)

echo "========================================"
echo "MCP Bridge Server 打包工具"
echo "========================================"
echo

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3"
    exit 1
fi

# 检查 PyInstaller
if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo "[警告] 未安装 PyInstaller，正在安装..."
    pip3 install pyinstaller
fi

echo "选择打包选项:"
echo
echo "  1. 单文件打包 (推荐，便于分发)"
echo "  2. 目录打包 (启动更快)"
echo "  3. 使用 spec 文件打包 (包含所有优化)"
echo "  4. 清理构建文件"
echo "  5. 退出"
echo

read -p "请输入选项 (1-5): " choice

case $choice in
    1)
        echo
        echo "正在进行单文件打包..."
        echo
        
        # 清理旧文件
        rm -rf build dist
        
        # 打包
        pyinstaller --onefile \
            --name mcp-bridge-server \
            --add-data "README.md:." \
            --add-data "docs:docs" \
            --hidden-import mcp \
            --hidden-import mcp.client.stdio \
            --hidden-import mcp.client.sse \
            --hidden-import uvicorn.logging \
            --hidden-import uvicorn.loops.auto \
            --hidden-import uvicorn.protocols.http.auto \
            --exclude-module tkinter \
            --exclude-module matplotlib \
            utils/mcp_bridge.py
        
        echo
        echo "✓ 打包完成！"
        echo "输出文件: dist/mcp-bridge-server"
        
        # 添加执行权限
        chmod +x dist/mcp-bridge-server
        
        # 生成版本信息
        VERSION="v1.0.0"
        PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
        ARCH=$(uname -m)
        
        if [ "$ARCH" = "x86_64" ]; then
            ARCH="x64"
        elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
            ARCH="arm64"
        fi
        
        FINAL_NAME="mcp-bridge-server-${VERSION}-${PLATFORM}-${ARCH}"
        
        echo
        read -p "是否重命名为发布版本名称? (y/n): " rename
        if [[ "$rename" == "y" || "$rename" == "Y" ]]; then
            mv dist/mcp-bridge-server "dist/${FINAL_NAME}"
            echo "✓ 已重命名为: ${FINAL_NAME}"
            
            # 生成校验和
            cd dist
            sha256sum "${FINAL_NAME}" > SHA256SUMS.txt
            echo "✓ 已生成 SHA256 校验和"
            cd ..
        fi
        ;;
        
    2)
        echo
        echo "正在进行目录打包..."
        echo
        
        # 清理旧文件
        rm -rf build dist
        
        # 打包
        pyinstaller --onedir \
            --name mcp-bridge-server \
            --add-data "README.md:." \
            --add-data "docs:docs" \
            --hidden-import mcp \
            --hidden-import mcp.client.stdio \
            --hidden-import mcp.client.sse \
            --hidden-import uvicorn.logging \
            --hidden-import uvicorn.loops.auto \
            --hidden-import uvicorn.protocols.http.auto \
            utils/mcp_bridge.py
        
        echo
        echo "✓ 打包完成！"
        echo "输出目录: dist/mcp-bridge-server/"
        
        chmod +x dist/mcp-bridge-server/mcp-bridge-server
        ;;
        
    3)
        echo
        echo "使用 spec 文件打包..."
        echo
        
        # 清理旧文件
        rm -rf build dist
        
        # 打包
        pyinstaller mcp_bridge.spec
        
        echo
        echo "✓ 打包完成！"
        echo "输出文件: dist/mcp-bridge-server"
        
        chmod +x dist/mcp-bridge-server
        ;;
        
    4)
        echo
        echo "正在清理构建文件..."
        
        if [ -d "build" ]; then
            rm -rf build
            echo "✓ 已删除 build 目录"
        fi
        
        if [ -d "dist" ]; then
            rm -rf dist
            echo "✓ 已删除 dist 目录"
        fi
        
        if [ -f "mcp-bridge-server.spec" ] && [ ! -f "mcp_bridge.spec" ]; then
            rm -f mcp-bridge-server.spec
            echo "✓ 已删除临时 spec 文件"
        fi
        
        echo
        echo "✓ 清理完成"
        ;;
        
    5)
        exit 0
        ;;
        
    *)
        echo
        echo "[错误] 无效的选项"
        exit 1
        ;;
esac

echo
echo "========================================"
echo

# 询问是否测试
if [ -f "dist/mcp-bridge-server" ]; then
    read -p "是否测试打包后的程序? (y/n): " test
    if [[ "$test" == "y" || "$test" == "Y" ]]; then
        echo
        echo "正在启动程序..."
        echo "按 Ctrl+C 停止测试"
        echo
        ./dist/mcp-bridge-server --help
    fi
fi
