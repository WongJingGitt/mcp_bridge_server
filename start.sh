#!/bin/bash
# MCP Bridge Server 启动脚本 (Linux/Mac)

echo "========================================"
echo "MCP Bridge Server 启动器"
echo "========================================"
echo

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

echo "选择启动模式:"
echo
echo "  1. 默认启动 (交互式，端口 3849)"
echo "  2. 自动结束占用进程 (端口 3849)"
echo "  3. 自定义端口启动"
echo "  4. 查看帮助"
echo "  5. 退出"
echo

read -p "请输入选项 (1-5): " choice

case $choice in
    1)
        echo
        echo "正在以交互模式启动..."
        python3 utils/mcp_bridge.py
        ;;
    2)
        echo
        echo "正在启动并自动处理端口占用..."
        python3 utils/mcp_bridge.py --auto-kill-port
        ;;
    3)
        echo
        read -p "请输入端口号: " port
        read -p "是否自动结束占用进程? (y/n): " auto_kill
        
        if [[ "$auto_kill" == "y" || "$auto_kill" == "Y" ]]; then
            python3 utils/mcp_bridge.py --port $port --auto-kill-port
        else
            python3 utils/mcp_bridge.py --port $port
        fi
        ;;
    4)
        echo
        python3 utils/mcp_bridge.py --help
        echo
        read -p "按回车键继续..."
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
