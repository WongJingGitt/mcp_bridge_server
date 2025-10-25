# 单独重启服务功能使用指南

## 功能概述

MCP Bridge Server 现在支持单独重启或关闭指定的 MCP 服务，而不需要重启所有服务。这在以下场景非常有用：

- 🔄 某个服务出现问题需要重启
- ➕ 添加了新的服务配置需要加载
- 🔧 修改了某个服务的配置需要应用
- 🛑 暂时关闭某个不需要的服务

## 新增 API 端点

### 1. 重启指定服务

**端点**: `POST /restart-server`

**请求体**:
```json
{
  "serverName": "服务名称",
  "config": {  // 可选，如果提供则使用新配置
    "enabled": true,
    "command": "path/to/command",
    "args": ["arg1", "arg2"],
    "env": {},
    "description": "服务描述"
  }
}
```

**响应**:
```json
{
  "success": true,
  "message": "服务 xxx 已重启",
  "toolCount": 10
}
```

**示例**:
```bash
# 使用原配置重启
curl -X POST http://localhost:3849/restart-server \
  -H "Content-Type: application/json" \
  -d '{"serverName": "Knowledge Graph Memory Server"}'

# 使用新配置重启
curl -X POST http://localhost:3849/restart-server \
  -H "Content-Type: application/json" \
  -d '{
    "serverName": "filesystem",
    "config": {
      "enabled": true,
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:\\NewPath"],
      "env": {}
    }
  }'
```

### 2. 关闭指定服务

**端点**: `POST /shutdown-server`

**请求体**:
```json
{
  "serverName": "服务名称"
}
```

**响应**:
```json
{
  "success": true,
  "message": "服务 xxx 已关闭"
}
```

**示例**:
```bash
curl -X POST http://localhost:3849/shutdown-server \
  -H "Content-Type: application/json" \
  -d '{"serverName": "12306-mcp"}'
```

## 使用场景

### 场景 1: 服务出现异常需要重启

```python
import requests

# 重启有问题的服务
response = requests.post(
    "http://localhost:3849/restart-server",
    json={"serverName": "Knowledge Graph Memory Server"}
)

if response.status_code == 200:
    print("服务重启成功")
```

### 场景 2: 修改配置后重新加载单个服务

```python
import requests

# 读取当前配置
config_response = requests.get("http://localhost:3849/config")
config = config_response.json()["config"]

# 修改某个服务的配置
config["mcpServers"]["filesystem"]["args"] = [
    "-y", 
    "@modelcontextprotocol/server-filesystem", 
    "D:\\NewDirectory"
]

# 只重启这个服务
response = requests.post(
    "http://localhost:3849/restart-server",
    json={
        "serverName": "filesystem",
        "config": config["mcpServers"]["filesystem"]
    }
)
```

### 场景 3: 暂时关闭不需要的服务

```python
import requests

# 关闭暂时不需要的服务
response = requests.post(
    "http://localhost:3849/shutdown-server",
    json={"serverName": "hotnews-stdio"}
)
```

## 错误处理改进

### 修复了 "Attempted to exit cancel scope" 错误

之前在重启服务时可能会看到这个错误：
```
RuntimeError: Attempted to exit cancel scope in a different task than it was entered in
```

**原因**: 在异步环境中，上下文管理器（context manager）必须在同一个任务中进入和退出。

**解决方案**: 
- 使用 `asyncio.create_task()` 在新任务中执行清理操作
- 添加适当的延迟确保资源正确释放
- 改进错误捕获，即使清理失败也能正常移除客户端

## Python 测试脚本

使用提供的测试脚本 `test_restart_server.py`:

```bash
# 确保服务器正在运行
python utils/mcp_bridge.py

# 在另一个终端运行测试
python test_restart_server.py
```

## JavaScript/浏览器中使用

```javascript
// 重启服务
async function restartServer(serverName) {
  const response = await fetch('http://localhost:3849/restart-server', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ serverName })
  });
  
  const result = await response.json();
  console.log(result.message);
  return result;
}

// 使用
await restartServer('Knowledge Graph Memory Server');
```

## 注意事项

1. **服务名称必须准确**: 使用 `GET /tools` 查看所有服务的准确名称
2. **重启会中断连接**: 正在使用该服务的工具调用会失败
3. **配置缓存**: 不提供 config 参数时会使用上次加载的配置
4. **资源清理**: 关闭操作会在后台异步执行，确保资源正确释放

## 与全局重载的区别

| 功能 | 单独重启 | 全局重载 (/reload) |
|------|---------|-------------------|
| 影响范围 | 仅指定服务 | 所有服务 |
| 性能影响 | 最小 | 较大 |
| 适用场景 | 单个服务问题 | 配置文件全面更新 |
| 其他服务 | 继续运行 | 全部重启 |

## 常见问题

**Q: 如何知道哪些服务正在运行？**  
A: 使用 `GET /tools` 端点获取所有服务列表。

**Q: 重启服务会影响其他服务吗？**  
A: 不会，只有指定的服务会重启，其他服务继续正常运行。

**Q: 如果重启失败怎么办？**  
A: 服务会从列表中移除，可以通过 `/reload` 重新加载所有服务。

**Q: 可以重启一个不存在的服务吗？**  
A: 如果服务名称在配置中存在但未运行，会尝试启动；如果配置中也不存在，会返回 404 错误。
