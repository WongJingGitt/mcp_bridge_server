#!/usr/bin/env python3
"""
MCP Bridge Server - Python版本
提供HTTP接口来管理和调用MCP服务器
"""

import asyncio
import json
import os
import signal
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# MCP SDK 导入
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

PORT = 3849


def get_config_path() -> Path:
    """获取配置文件路径"""
    system = sys.platform
    
    if system == "win32":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            appdata = str(Path.home() / "AppData" / "Roaming")
        config_dir = Path(appdata) / "mcp-bridge" / "config"
    elif system == "darwin":
        config_dir = Path.home() / "Library" / "Application Support" / "mcp-bridge" / "config"
    elif system.startswith("linux"):
        config_dir = Path.home() / ".config" / "mcp-bridge" / "config"
    else:
        config_dir = Path.home() / ".mcp-bridge" / "config"
    
    # 创建目录
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        print(f"配置目录: {config_dir}")
    except Exception as e:
        print(f"创建配置目录失败: {config_dir}, 错误: {e}")
    
    return config_dir / "mcp-config.json"


class MCPServerConfig(BaseModel):
    """MCP服务器配置"""
    enabled: bool = True
    disabled: bool = False
    type: str = "stdio"  # "stdio" 或 "sse"
    # stdio 类型配置
    command: Optional[str] = None
    args: List[str] = []
    env: Dict[str, str] = {}
    # sse 类型配置
    url: Optional[str] = None
    # 通用配置
    timeout: int = 30
    description: str = ""


class Config(BaseModel):
    """配置文件结构"""
    mcpServers: Dict[str, MCPServerConfig]


class ExecuteRequest(BaseModel):
    """执行工具请求"""
    name: str
    arguments: Dict[str, Any] = {}


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    config: Dict[str, Any]


