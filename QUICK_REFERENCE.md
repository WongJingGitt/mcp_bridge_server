# MCP Bridge Server - 快速参考

## 启动命令

```bash
# 🟢 推荐: 使用启动脚本
start.bat        # Windows
./start.sh       # Linux/Mac

# 🔵 默认启动 (交互式)
python utils/mcp_bridge.py

# 🟡 自动处理端口占用
python utils/mcp_bridge.py --auto-kill-port

# 🟣 自定义端口
python utils/mcp_bridge.py --port 8080

# 🔴 完整示例
python utils/mcp_bridge.py --port 8080 --auto-kill-port --config /path/to/config.json
```

## 环境变量

```bash
# Windows
set MCP_AUTO_KILL_PORT=true
set MCP_CONFIG_PATH=C:\path\to\config.json

# Linux/Mac
export MCP_AUTO_KILL_PORT=true
export MCP_CONFIG_PATH=/path/to/config.json
```

## API 端点

### 核心功能
- `GET  /health` - 健康检查
- `GET  /tools` - 获取服务列表
- `GET  /tools?serverName=xxx` - 获取工具列表
- `POST /execute` - 执行工具

### 配置管理
- `GET  /config` - 读取配置
- `POST /config` - 更新配置并重载
- `POST /reload` - 重载所有服务

### 服务管理 🆕
- `POST /restart-server` - 重启单个服务
- `POST /shutdown-server` - 关闭单个服务
- `POST /reset-history` - 重置调用历史

## 快速示例

### 重启服务
```bash
curl -X POST http://localhost:3849/restart-server \
  -H "Content-Type: application/json" \
  -d '{"serverName": "my-service"}'
```

### 关闭服务
```bash
curl -X POST http://localhost:3849/shutdown-server \
  -H "Content-Type: application/json" \
  -d '{"serverName": "my-service"}'
```

### 重载所有服务
```bash
curl -X POST http://localhost:3849/reload
```

## 端口占用处理

### 交互式选择
```
⚠️  端口 3849 已被占用
   占用进程: python.exe (PID: 12345)

请选择操作:
  1. 结束占用进程并继续
  2. 使用其他端口
  3. 退出程序
```

### 自动处理
```bash
# 直接结束占用进程
python utils/mcp_bridge.py --auto-kill-port
```

## 配置文件位置

- **Windows**: `%APPDATA%\mcp-bridge\config\mcp-config.json`
- **macOS**: `~/Library/Application Support/mcp-bridge/config/mcp-config.json`
- **Linux**: `~/.config/mcp-bridge/config/mcp-config.json`

## 常见问题

### 端口被占用？
```bash
# 查看占用进程
netstat -ano | findstr :3849  # Windows
lsof -i :3849                  # Linux/Mac

# 结束进程
taskkill /F /PID <PID>        # Windows
kill -9 <PID>                  # Linux/Mac
```

### 配置不生效？
```bash
# 重载配置
curl -X POST http://localhost:3849/reload
```

### 单个服务出错？
```bash
# 重启有问题的服务
curl -X POST http://localhost:3849/restart-server \
  -d '{"serverName": "problem-service"}'
```

## 文档链接

- [完整文档](README.md)
- [端口管理](docs/PORT_MANAGEMENT.md)
- [服务重启](docs/RESTART_SERVER_GUIDE.md)

---

💡 **提示**: 使用 `--help` 查看所有可用参数
```bash
python utils/mcp_bridge.py --help
```
