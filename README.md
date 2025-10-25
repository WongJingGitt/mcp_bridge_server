# MCP Bridge Server

**为 DeepSeek 网页端提供 MCP 工具能力的本地桥接服务**

本项目是一个轻量级的本地服务器，旨在作为浏览器插件的后端核心，为原生的 DeepSeek 网页端注入强大的模型上下文协议 (Model Context Protocol, MCP) 工具调用能力。

它通过一个标准的 HTTP API 与浏览器插件通信，负责在后台动态地启动、管理和调用一个或多个 MCP 服务进程，并将它们的能力统一暴露出去。

## ✨ 核心特性

*   **统一管理**：通过简单的 JSON 配置，即可同时管理和运行多个不同的 MCP 服务。
*   **分层式工具发现**：创新的两阶段工具发现机制。模型首先获取服务（工具集）的概览，再按需查询具体工具详情，极大地节省了宝贵的上下文（Token）空间。
*   **动态配置与热重载**：无需重启服务，即可通过 API 更新配置文件并重新加载所有后端 MCP 服务。
*   **跨平台兼容**：自动检测 Windows, macOS, Linux 等主流操作系统，并将配置文件存储在标准的用户数据目录下。
*   **简单容错**：内置简单的工具调用重试和熔断机制，当某个工具连续调用失败时会暂时阻止调用，提高稳定性。
*   **零依赖运行**：可被打包为单一的可执行文件，用户下载后无需安装任何依赖（如 Node.js）即可直接运行。

## ⚙️ 工作流程

整个系统的工作流程非常清晰：

```
[浏览器插件 (DeepSeek 增强)] <--- HTTP API ---> [MCP Bridge Server (本项目)] <--- Stdio ---> [具体的 MCP 服务进程 1, 2, 3...]
```

1.  **插件**负责拦截和改写 DeepSeek 网页端的网络请求，并与用户界面交互。
2.  **MCP Bridge Server** 负责管理所有后端工具的生命周期，并提供统一的 API 接口。
3.  **MCP 服务进程** 是实现了 MCP 协议、提供具体工具能力的独立程序。

## 🚀 快速上手 (用户指南)

后续本项目会打包成可执行文件，您只需要按照以下步骤操作即可。

### 1. 下载

从本项目的 GitHub Releases 页面下载对应您操作系统的最新版本（例如 `mcp-bridge-server-win-x64.exe` 或 `mcp-bridge-server-macos-arm64`）。

### 2. 启动服务

#### 方式 1: 使用启动脚本（推荐）

**Windows 用户**:
```bash
# 双击运行或在命令行执行
start.bat
```

**Linux/Mac 用户**:
```bash
# 赋予执行权限（首次）
chmod +x start.sh

# 运行
./start.sh
```

启动脚本会提供友好的菜单选项：
- 默认启动（交互式）
- 自动处理端口占用
- 自定义端口
- 查看帮助

#### 方式 2: 直接运行（开发者）

```bash
# 默认启动（端口 3849，交互式处理端口占用）
python utils/mcp_bridge.py

# 自动结束占用进程并启动
python utils/mcp_bridge.py --auto-kill-port

# 使用自定义端口
python utils/mcp_bridge.py --port 8080

# 组合使用
python utils/mcp_bridge.py --port 8080 --auto-kill-port --config /path/to/config.json
```

#### 端口占用处理

首次运行时，程序会自动检查端口是否被占用：

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

**命令行参数**:
- `--port PORT`: 指定端口号（默认 3849）
- `--auto-kill-port`: 自动结束占用端口的进程
- `--config PATH`: 指定配置文件路径

**环境变量**:
- `MCP_AUTO_KILL_PORT=true`: 自动处理端口占用
- `MCP_CONFIG_PATH=/path/to/config`: 配置文件路径

详细说明请参考 [端口管理文档](docs/PORT_MANAGEMENT.md)。

### 3. 首次运行