class MCPManager:
    """MCP服务管理器"""
    
    def __init__(self):
        self.clients: Dict[str, Dict[str, Any]] = {}
        self.tool_call_history: Dict[str, int] = {}
        self.sessions: Dict[str, ClientSession] = {}
    
    async def load_config(self, config_path: Path) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if not config_path.exists():
                print(f"配置文件不存在，正在创建默认配置: {config_path}")
                
                default_config = {
                    "mcpServers": {
                        "example_service": {
                            "enabled": True,
                            "command": "path/to/your/mcp/server/executable",
                            "args": ["--port", "8080"],
                            "description": "这是一个示例服务，请替换成你自己的配置。它能...",
                            "env": {}
                        }
                    }
                }
                
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                
                print(f"✓ 默认配置已创建: {config_path}")
                return default_config
            
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        except Exception as e:
            print(f"读取配置失败: {e}")
            return {"mcpServers": {}}
    
    async def init_server(self, server_name: str, server_config: Dict[str, Any]):
        """初始化单个MCP服务器"""
        if server_name in self.clients:
            print(f"服务器 {server_name} 已初始化")
            return
        
        server_type = server_config.get("type", "stdio").lower()
        timeout = server_config.get("timeout", 30)
        
        try:
            print(f"正在初始化服务器 {server_name} (类型: {server_type})...")
            
            if server_type == "sse":
                # SSE 类型服务器
                await self._init_sse_server(server_name, server_config, timeout)
            else:
                # stdio 类型服务器
                await self._init_stdio_server(server_name, server_config, timeout)
            
            print(f"✓ 服务器 {server_name} 初始化成功，加载 {len(self.clients[server_name]['tools'])} 个工具")
        
        except asyncio.TimeoutError:
            print(f"✗ 服务器 {server_name} 初始化超时（{timeout}秒）")
            raise
        except Exception as e:
            print(f"✗ 服务器 {server_name} 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def _init_stdio_server(self, server_name: str, server_config: Dict[str, Any], timeout: int):
        """初始化 stdio 类型服务器"""
        command = server_config.get("command")
        if not command:
            raise ValueError(f"stdio 类型服务器必须指定 command 字段")
        
        args = server_config.get("args", [])
        env = server_config.get("env", {})
        
        # 合并环境变量
        server_env = {**os.environ, **env}
        
        print(f"  执行命令: {command} {' '.join(args)}")
        
        # 创建服务器参数
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=server_env
        )
        
        print(f"  正在启动子进程...")
        
        # 使用异步上下文管理器连接到服务器
        stdio_context = stdio_client(server_params)
        read, write = await asyncio.wait_for(
            stdio_context.__aenter__(),
            timeout=timeout
        )
        print(f"  子进程已启动，正在建立会话...")
        
        # 创建会话上下文管理器
        session_context = ClientSession(read, write)
        session = await asyncio.wait_for(
            session_context.__aenter__(),
            timeout=timeout
        )
        print(f"  会话已建立，正在初始化...")
        
        try:
            # 初始化会话
            await asyncio.wait_for(
                session.initialize(),
                timeout=timeout
            )
            print(f"  会话初始化完成")
        except asyncio.TimeoutError:
            print(f"  ✗ 会话初始化超时")
            await session_context.__aexit__(None, None, None)
            await stdio_context.__aexit__(None, None, None)
            raise
        
        # 获取工具列表
        try:
            print(f"  正在获取工具列表...")
            tools_response = await asyncio.wait_for(
                session.list_tools(),
                timeout=timeout
            )
            tools = tools_response.tools if hasattr(tools_response, 'tools') else []
            print(f"  成功获取 {len(tools)} 个工具")
        except asyncio.TimeoutError:
            print(f"  ✗ 获取工具列表超时")
            await session_context.__aexit__(None, None, None)
            await stdio_context.__aexit__(None, None, None)
            raise
        
        self.clients[server_name] = {
            "type": "stdio",
            "session": session,
            "session_context": session_context,
            "tools": tools,
            "config": server_config,
            "stdio_context": stdio_context,
            "read": read,
            "write": write
        }
    
    async def _init_sse_server(self, server_name: str, server_config: Dict[str, Any], timeout: int):
        """初始化 SSE 类型服务器"""
        url = server_config.get("url")
        if not url:
            raise ValueError(f"sse 类型服务器必须指定 url 字段")
        
        print(f"  连接到 SSE 服务器: {url}")
        
        sse_context = None
        read = None
        write = None
        session_context = None
        
        try:
            # 使用异步上下文管理器连接到 SSE 服务器
            sse_context = sse_client(url)
            
            # 建立 SSE 连接
            try:
                read, write = await asyncio.wait_for(
                    sse_context.__aenter__(),
                    timeout=timeout
                )
                print(f"  SSE 连接已建立")
            except asyncio.TimeoutError:
                print(f"  ✗ 连接 SSE 服务器超时（{timeout}秒）")
                print(f"  提示：请检查 URL 是否有效，或尝试增加 timeout 值")
                raise
            except Exception as e:
                print(f"  ✗ 连接 SSE 服务器失败: {e}")
                print(f"  提示：请确认 URL 格式正确且服务器可访问")
                raise
            
            # 创建会话上下文管理器
            session_context = ClientSession(read, write)
            session = await asyncio.wait_for(
                session_context.__aenter__(),
                timeout=timeout
            )
            print(f"  会话已建立，正在初始化...")
            
            # 初始化会话
            try:
                await asyncio.wait_for(
                    session.initialize(),
                    timeout=timeout
                )
                print(f"  会话初始化完成")
            except asyncio.TimeoutError:
                print(f"  ✗ 会话初始化超时")
                raise
            
            # 获取工具列表
            try:
                print(f"  正在获取工具列表...")
                tools_response = await asyncio.wait_for(
                    session.list_tools(),
                    timeout=timeout
                )
                tools = tools_response.tools if hasattr(tools_response, 'tools') else []
                print(f"  成功获取 {len(tools)} 个工具")
            except asyncio.TimeoutError:
                print(f"  ✗ 获取工具列表超时")
                raise
            
            self.clients[server_name] = {
                "type": "sse",
                "session": session,
                "session_context": session_context,
                "tools": tools,
                "config": server_config,
                "sse_context": sse_context,
                "read": read,
                "write": write
            }
            
        except Exception:
            # 清理资源
            if session_context and read is not None:
                print(f"  清理会话...")
                try:
                    await session_context.__aexit__(*sys.exc_info())
                except Exception:
                    pass
            
            if sse_context and read is not None:
                print(f"  清理 SSE 连接...")
                try:
                    await sse_context.__aexit__(*sys.exc_info())
                except Exception:
                    pass
            raise
    
    async def init_all_servers(self, config: Dict[str, Any]):
        """初始化所有服务器"""
        servers = config.get("mcpServers", {})
        
        tasks = []
        for name, cfg in servers.items():
            # 检查 enabled 标志
            if cfg.get("enabled", True) is False:
                print(f"ℹ️ 服务 {name} 已被禁用，跳过加载。")
                continue
            
            # 创建初始化任务
            task = self._init_server_with_error_handling(name, cfg)
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _init_server_with_error_handling(self, name: str, cfg: Dict[str, Any]):
        """带错误处理的服务器初始化"""
        try:
            await self.init_server(name, cfg)
        except Exception as e:
            print(f"跳过服务器 {name}: {e}")
    
    def get_services(self) -> List[Dict[str, str]]:
        """获取所有服务列表"""
        services = []
        for server_name, client_data in self.clients.items():
            config = client_data["config"]
            services.append({
                "name": server_name,
                "description": config.get("description", f"一个名为 {server_name} 的工具服务。")
            })
        return services
    
    def get_tools_by_server(self, server_name: str) -> List[Dict[str, Any]]:
        """获取指定服务器的工具列表"""
        if server_name not in self.clients:
            raise ValueError(f"服务 {server_name} 不存在或未成功加载")
        
        tools = self.clients[server_name]["tools"]
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                "serverName": server_name
            }
            for tool in tools
        ]
    
    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """执行工具"""
        # 查找工具所属的服务器
        target_server = None
        target_session = None
        
        for server_name, client_data in self.clients.items():
            tools = client_data["tools"]
            for tool in tools:
                if tool.name == tool_name:
                    target_server = server_name
                    target_session = client_data["session"]
                    break
            if target_server:
                break
        
        if not target_server:
            raise ValueError(f"工具 {tool_name} 不存在")
        
        # 检查调用次数
        call_key = f"{target_server}:{tool_name}"
        call_count = self.tool_call_history.get(call_key, 0)
        
        if call_count >= 3:
            raise ValueError(f"工具 {tool_name} 已达到最大调用次数 (3次)")
        
        try:
            # 调用工具
            result = await target_session.call_tool(tool_name, args)
            
            # 重置调用计数
            self.tool_call_history[call_key] = 0
            
            return result
        
        except Exception as e:
            # 增加调用计数
            self.tool_call_history[call_key] = call_count + 1
            raise
    
    def reset_tool_call_history(self):
        """重置工具调用历史"""
        self.tool_call_history.clear()
    
    async def shutdown(self):
        """关闭所有服务器连接"""
        for name, client_data in self.clients.items():
            try:
                # 先关闭会话上下文
                session_context = client_data.get("session_context")
                if session_context:
                    await session_context.__aexit__(None, None, None)
                
                # 根据类型关闭对应的传输层连接
                server_type = client_data.get("type", "stdio")
                if server_type == "sse":
                    sse_context = client_data.get("sse_context")
                    if sse_context:
                        await sse_context.__aexit__(None, None, None)
                else:
                    stdio_context = client_data.get("stdio_context")
                    if stdio_context:
                        await stdio_context.__aexit__(None, None, None)
                
                print(f"已关闭服务器: {name}")
            except Exception as e:
                print(f"关闭服务器 {name} 失败: {e}")
        
        self.clients.clear()


