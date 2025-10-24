// mcp-bridge-server.js
const express = require('express');
const cors = require('cors');
const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');
const fs = require('fs').promises;
const path = require('path');
const { spawn } = require('child_process');

const app = express();
const PORT = 3849; // 随便选的端口，你可以改

app.use(cors());
app.use(express.json());

// MCP 客户端管理器
class MCPManager {
  constructor() {
    this.clients = new Map(); // serverName -> {client, tools, process}
    this.toolCallHistory = new Map(); // 用于追踪工具调用次数
  }

  async loadConfig(configPath) {
    try {
      const content = await fs.readFile(configPath, 'utf-8');
      return JSON.parse(content);
    } catch (err) {
      console.error('读取配置失败:', err.message);
      return { mcpServers: {} };
    }
  }

  async initServer(serverName, serverConfig) {
    if (this.clients.has(serverName)) {
      console.log(`服务器 ${serverName} 已初始化`);
      return;
    }

    try {
      const { command, args = [], env = {} } = serverConfig;
      
      // 合并环境变量
      const serverEnv = { ...process.env, ...env };
      
      // 启动 MCP 服务器进程
      const childProcess = spawn(command, args, {
        env: serverEnv,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      childProcess.stderr.on('data', (data) => {
        console.error(`[${serverName}] stderr:`, data.toString());
      });

      childProcess.on('error', (err) => {
        console.error(`[${serverName}] 进程错误:`, err);
        this.clients.delete(serverName);
      });

      // 创建 MCP 客户端
      const transport = new StdioClientTransport({
        command,
        args,
        env: serverEnv
      });

      const client = new Client({
        name: 'deepseek-mcp-bridge',
        version: '1.0.0'
      }, {
        capabilities: {}
      });

      await client.connect(transport);

      // 获取工具列表
      const toolsResponse = await client.listTools();
      const tools = toolsResponse.tools || [];

      this.clients.set(serverName, { client, tools, process: childProcess });
      console.log(`✓ 服务器 ${serverName} 初始化成功，加载 ${tools.length} 个工具`);
    } catch (err) {
      console.error(`✗ 服务器 ${serverName} 初始化失败:`, err.message);
      throw err;
    }
  }

  async initAllServers(config) {
    const servers = config.mcpServers || {};
    const promises = Object.entries(servers).map(([name, cfg]) =>
      this.initServer(name, cfg).catch(err => {
        console.error(`跳过服务器 ${name}:`, err.message);
      })
    );
    await Promise.all(promises);
  }

  getAllTools() {
    const allTools = [];
    for (const [serverName, { tools }] of this.clients.entries()) {
      allTools.push(...tools.map(tool => ({
        ...tool,
        serverName // 标记工具来源
      })));
    }
    return allTools;
  }

  async executeTool(toolName, args) {
    // 查找工具所属的服务器
    let targetServer = null;
    let targetTool = null;

    for (const [serverName, { tools, client }] of this.clients.entries()) {
      const tool = tools.find(t => t.name === toolName);
      if (tool) {
        targetServer = { name: serverName, client };
        targetTool = tool;
        break;
      }
    }

    if (!targetServer) {
      throw new Error(`工具 ${toolName} 不存在`);
    }

    // 检查调用次数
    const callKey = `${targetServer.name}:${toolName}`;
    const callCount = this.toolCallHistory.get(callKey) || 0;
    
    if (callCount >= 3) {
      throw new Error(`工具 ${toolName} 已达到最大调用次数 (3次)`);
    }

    try {
      const result = await targetServer.client.callTool({
        name: toolName,
        arguments: args
      });

      // 重置计数器（成功后）
      this.toolCallHistory.set(callKey, 0);

      return result;
    } catch (err) {
      // 增加失败计数
      this.toolCallHistory.set(callKey, callCount + 1);
      throw err;
    }
  }

  resetToolCallHistory() {
    this.toolCallHistory.clear();
  }

  async shutdown() {
    for (const [name, { client, process }] of this.clients.entries()) {
      try {
        await client.close();
        process.kill();
        console.log(`已关闭服务器: ${name}`);
      } catch (err) {
        console.error(`关闭服务器 ${name} 失败:`, err);
      }
    }
    this.clients.clear();
  }
}

// 控制台输出格式化log信息
function log(message, type='info', ...args) {
  const timestamp = new Date().toLocaleString();
  const color = type === 'info' ? '\x1b[32m' : '\x1b[31m';
  const reset = '\x1b[0m';
  const logMessage = `[${timestamp}] ${message}`;
  const logMessageWithColor = `${color}${logMessage}${reset}`;
  console.log(logMessageWithColor, ...args);
}

const manager = new MCPManager();

// API 路由

// 健康检查
app.get('/health', (req, res) => {
  log('调用接口：运行状态检查');
  res.json({ status: 'ok', timestamp: Date.now() });
});

// 获取工具列表
app.get('/tools', (req, res) => {
  try {
    const tools = manager.getAllTools();
    res.json({
      success: true,
      tools: tools.map(t => ({
        name: t.name,
        description: t.description,
        parameters: t.inputSchema,
        serverName: t.serverName
      }))
    });
    log('调用接口：获取工具列表')
  } catch (err) {
    log('调用接口：获取工具列表', 'error', err.message)
    res.status(500).json({
      success: false,
      error: err.message
    });
  }
});

// 执行工具
app.post('/execute', async (req, res) => {
  const { name, arguments: args } = req.body;
  if (!name) {
    return res.status(400).json({
      success: false,
      error: '缺少参数: name'
    });
  }

  try {
    const result = await manager.executeTool(name, args || {});
    res.json({
      success: true,
      result: result.content
    });
    log('调用接口：执行工具', 'info' , name, args)
  } catch (err) {
    log('调用接口：执行工具', 'error', err.message)
    res.status(500).json({
      success: false,
      error: err.message
    });
  }
});

// 重载配置
app.post('/reload', async (req, res) => {
  try {
    
    await manager.shutdown();
    const configPath = req.body.configPath || './data/mcp-config.json';
    const config = await manager.loadConfig(configPath);
    await manager.initAllServers(config);
    res.json({
      success: true,
      message: '配置已重载'
    });
    log('调用接口：重载配置')
  } catch (err) {
    log('调用接口：重载配置', 'error', err.message)
    res.status(500).json({
      success: false,
      error: err.message
    });
  }
});

// 更新配置文件
app.post('/config', async (req, res) => {
  const { config, configPath = './data/mcp-config.json' } = req.body;
  if (!config) {
    log('调用接口：更新配置文件', 'error', '缺少参数: config')
    return res.status(400).json({
      success: false,
      error: '缺少参数: config'
    });
  }

  

  try {
    await fs.writeFile(configPath, JSON.stringify(config, null, 2), 'utf-8');
    // 自动重载
    await manager.shutdown();
    await manager.initAllServers(config);

    res.json({
      success: true,
      message: '配置已保存并重载'
    });
    log('调用接口：更新配置文件', 'info', configPath)
  } catch (err) {
    log('调用接口：更新配置文件', 'error', err.message)
    res.status(500).json({
      success: false,
      error: err.message
    });
  }
});

// 重置工具调用计数
app.post('/reset-history', (req, res) => {
  log('调用接口：重置工具调用计数');
  manager.resetToolCallHistory();
  res.json({
    success: true,
    message: '调用历史已重置'
  });
});

// 启动服务器
async function start() {
  try {
    // 加载配置
    const configPath = process.env.MCP_CONFIG_PATH || './data/mcp-config.json';
    console.log('读取配置文件:', configPath);
    
    const config = await manager.loadConfig(configPath);
    await manager.initAllServers(config);

    app.listen(PORT, () => {
      console.log(`\n🚀 MCP 桥接服务已启动`);
      console.log(`   地址: http://localhost:${PORT}`);
      console.log(`   工具数量: ${manager.getAllTools().length}`);
      console.log(`\n可用接口:`);
      console.log(`   GET  /health         - 健康检查`);
      console.log(`   GET  /tools          - 获取工具列表`);
      console.log(`   POST /execute        - 执行工具`);
      console.log(`   POST /reload         - 重载配置`);
      console.log(`   POST /config         - 更新配置文件`);
      console.log(`   POST /reset-history  - 重置调用历史\n`);
    });
  } catch (err) {
    console.error('启动失败:', err);
    process.exit(1);
  }
}

// 优雅关闭
process.on('SIGINT', async () => {
  console.log('\n正在关闭服务...');
  await manager.shutdown();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  await manager.shutdown();
  process.exit(0);
});

start();