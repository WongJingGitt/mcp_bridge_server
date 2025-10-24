# MCP 桥接服务

## 概述

MCP 桥接服务器是一个基于 Express.js 的轻量级 HTTP 服务，用于实现与 Model Context Protocol (MCP) 的本地桥接通信。它提供统一的 RESTful API 接口，使开发者能够安全地调用和管理 MCP 服务工具。

**核心特性：**
- ✅ 支持 MCP 协议的标准化通信
- ✅ 内置进程管理与自动重连机制
- ✅ 完善的工具调用监控与限流
- ✅ 跨平台支持（Windows/macOS/Linux）

**基础信息：**
- **服务端口：** `3849`
- **协议：** HTTP
- **数据格式：** JSON
- **CORS：** 已启用

## 快速开始

### 启动服务
```
# 开发环境
npm start

# 打包后（可执行文件）
./dist/mcp-bridge  # Windows: mcp-bridge.exe
```

> **注意**：
> - 配置文件自动存储在系统用户目录中，与运行位置无关
> - Windows: `%APPDATA%\\mcp-bridge\\config\\mcp-config.json`
> - macOS: `~/Library/Application Support/mcp-bridge/config/mcp-config.json`
> - Linux: `~/.config/mcp-bridge/config/mcp-config.json`
> - 配置文件不存在时会自动创建默认空配置

### 目录结构要求
```
# 系统配置目录结构（自动生成）
# Windows
C:\\Users\\<用户名>\\AppData\\Roaming\\mcp-bridge\\config\\
└── mcp-config.json

# macOS
~/Library/Application Support/mcp-bridge/config/
└── mcp-config.json

# Linux
~/.config/mcp-bridge/config/
└── mcp-config.json
```

## API 接口

### 1. 健康检查
验证服务运行状态。

**请求：**
```http
GET /health
```

**成功响应：**
```json
{
  "status": "ok",
  "timestamp": 1729820123456
}
```

### 2. 获取工具列表
获取所有已注册 MCP 工具的元数据信息。

**请求：**
```http
GET /tools
```

**响应结构：**
```json
{
  "success": true,
  "tools": [
    {
      "name": "tool_name",
      "description": "工具功能描述",
      "parameters": {
        "type": "object",
        "properties": {
          "param1": {"type": "string", "description": "参数说明"},
          "param2": {"type": "number"}
        },
        "required": ["param1"]
      },
      "serverName": "服务名称"
    }
  ]
}
```

### 3. 执行工具
调用指定 MCP 工具并获取执行结果。

**请求：**
```http
POST /execute
Content-Type: application/json
```

**请求体：**
```json
{
  "name": "tool_name",
  "arguments": {
    "param1": "value1",
    "param2": 123
  }
}
```

**响应：**
```json
{
  "success": true,
  "result": "工具执行结果数据"
}
```

**错误响应：**
```json
{
  "success": false,
  "error": "详细的错误原因",
  "errorCode": "TOOL_NOT_FOUND"
}
```

> **安全机制**：单个工具连续失败 3 次后将被临时禁用，可通过 `/reset-history` 重置

### 4. 重载配置
动态重新加载 MCP 服务器配置。

**请求：**
```http
POST /reload
Content-Type: application/json
```

**可选参数：**
```json
{
  "configPath": "/自定义/配置路径.json"
}
```

**成功响应：**
```json
{
  "success": true,
  "message": "配置已重载",
  "toolCount": 5
}
```

### 5. 更新配置文件
持久化保存新配置并立即生效。

**请求：**
```http
POST /config
Content-Type: application/json
```

**请求体：**
```json
{
  "config": {
    "mcpServers": {
      "jenkins_tools": {
        "command": "node",
        "args": ["server.js"],
        "env": {
          "TOKEN": "secure_value"
        }
      }
    }
  },
  "configPath": "./data/mcp-config.json"
}
```

### 6. 重置调用历史
清除工具调用失败计数器。

**请求：**
```http
POST /reset-history
```

**响应：**
```json
{
  "success": true,
  "message": "调用历史已重置",
  "resetCount": 3
}
```

## 配置规范

### 配置文件位置
- 默认路径：`./data/mcp-config.json`
- 必须包含 `mcpServers` 配置节点
- 目录结构需提前创建（服务不会自动创建目录）

### 配置示例
```json
{
  "mcpServers": {
    "jenkins_tools": {
      "command": "node",
      "args": ["jenkins-mcp-server.js"],
      "env": {
        "JENKINS_URL": "http://jenkins.example.com",
        "JENKINS_TOKEN": "your_secure_token"
      }
    }
  }
}
```

## 安全机制

| 机制                | 说明                              |
|---------------------|-----------------------------------|
| 调用频率限制        | 单工具连续失败 3 次后临时禁用     |
| 进程隔离            | 每个 MCP 服务独立进程运行         |
| 配置热更新          | 支持运行时动态重载配置            |
| 环境变量保护        | 敏感信息建议通过安全方式注入      |

## 开发者示例

### Python 调用示例
``python
import requests  # 需先安装: pip install requests

response = requests.post(
    'http://localhost:3849/execute',
    json={
        'name': 'get_job_status',
        'arguments': {'job_id': 'build-123'}
    }
)
print(response.json())  # 输出: {"success": true, "result": "..."}
```

### JavaScript 调用示例
```
// 使用 fetch API (现代浏览器)
const response = await fetch('/execute', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    name: 'get_job_status',
    arguments: {job_id: 'build-123'}
  })
});

const result = await response.json();
console.log(result); // { success: true, result: "..." }
```

### Node.js 调用示例
```
const axios = require('axios'); // 需先安装: npm install axios

async function callTool() {
  try {
    const response = await axios.post('http://localhost:3849/execute', {
      name: 'get_job_status',
      arguments: { job_id: 'build-123' }
    });
    console.log(response.data);
  } catch (error) {
    console.error('调用失败:', error.response?.data || error.message);
  }
}
```

## 服务日志

启动成功时显示：
```
🚀 MCP 桥接服务已启动
   地址: http://localhost:3849
   工具数量: 5

可用接口:
   GET  /health         - 健康检查
   GET  /tools          - 获取工具列表
   POST /execute        - 执行工具
   POST /reload         - 重载配置
   POST /config         - 更新配置文件
   POST /reset-history  - 重置调用历史
```

## 最佳实践

1. **配置管理**
   - 将 `data/` 目录加入版本控制忽略列表（.gitignore）
   - 敏感信息通过环境变量注入，避免硬编码

2. **部署建议**
   - 生产环境建议通过 `npm run build` 生成可执行文件
   - 使用进程管理工具（如 pm2）保障服务稳定性

3. **错误处理**
   - 客户端应实现指数退避重试机制
   - 关注 `errorCode` 字段进行针对性错误处理

---

**版本：** 1.0.0  
**最后更新：** 2025-10-24