# 全局管理器实例
manager: Optional[MCPManager] = None
config_path: Optional[Path] = None


def log(message: str, log_type: str = "info", *args):
    """日志输出"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    color = "\033[32m" if log_type == "info" else "\033[31m"
    reset = "\033[0m"
    print(f"{color}[{timestamp}] {message}{reset}", *args)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global manager, config_path
    
    # 启动时初始化
    try:
        manager = MCPManager()
        
        # 获取配置路径
        env_config_path = os.environ.get("MCP_CONFIG_PATH", "")
        if env_config_path:
            config_path = Path(env_config_path)
        else:
            config_path = get_config_path()
        
        print(f"读取配置文件: {config_path}")
        config = await manager.load_config(config_path)
        await manager.init_all_servers(config)
        
        print(f"\n🚀 MCP 桥接服务已启动")
        print(f"   地址: http://localhost:{PORT}")
        print(f"   已加载服务数量: {len(manager.get_services())}")
        print(f"\n可用接口:")
        print(f"   GET  /health                  - 健康检查")
        print(f"   GET  /tools                   - 获取所有[服务]的列表和描述")
        print(f"   GET  /tools?serverName=<n> - 获取指定服务下的[工具]列表")
        print(f"   POST /execute                 - 执行工具")
        print(f"   GET  /config                  - 读取配置文件内容")
        print(f"   POST /config                  - 更新配置文件并重载")
        print(f"   POST /reload                  - 手动重载配置")
        print(f"   POST /reset-history           - 重置调用历史\n")
    
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    yield
    
    # 关闭时清理
    if manager:
        print("\n正在关闭服务...")
        await manager.shutdown()
        print("服务器已关闭")


# 使用 lifespan 创建 FastAPI 应用
app = FastAPI(title="MCP Bridge Server", version="1.0.0", lifespan=lifespan)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().timestamp()}


@app.get("/tools")
async def get_tools(serverName: Optional[str] = Query(None)):
    """获取工具列表"""
    try:
        if serverName:
            # 获取指定服务器的工具
            tools = manager.get_tools_by_server(serverName)
            return {"success": True, "tools": tools}
        else:
            # 获取所有服务列表
            services = manager.get_services()
            return {"success": True, "services": services}
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute")
async def execute_tool(request: ExecuteRequest):
    """执行工具"""
    try:
        result = await manager.execute_tool(request.name, request.arguments)
        
        # 提取内容
        content = []
        if hasattr(result, 'content'):
            content = result.content
        
        return {"success": True, "result": content}
    
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        error_detail = {
            "error": str(e),
            "type": type(e).__name__,
            "traceback": error_traceback
        }
        log(f"工具执行错误: {error_detail}", "error")
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/config")
async def get_config():
    """读取配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return {"success": True, "config": config}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取配置文件失败: {e}")


@app.post("/config")
async def update_config(request: ConfigUpdateRequest):
    """更新配置文件并重载"""
    try:
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(request.config, f, indent=2, ensure_ascii=False)
        
        # 重载服务
        await manager.shutdown()
        await manager.init_all_servers(request.config)
        
        return {"success": True, "message": "配置已保存并重载"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reload")
async def reload_config():
    """重载配置"""
    try:
        await manager.shutdown()
        config = await manager.load_config(config_path)
        await manager.init_all_servers(config)
        
        return {"success": True, "message": "配置已重载"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset-history")
async def reset_history():
    """重置调用历史"""
    manager.reset_tool_call_history()
    return {"success": True, "message": "调用历史已重置"}


def signal_handler(sig, frame):
    """处理终止信号"""
    print("\n接收到终止信号，正在关闭...")
    sys.exit(0)


if __name__ == "__main__":
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )