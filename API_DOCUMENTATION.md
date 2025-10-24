# MCP 桥接服务器 API 文档

## 概述

MCP 桥接服务器是一个基于 Express.js 的 HTTP 服务，用于管理和调用 MCP (Model Context Protocol) 服务器工具。它提供了统一的 RESTful API 接口来执行各种 MCP 工具操作。

**基础信息：**
- **服务端口：** `3849`
- **协议：** HTTP/HTTPS
- **数据格式：** JSON
- **CORS：** 已启用

## 快速开始

### 启动服务
```bash
node mcp-bridge-server.js
```

### 环境变量
- `MCP_CONFIG_PATH` - MCP 配置文件路径（默认：`./mcp-config.json`）

## API 接口

### 1. 健康检查
检查服务运行状态。

**请求：**
```http
GET /health
```

**响应：**
```json
{
  "status": "ok",
  "timestamp": 1698067200000
}
```

### 2. 获取工具列表
获取所有可用的 MCP 工具信息。

**请求：**
```http
GET /tools
```

**响应：**
```json
{
  "success": true,
  "tools": [
    {
      "name": "tool_name",
      "description": "工具描述",
      "parameters": {
        "type": "object",
        "properties": {
          "param1": {"type": "string"},
          "param2": {"type": "number"}
        }
      },
      "serverName": "server_name"
    }
  ]
}
```

### 3. 执行工具
执行指定的 MCP 工具。

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
  "result": "工具执行结果"
}
```

**错误响应：**
```json
{
  "success": false,
  "error": "错误信息"
}
```

### 4. 重载配置
重新加载 MCP 服务器配置。

**请求：**
```http
POST /reload
Content-Type: application/json
```

**请求体（可选）：**
```json
{
  "configPath": "/path/to/config.json"
}
```

**响应：**
```json
{
  "success": true,
  "message": "配置已重载"
}
```

### 5. 更新配置文件
更新并应用新的配置文件。

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
      "server1": {
        "command": "node",
        "args": ["server1.js"],
        "env": {}
      }
    }
  },
  "configPath": "./mcp-config.json"
}
```

**响应：**
```json
{
  "success": true,
  "message": "配置已保存并重载"
}
```

### 6. 重置调用历史
重置工具调用计数器。

**请求：**
```http
POST /reset-history
```

**响应：**
```json
{
  "success": true,
  "message": "调用历史已重置"
}
```

## 配置格式

### MCP 配置文件示例
```json
{
  "mcpServers": {
    "jenkins_tools": {
      "command": "node",
      "args": ["jenkins-mcp-server.js"],
      "env": {
        "JENKINS_URL": "http://jenkins.example.com",
        "JENKINS_TOKEN": "your_token"
      }
    },
    "database_tools": {
      "command": "python",
      "args": ["database-mcp-server.py"],
      "env": {
        "DB_HOST": "localhost",
        "DB_PORT": "5432"
      }
    }
  }
}
```

## 错误处理

所有 API 接口都遵循统一的错误响应格式：

```json
{
  "success": false,
  "error": "详细的错误信息"
}
```

**常见错误码：**
- `400` - 请求参数错误
- `500` - 服务器内部错误

## 安全特性

### 调用限制
- 每个工具在连续失败 3 次后会被暂时禁用
- 成功调用后会重置失败计数器
- 可通过 `/reset-history` 接口手动重置

### 进程管理
- 自动管理 MCP 服务器进程生命周期
- 支持优雅关闭和重启
- 进程错误监控和日志记录

## 使用示例

### Python 客户端示例
```python
import requests

BASE_URL = "http://localhost:3849"

# 获取工具列表
response = requests.get(f"{BASE_URL}/tools")
tools = response.json()["tools"]

# 执行工具
result = requests.post(f"{BASE_URL}/execute", json={
    "name": "get_job_names_and_description",
    "arguments": {}
})

print(result.json())
```

### JavaScript 客户端示例
```javascript
const BASE_URL = 'http://localhost:3849';

// 获取工具列表
const tools = await fetch(`${BASE_URL}/tools`).then(r => r.json());

// 执行工具
const result = await fetch(`${BASE_URL}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        name: 'get_date',
        arguments: {}
    })
}).then(r => r.json());
```

## 日志信息

服务启动时会显示以下信息：
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

## 注意事项

1. **配置文件路径**：默认使用 `./mcp-config.json`，可通过环境变量 `MCP_CONFIG_PATH` 修改
2. **工具调用**：确保工具名称和参数格式正确
3. **进程管理**：服务关闭时会自动清理所有 MCP 服务器进程
4. **错误处理**：建议在客户端实现重试机制处理临时错误

---

**版本：** 1.0.0  
**最后更新：** 2025-10-23