直接双击运行该可执行文件。此时会弹出一个命令行窗口，并显示服务正在启动。

**最重要的一步**：首次成功运行后，程序会自动在您的系统用户目录下创建一个默认的配置文件 `mcp-config.json`。

### 4. 配置服务

这是使用本项目的**核心步骤**。您需要告诉桥接服务去哪里找到并启动您自己的 MCP 工具。

1.  **找到配置文件**：
    *   **Windows**: `%APPDATA%\mcp-bridge\config\mcp-config.json`
        (可以直接在资源管理器的地址栏输入 `%APPDATA%` 并回车)
    *   **macOS**: `~/Library/Application Support/mcp-bridge/config/mcp-config.json`
    *   **Linux**: `~/.config/mcp-bridge/config/mcp-config.json`

2.  **编辑配置文件**：
    用任何文本编辑器（如 VS Code, Sublime Text, 记事本）打开 `mcp-config.json`。您会看到如下结构：

    ```json
    {
      "mcpServers": {
        "example_service": {
          "command": "path/to/your/mcp/server/executable",
          "args": ["--port", "8080"],
          "description": "这是一个示例服务，请替换成你自己的配置。它能...",
          "env": {}
        }
      }
    }
    ```

    请根据您的实际情况修改它。例如，如果您有一个用 Python 编写的天气服务，您的配置可能如下：

    ```json
    {
      "mcpServers": {
        "weather_service": {
          "command": "python",
          "args": ["/path/to/your/weather_server.py"],
          "description": "一个提供实时天气信息和未来天气预报的服务。"
        },
        "calculator_service": {
          "command": "/path/to/your/calculator_app.exe",
          "args": [],
          "description": "一个能够执行复杂数学计算和表达式求值的服务。"
        }
      }
    }
    ```

    **字段说明**:
    *   `"weather_service"`: 服务的唯一名称，您可自定义，插件将通过此名称识别服务。
    *   `"command"`: **[必需]** 用于启动 MCP 服务的命令。可以是 `python`, `node` 等解释器，也可以是可执行文件的完整路径。
    *   `"args"`: **[可选]** 传递给命令的参数列表，每个参数都是一个独立的字符串。
    *   `"description"`: **[必需]** 对这个服务的**高级描述**。这段描述会首先被模型看到，用于它判断是否需要使用此服务下的工具。请务必写得清晰准确！
    *   `"env"`: **[可选]** 为该服务进程设置额外的环境变量。

### 5. 重新运行或重载

配置完成后，保存文件。有两种方式应用新配置：

**方式 1: 重启服务**
- 关闭当前运行的服务（Ctrl+C）
- 重新运行启动脚本或命令

**方式 2: 热重载（推荐）**
```bash
# 使用 API 重载配置
curl -X POST http://localhost:3849/reload

# 或重启单个服务
curl -X POST http://localhost:3849/restart-server \
  -H "Content-Type: application/json" \
  -d '{"serverName": "weather_service"}'
```

如果配置无误，您将在命令行窗口看到类似 "✓ 服务器 xxx 初始化成功" 的日志。

现在，您的桥接服务已经准备就绪，可以与浏览器插件进行交互了！

## 📚 API 接口文档

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
    > **错误处理增强**: 从 v1.1 开始,执行失败时会返回详细的错误信息,包括错误类型和完整的 Python 调用堆栈,帮助快速定位问题。浏览器扩展会将这些信息展示给 AI 模型,以便模型分析错误原因并尝试修正。

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

### Node.js 版本（如有）

1.  **环境**: 确保您已安装 [Node.js](https://nodejs.org/) (建议 v18 或更高版本)。
2.  **克隆仓库**: `git clone <repository_url>`
3.  **安装依赖**: `cd mcp-bridge-server && npm install`
4.  **运行**: `node mcp-bridge-server.js`

## 📄 许可证

本项目采用 [MIT](https://opensource.org/licenses/MIT) 许可证。