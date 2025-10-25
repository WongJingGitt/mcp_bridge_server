# 🌉 MCP Bridge Server

<div align="center">

**为 MCP Bridge 浏览器扩展提供强大的本地工具调用能力**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-Protocol-blue.svg)](https://modelcontextprotocol.io)
[![GitHub](https://img.shields.io/badge/GitHub-WongJingGitt-blue.svg)](https://github.com/WongJingGitt)

[快速开始](#-快速开始) • [API 文档](#-api-文档) • [配置指南](#-配置指南) • [开发者指南](#-开发者指南)

</div>

---

## 📖 简介

MCP Bridge Server 是 [MCP Bridge 浏览器扩展](https://github.com/WongJingGitt/mcp_bridge) 的本地桥接服务，负责管理和调用遵循 **[MCP (Model Context Protocol)](https://modelcontextprotocol.io)** 协议的工具服务。

通过标准的 HTTP REST API 与浏览器扩展通信，本服务在后台动态启动、管理和调用一个或多个 MCP 服务进程，并将它们的能力统一暴露给网页版 AI 平台（DeepSeek、通义千问、腾讯元宝、豆包等）。

### 架构示意图

```
┌─────────────────┐                    ┌──────────────────────┐
│  浏览器扩展       │ ◄── HTTP/REST ──►  │  MCP Bridge Server   │
│  (前端界面)       │                    │  (本项目)             │
└─────────────────┘                    └──────────┬───────────┘
                                                  │ MCP Protocol
                                                  │ (stdio)
                                       ┌──────────▼───────────┐
                                       │  MCP 工具服务进程      │
                                       │  • filesystem        │
                                       │  • git               │
                                       │  • database          │
                                       │  • ...               │
                                       └──────────────────────┘
```

---

## ✨ 核心特性

### 🎯 核心能力

- **统一管理** - 通过简单的 JSON 配置同时管理多个 MCP 服务
- **分层工具发现** - 两阶段发现机制：先获取服务概览，再按需查询工具详情，节省上下文
- **动态配置** - 支持热重载，无需重启服务即可应用新配置
- **跨平台兼容** - 自动适配 Windows/macOS/Linux，配置存储在标准用户目录

### 🛡️ 高级特性

- **零依赖运行** - 可打包为单一可执行文件，无需安装 Python 环境
- **智能端口管理** - 自动检测端口占用，提供交互式处理方案
- **服务热重启** - 支持单独重启某个服务，不影响其他服务
- **错误追踪** - 返回详细的错误堆栈信息，帮助 AI 自主诊断和修正
- **熔断保护** - 内置重试和熔断机制，防止故障服务影响整体稳定性

---

## 🚀 快速开始

### 前置要求

- **运行环境**:
    - 使用可执行文件：无需任何依赖
    - 从源码运行：Python 3.8+

### 1️⃣ 下载服务

#### 方式一：下载可执行文件（推荐）

从 [Releases](https://github.com/WongJingGitt/mcp_bridge_server/releases) 下载对应平台的可执行文件：

- **Windows**: `mcp-bridge-server.exe`
- **macOS**: `mcp-bridge-server-macos`
- **Linux**: `mcp-bridge-server-linux`

#### 方式二：克隆源码

```bash
git clone https://github.com/WongJingGitt/mcp_bridge_server.git
cd mcp_bridge_server
pip install -r requirements.txt
```

### 2️⃣ 启动服务

#### 使用启动脚本（推荐）

<details>
<summary><b>Windows 用户</b></summary>

```bash
# 双击运行或在命令行执行
start.bat
```

启动脚本提供友好的交互式菜单：
```
MCP Bridge Server v1.0.0
请选择启动方式:
  1. 默认启动 (端口 3849, 交互式处理端口占用)
  2. 自动处理端口占用 (强制结束占用进程)
  3. 使用自定义端口
  4. 查看帮助
  5. 退出
```
</details>

<details>
<summary><b>Linux/Mac 用户</b></summary>

```bash
# 赋予执行权限（首次）
chmod +x start.sh

# 运行
./start.sh
```
</details>

#### 直接运行（开发者）

```bash
# 默认启动（端口 3849）
python utils/mcp_bridge.py

# 自动处理端口占用
python utils/mcp_bridge.py --auto-kill-port

# 使用自定义端口
python utils/mcp_bridge.py --port 8080

# 组合参数
python utils/mcp_bridge.py --port 8080 --auto-kill-port
```

**命令行参数**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--port PORT` | 指定端口号 | 3849 |
| `--auto-kill-port` | 自动结束占用端口的进程 | false |
| `--config PATH` | 指定配置文件路径 | 系统默认位置 |

**环境变量**：

| 变量 | 说明 |
|------|------|
| `MCP_AUTO_KILL_PORT=true` | 自动处理端口占用 |
| `MCP_CONFIG_PATH=/path/to/config` | 配置文件路径 |

#### 端口占用处理

首次运行时自动检测端口占用：

```
MCP Bridge Server v1.0.0
正在检查端口 3849...

⚠️  端口 3849 已被占用
   占用进程: python.exe (PID: 12345)

请选择操作:
  1. 结束占用进程并继续
  2. 使用其他端口
  3. 退出程序

请输入选项 (1/2/3): 
```

详细说明请参考 [端口管理文档](docs/PORT_MANAGEMENT.md)。

### 3️⃣ 首次运行

服务启动后，会在系统用户目录自动创建默认配置文件：

- **Windows**: `%APPDATA%\mcp-bridge\config\mcp-config.json`
- **macOS**: `~/Library/Application Support/mcp-bridge/config/mcp-config.json`
- **Linux**: `~/.config/mcp-bridge/config/mcp-config.json`

成功启动后会显示：

```
✓ 配置文件已创建: C:\Users\YourName\AppData\Roaming\mcp-bridge\config\mcp-config.json
✓ MCP Bridge Server 正在运行于 http://localhost:3849
✓ 服务已就绪，等待浏览器扩展连接...
```

---

## ⚙️ 配置指南

这是使用本项目的**核心步骤**。您需要告诉桥接服务去哪里找到并启动您的 MCP 工具。

### 配置文件位置

首次运行后自动创建在：

| 操作系统 | 路径 | 快速访问 |
|---------|------|----------|
| **Windows** | `%APPDATA%\mcp-bridge\config\mcp-config.json` | 在资源管理器地址栏输入 `%APPDATA%` |
| **macOS** | `~/Library/Application Support/mcp-bridge/config/mcp-config.json` | Finder → 前往 → 前往文件夹 |
| **Linux** | `~/.config/mcp-bridge/config/mcp-config.json` | 终端 `cd ~/.config/mcp-bridge/config` |

### 配置文件结构

打开 `mcp-config.json`，您会看到默认结构：

```json
{
  "mcpServers": {
    "example_service": {
      "enabled": true,
      "command": "path/to/your/mcp/server/executable",
      "args": ["--port", "8080"],
      "description": "这是一个示例服务，请替换成你自己的配置",
      "env": {}
    }
  }
}
```

### 配置示例

#### 示例 1：文件系统工具

```json
{
  "mcpServers": {
    "filesystem": {
      "enabled": true,
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:\\Users\\YourName\\Documents"],
      "description": "提供文件系统访问能力，可以读写指定目录下的文件"
    }
  }
}
```

#### 示例 2：Git 仓库管理

```json
{
  "mcpServers": {
    "git": {
      "enabled": true,
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "C:\\myrepo"],
      "description": "管理 Git 仓库，查看提交历史、分支、差异等"
    }
  }
}
```

#### 示例 3：多服务配置

```json
{
  "mcpServers": {
    "filesystem": {
      "enabled": true,
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "D:\\data"],
      "description": "文件系统访问工具"
    },
    "weather": {
      "enabled": true,
      "command": "python",
      "args": ["C:\\tools\\weather_server.py"],
      "description": "提供实时天气信息和未来天气预报",
      "env": {
        "API_KEY": "your_api_key_here"
      }
    },
    "calculator": {
      "enabled": false,
      "command": "C:\\tools\\calculator.exe",
      "args": [],
      "description": "执行复杂数学计算和表达式求值"
    }
  }
}
```

### 字段说明

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| **服务名称** (如 `"filesystem"`) | ✅ | string | 服务的唯一标识，浏览器扩展通过此名称识别服务 |
| `enabled` | ❌ | boolean | 是否启用该服务（默认 true） |
| `command` | ✅ | string | 启动命令（`python`, `node`, `npx`, 可执行文件路径等） |
| `args` | ❌ | array | 传递给命令的参数列表，每个参数是独立的字符串 |
| `description` | ✅ | string | **重要！** 服务的功能描述，AI 模型根据此判断是否使用该服务，请写得清晰准确 |
| `env` | ❌ | object | 环境变量键值对，为该服务进程设置额外的环境变量 |

### 应用新配置

配置修改后，有两种方式应用：

#### 方式 1：重启服务

```bash
# 停止服务 (Ctrl+C)
# 重新运行启动脚本
./start.sh  # 或 start.bat
```

#### 方式 2：热重载（推荐）

```bash
# 重载所有服务
curl -X POST http://localhost:3849/reload

# 或使用浏览器扩展的设置页面
# Options → 服务配置 → 保存并重载服务
```

#### 方式 3：单独重启某个服务

```bash
curl -X POST http://localhost:3849/restart-server \
  -H "Content-Type: application/json" \
  -d '{"serverName": "filesystem"}'
```

详细说明请参考 [服务重启指南](docs/RESTART_SERVER_GUIDE.md)。

### 验证配置

配置成功后，在命令行窗口应该看到：

```
✓ 服务器 filesystem 初始化成功 (5 个工具)
✓ 服务器 weather 初始化成功 (3 个工具)
✗ 服务器 calculator 已禁用
```

也可以通过 API 验证：

```bash
# 查看所有服务
curl http://localhost:3849/tools

# 查看特定服务的工具
curl http://localhost:3849/tools?serverName=filesystem
```

---

服务启动后，默认监听本地的 `3849` 端口（可通过 `--port` 参数修改）。

### 核心接口

#### `GET /health`
*   **功能**: 健康检查。
*   **返回**: `{ "status": "ok", "timestamp": 1678886400000 }`

#### `GET /tools`
*   **功能**: **(第一层发现)** 获取所有已加载**服务**的列表及其描述。
*   **返回**:
    ```json
    {
      "success": true,
      "services": [
        { "name": "weather_service", "description": "..." },
        { "name": "calculator_service", "description": "..." }
      ]
    }
    ```

#### `GET /tools?serverName=<name>`
*   **功能**: **(第二层发现)** 根据服务名称，获取该服务下的所有具体**工具**的详细信息。
*   **参数**: `serverName` - 您在配置文件中定义的服务名称。
*   **返回**:
    ```json
    {
      "success": true,
      "tools": [
        {
          "name": "get_current_weather",
          "description": "获取指定城市的当前天气",
          "parameters": { /* JSON Schema */ },
          "serverName": "weather_service"
        }
      ]
    }
    ```

#### `POST /execute`
*   **功能**: 执行一个指定的工具。
*   **请求体**: `{ "name": "tool_name", "arguments": { "param": "value" } }`
*   **成功返回**: `{ "success": true, "result": [...] }`
*   **错误返回**:
    ```json
    {
      "detail": {
        "error": "错误消息",
        "type": "ErrorType",
        "traceback": "完整的 Python 调用堆栈"
      }
    }
    ```
    > **错误处理增强**: 执行失败时会返回详细的错误信息,包括错误类型和完整的 Python 调用堆栈,帮助快速定位问题。浏览器扩展会将这些信息展示给 AI 模型,以便模型分析错误原因并尝试修正。

#### `POST /reload`
*   **功能**: 重新加载并初始化配置文件中的所有服务。当您修改了 `mcp-config.json` 后，调用此接口可使配置生效，无需重启主服务。
*   **返回**: `{ "success": true, "message": "配置已重载" }`

#### `POST /config`
*   **功能**: 直接通过 API 更新 `mcp-config.json` 文件的内容，并自动执行重载。
*   **请求体**: `{ "config": { "mcpServers": { ... } } }`
*   **返回**: `{ "success": true, "message": "配置已保存并重载" }`

### 服务管理接口

#### `POST /restart-server`
*   **功能**: 重启指定的单个服务，而不影响其他服务。
*   **请求体**:
    ```json
    {
      "serverName": "weather_service",
      "config": { /* 可选，提供新配置 */ }
    }
    ```
*   **返回**: `{ "success": true, "message": "服务 xxx 已重启", "toolCount": 5 }`
*   **详细文档**: 参见 [服务重启指南](docs/RESTART_SERVER_GUIDE.md)

#### `POST /shutdown-server`
*   **功能**: 关闭指定的服务。
*   **请求体**: `{ "serverName": "weather_service" }`
*   **返回**: `{ "success": true, "message": "服务 xxx 已关闭" }`

#### `POST /reset-history`
*   **功能**: 重置所有工具的失败调用计数器。
*   **返回**: `{ "success": true, "message": "调用历史已重置" }`

---

## � 文档

- [端口管理指南](docs/PORT_MANAGEMENT.md) - 端口检测和处理
- [服务重启指南](docs/RESTART_SERVER_GUIDE.md) - 单独重启服务功能

## �🔧 开发者指南 (从源码运行)

如果您想修改源码或从源码运行：

### Python 版本

1.  **环境要求**: Python 3.8+
2.  **克隆仓库**: `git clone <repository_url>`
3.  **安装依赖**:
    ```bash
    cd mcp-bridge-server
    pip install -r requirements.txt
    ```
4.  **运行**:
    ```bash
    # 默认启动
    python utils/mcp_bridge.py
    
    # 使用启动脚本
    ./start.sh  # Linux/Mac
    start.bat   # Windows
    ```

## 📄 许可证

本项目采用 [MIT](https://opensource.org/licenses/MIT) 许可证。