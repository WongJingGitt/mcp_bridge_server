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
import socket
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import asynccontextmanager
import uuid
import threading
import time
import json
from collections import OrderedDict

# 尝试导入版本信息
try:
    # 如果是打包后的程序，使用相对导入
    if getattr(sys, 'frozen', False):
        __version__ = "1.0.0"
    else:
        # 开发环境，从 version.py 导入
        parent_dir = Path(__file__).parent.parent
        if str(parent_dir) not in sys.path:
            sys.path.insert(0, str(parent_dir))
        from version import __version__
except ImportError:
    __version__ = "1.0.0"

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


def is_port_in_use(port: int) -> bool:
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except OSError:
            return True


def get_process_using_port(port: int) -> Optional[Dict[str, Any]]:
    """获取占用端口的进程信息"""
    try:
        if sys.platform == "win32":
            # Windows 使用 netstat
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                encoding='gbk',
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            for line in result.stdout.split('\n'):
                if f':{port} ' in line or f':{port}\t' in line:
                    parts = line.split()
                    if len(parts) >= 5 and parts[1].endswith(f':{port}'):
                        pid = parts[-1]
                        # 获取进程名称
                        try:
                            tasklist_result = subprocess.run(
                                ['tasklist', '/FI', f'PID eq {pid}', '/NH'],
                                capture_output=True,
                                text=True,
                                encoding='gbk',
                                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                            )
                            process_name = tasklist_result.stdout.split()[0] if tasklist_result.stdout else "Unknown"
                            return {"pid": pid, "name": process_name}
                        except:
                            return {"pid": pid, "name": "Unknown"}
        else:
            # Linux/Mac 使用 lsof
            result = subprocess.run(
                ['lsof', '-i', f':{port}', '-t'],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                pid = result.stdout.strip().split('\n')[0]
                # 获取进程名称
                try:
                    name_result = subprocess.run(
                        ['ps', '-p', pid, '-o', 'comm='],
                        capture_output=True,
                        text=True
                    )
                    process_name = name_result.stdout.strip()
                    return {"pid": pid, "name": process_name}
                except:
                    return {"pid": pid, "name": "Unknown"}
    except Exception as e:
        print(f"获取进程信息失败: {e}")
    
    return None


def kill_process_by_pid(pid: str) -> bool:
    """根据 PID 结束进程"""
    try:
        if sys.platform == "win32":
            subprocess.run(
                ['taskkill', '/F', '/PID', pid], 
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
        else:
            subprocess.run(['kill', '-9', pid], check=True)
        return True
    except Exception as e:
        print(f"结束进程失败: {e}")
        return False


def check_and_handle_port(port: int, auto_kill: bool = False) -> bool:
    """
    检查并处理端口占用
    
    Args:
        port: 要检查的端口
        auto_kill: 是否自动结束占用进程（通过环境变量或命令行参数）
    
    Returns:
        True 如果端口可用，False 如果端口被占用且用户选择不结束进程
    """
    if not is_port_in_use(port):
        return True
    
    print(f"\n⚠️  端口 {port} 已被占用")
    
    # 获取占用进程信息
    process_info = get_process_using_port(port)
    if process_info:
        print(f"   占用进程: {process_info['name']} (PID: {process_info['pid']})")
    
    # 检查环境变量
    if auto_kill or os.environ.get('MCP_AUTO_KILL_PORT', '').lower() in ['true', '1', 'yes']:
        print(f"   自动结束占用进程...")
        if process_info and kill_process_by_pid(process_info['pid']):
            print(f"   ✓ 进程已结束")
            # 等待端口释放
            import time
            time.sleep(1)
            if not is_port_in_use(port):
                print(f"   ✓ 端口 {port} 已释放")
                return True
            else:
                print(f"   ✗ 端口 {port} 仍被占用")
                return False
        else:
            print(f"   ✗ 无法结束进程")
            return False
    
    # 交互式询问
    try:
        print(f"\n请选择操作:")
        print(f"  1. 结束占用进程并继续")
        print(f"  2. 使用其他端口")
        print(f"  3. 退出程序")
        
        choice = input("\n请输入选项 (1/2/3): ").strip()
        
        if choice == '1':
            if process_info and kill_process_by_pid(process_info['pid']):
                print(f"✓ 进程已结束")
                # 等待端口释放
                import time
                time.sleep(1)
                if not is_port_in_use(port):
                    print(f"✓ 端口 {port} 已释放")
                    return True
                else:
                    print(f"✗ 端口 {port} 仍被占用，请手动处理")
                    return False
            else:
                print(f"✗ 无法结束进程")
                return False
        
        elif choice == '2':
            new_port = input(f"请输入新端口号 (当前: {port}): ").strip()
            try:
                new_port_num = int(new_port)
                if 1 <= new_port_num <= 65535:
                    global PORT
                    PORT = new_port_num
                    print(f"✓ 已切换到端口 {PORT}")
                    return check_and_handle_port(PORT, auto_kill)
                else:
                    print(f"✗ 端口号必须在 1-65535 之间")
                    return False
            except ValueError:
                print(f"✗ 无效的端口号")
                return False
        
        else:
            print("退出程序")
            return False
    
    except (KeyboardInterrupt, EOFError):
        print("\n\n已取消")
        return False


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
    # 缓存配置
    max_output_bytes: int = 1000  # 触发缓存的输出字节数阈值
    output_truncate_strategy: str = "tail"  # 截断策略: "tail", "head", "middle"
    cache_large_results: bool = True  # 是否启用大结果缓存
    result_cache_ttl: int = 300  # 缓存过期时间（秒）
    max_memory_cache_size: int = 10240  # 内存缓存阈值（字节），超过此大小使用文件缓存


class Config(BaseModel):
    """配置文件结构"""
    mcpServers: Dict[str, MCPServerConfig]


class ExecuteRequest(BaseModel):
    """执行工具请求"""
    name: str
    arguments: Dict[str, Any] = {}
    serverName: Optional[str] = None  # 可选的服务名称，用于指定特定服务下的工具


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    config: Dict[str, Any]


class ServerRestartRequest(BaseModel):
    """服务器重启请求"""
    serverName: str
    config: Optional[Dict[str, Any]] = None  # 可选的新配置


class GetResultRequest(BaseModel):
    """获取缓存结果请求"""
    cache_id: str
    start: Optional[int] = 0
    end: Optional[int] = None


class SearchCacheRequest(BaseModel):
    """搜索缓存内容请求"""
    cache_id: str
    keyword: str
    case_sensitive: Optional[bool] = False
    max_results: Optional[int] = 50


class GetCacheContextRequest(BaseModel):
    """获取缓存上下文请求"""
    cache_id: str
    line_num: int
    context_lines: Optional[int] = 3


class MCPManager:
    """MCP服务管理器"""
    
    def __init__(self):
        self.clients: Dict[str, Dict[str, Any]] = {}
        self.tool_call_history: Dict[str, int] = {}
        self.sessions: Dict[str, ClientSession] = {}
        self.config_cache: Dict[str, Any] = {}  # 缓存配置用于重启单个服务
        
        # 缓存系统相关
        self.memory_cache: OrderedDict = OrderedDict()  # 内存缓存
        self.cache_lock = threading.RLock()  # 缓存访问锁
        self.max_memory_cache_items = 100  # 最大内存缓存条目数
    
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
                self.config_cache = default_config  # 缓存配置
                return default_config
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.config_cache = config  # 缓存配置
                return config
        
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
                "description": config.get("description", f"一个名为 {server_name} 的工具服务。"),
                "is_core": config.get("is_core", False)  # 读取配置中的 is_core 标记，默认为 False
            })
        return services
    
    def get_tools_by_server(self, server_name: str) -> Dict[str, Any]:
        """获取指定服务器的工具列表（包含服务描述）"""
        if server_name not in self.clients:
            raise ValueError(f"服务 {server_name} 不存在或未成功加载")
        
        client_data = self.clients[server_name]
        config = client_data["config"]
        tools = client_data["tools"]
        
        return {
            "service_name": server_name,
            "service_description": config.get("description", f"一个名为 {server_name} 的工具服务。"),
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                }
                for tool in tools
            ]
        }
    
    def get_tool_detail(self, tool_name: str, server_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取工具的详细信息
        
        Args:
            tool_name: 工具名称
            server_name: 可选的服务名称
        
        Returns:
            工具的详细信息，包括完整的参数定义
        """
        target_server = None
        target_tool = None
        
        if server_name:
            if server_name not in self.clients:
                raise ValueError(f"服务 {server_name} 不存在或未加载")
            
            tools = self.clients[server_name]["tools"]
            for tool in tools:
                if tool.name == tool_name:
                    target_server = server_name
                    target_tool = tool
                    break
            
            if not target_tool:
                raise ValueError(f"服务 {server_name} 中不存在工具 {tool_name}")
        else:
            # 在所有服务中查找
            for srv_name, client_data in self.clients.items():
                tools = client_data["tools"]
                for tool in tools:
                    if tool.name == tool_name:
                        target_server = srv_name
                        target_tool = tool
                        break
                if target_tool:
                    break
            
            if not target_tool:
                raise ValueError(f"工具 {tool_name} 不存在")
        
        # 提取完整的工具信息
        return {
            "name": target_tool.name,
            "description": target_tool.description,
            "serverName": target_server,
            "inputSchema": target_tool.inputSchema if hasattr(target_tool, 'inputSchema') else {},
            "parameters": target_tool.inputSchema if hasattr(target_tool, 'inputSchema') else {}
        }
    
    async def execute_tool(self, tool_name: str, args: Dict[str, Any], server_name: Optional[str] = None) -> Any:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            args: 工具参数
            server_name: 可选的服务名称，指定从哪个服务调用工具
        
        Returns:
            工具执行结果
        
        Raises:
            ValueError: 当工具不存在、服务不存在或达到最大调用次数时
        """
        target_server = None
        target_session = None
        
        # 清理参数：移除值为 None 的键，因为某些 MCP 服务可能不支持 null 值
        cleaned_args = {k: v for k, v in args.items() if v is not None}
        
        # 如果指定了服务名称，直接在该服务中查找
        if server_name:
            if server_name not in self.clients:
                raise ValueError(f"服务 {server_name} 不存在或未加载")
            
            client_data = self.clients[server_name]
            tools = client_data["tools"]
            
            # 在指定服务中查找工具
            tool_found = False
            for tool in tools:
                if tool.name == tool_name:
                    tool_found = True
                    target_server = server_name
                    target_session = client_data["session"]
                    break
            
            if not tool_found:
                raise ValueError(f"服务 {server_name} 中不存在工具 {tool_name}")
        
        else:
            # 未指定服务名称，在所有服务中查找（保持向后兼容）
            matching_servers = []
            
            for srv_name, client_data in self.clients.items():
                tools = client_data["tools"]
                for tool in tools:
                    if tool.name == tool_name:
                        matching_servers.append(srv_name)
                        if not target_server:  # 记录第一个匹配的服务
                            target_server = srv_name
                            target_session = client_data["session"]
                        break
            
            if not target_server:
                raise ValueError(f"工具 {tool_name} 不存在")
            
            # 如果有多个服务提供同名工具，给出警告
            if len(matching_servers) > 1:
                print(f"⚠️  警告: 工具 {tool_name} 在多个服务中存在: {', '.join(matching_servers)}")
                print(f"   将使用服务 {target_server}，建议在请求中指定 serverName 参数以避免歧义")
        
        # 检查调用次数
        call_key = f"{target_server}:{tool_name}"
        call_count = self.tool_call_history.get(call_key, 0)
        
        if call_count >= 3:
            raise ValueError(f"工具 {tool_name} (服务: {target_server}) 已达到最大调用次数 (3次)")
        
        try:
            # 打印调试信息
            print(f"[执行工具] 服务: {target_server}, 工具: {tool_name}")
            print(f"[原始参数] {args}")
            print(f"[清理后参数] {cleaned_args}")
            
            # 调用工具
            result = await target_session.call_tool(tool_name, cleaned_args)
            
            # 获取服务配置
            server_config = self.clients[target_server]["config"]
            
            # 将MCP结果转换为可序列化的格式
            if hasattr(result, 'model_dump'):
                # 使用Pydantic的model_dump方法（如果可用）
                serializable_result = result.model_dump()
            elif hasattr(result, '__dict__'):
                # 尝试转换对象为字典
                import copy
                try:
                    serializable_result = copy.deepcopy(result.__dict__)
                except Exception:
                    # 如果deepcopy失败，尝试手动转换
                    serializable_result = {}
                    for attr_name in dir(result):
                        if not attr_name.startswith('_'):
                            attr_value = getattr(result, attr_name)
                            if isinstance(attr_value, (str, int, float, bool, list, dict, type(None))):
                                serializable_result[attr_name] = attr_value
                            else:
                                # 尝试转换为字符串表示
                                try:
                                    serializable_result[attr_name] = str(attr_value)
                                except:
                                    serializable_result[attr_name] = f"<unserializable: {type(attr_value).__name__}>"
            else:
                # 如果无法转换，直接使用结果
                serializable_result = result
            
            # 使用缓存系统处理结果
            cached_result = self.cache_result(serializable_result, server_config)
            
            # 重置调用计数
            self.tool_call_history[call_key] = 0
            
            return cached_result
        
        except Exception as e:
            # 增加调用计数
            self.tool_call_history[call_key] = call_count + 1
            
            # 打印详细错误信息
            print(f"[工具执行失败] 服务: {target_server}, 工具: {tool_name}")
            print(f"[错误类型] {type(e).__name__}")
            print(f"[错误信息] {str(e)}")
            raise
    
    def reset_tool_call_history(self):
        """重置工具调用历史"""
        self.tool_call_history.clear()
    
    async def shutdown(self):
        """关闭所有服务器连接"""
        for name in list(self.clients.keys()):
            await self.shutdown_server(name)
    
    async def shutdown_server(self, server_name: str):
        """关闭指定的服务器连接"""
        if server_name not in self.clients:
            print(f"服务器 {server_name} 不存在，无需关闭")
            return
        
        client_data = self.clients[server_name]
        
        try:
            # 创建一个新任务来处理关闭，避免 cancel scope 错误
            async def cleanup():
                try:
                    # 先关闭会话上下文
                    session_context = client_data.get("session_context")
                    if session_context:
                        try:
                            await session_context.__aexit__(None, None, None)
                        except Exception as e:
                            print(f"  关闭会话上下文时出错: {e}")
                    
                    # 根据类型关闭对应的传输层连接
                    server_type = client_data.get("type", "stdio")
                    if server_type == "sse":
                        sse_context = client_data.get("sse_context")
                        if sse_context:
                            try:
                                await sse_context.__aexit__(None, None, None)
                            except Exception as e:
                                print(f"  关闭 SSE 连接时出错: {e}")
                    else:
                        stdio_context = client_data.get("stdio_context")
                        if stdio_context:
                            try:
                                await stdio_context.__aexit__(None, None, None)
                            except Exception as e:
                                print(f"  关闭 stdio 连接时出错: {e}")
                except Exception as e:
                    print(f"  清理资源时出错: {e}")
            
            # 使用 asyncio.create_task 在新任务中执行清理
            # 但我们不等待它完成，让它在后台运行
            asyncio.create_task(cleanup())
            
            # 给一点时间让清理开始
            await asyncio.sleep(0.1)
            
            print(f"已关闭服务器: {server_name}")
        except Exception as e:
            print(f"关闭服务器 {server_name} 失败: {e}")
        finally:
            # 无论如何都从字典中移除
            self.clients.pop(server_name, None)
    
    def _get_cache_directory(self) -> Path:
        """获取缓存目录路径"""
        # 根据操作系统确定缓存目录
        if sys.platform == "win32":
            cache_dir = Path(os.environ.get("APPDATA", "")) / "mcp-bridge" / "cache"
        elif sys.platform == "darwin":
            cache_dir = Path.home() / "Library" / "Application Support" / "mcp-bridge" / "cache"
        else:  # Linux and others
            cache_dir = Path.home() / ".cache" / "mcp-bridge"
        
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def _store_in_file_cache(self, content: Any, ttl: int) -> str:
        """将内容存储到文件缓存并返回ID"""
        cache_id = str(uuid.uuid4())
        cache_file = self._get_cache_directory() / f"{cache_id}.txt"
        
        # 序列化内容
        if isinstance(content, str):
            content_str = content
        else:
            content_str = json.dumps(content, ensure_ascii=False, indent=2)
        
        # 写入文件
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(content_str)
        
        # 创建元数据文件
        metadata_file = self._get_cache_directory() / f"{cache_id}.meta"
        metadata = {
            "created_at": time.time(),
            "expires_at": time.time() + ttl,
            "size": len(content_str.encode('utf-8'))
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f)
        
        return cache_id
    
    def _get_from_file_cache(self, cache_id: str) -> Optional[Any]:
        """从文件缓存获取内容"""
        cache_file = self._get_cache_directory() / f"{cache_id}.txt"
        metadata_file = self._get_cache_directory() / f"{cache_id}.meta"
        
        # 检查文件是否存在
        if not cache_file.exists() or not metadata_file.exists():
            return None
        
        # 检查过期时间
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            if time.time() > metadata.get("expires_at", 0):
                # 过期，删除文件
                cache_file.unlink(missing_ok=True)
                metadata_file.unlink(missing_ok=True)
                return None
        except:
            return None
        
        # 读取内容
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 尝试解析JSON，如果不是JSON则返回原字符串
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return content
        except:
            return None
    
    def _store_in_memory_cache(self, content: Any, ttl: int) -> str:
        """将内容存储到内存缓存并返回ID"""
        cache_id = str(uuid.uuid4())
        
        with self.cache_lock:
            # 清理过期项
            current_time = time.time()
            expired_keys = []
            for key, (_, expire_time) in list(self.memory_cache.items()):
                if current_time > expire_time:
                    expired_keys.append(key)
            for key in expired_keys:
                self.memory_cache.pop(key, None)
            
            # 如果达到最大容量，移除最旧的项
            while len(self.memory_cache) >= self.max_memory_cache_items:
                oldest_key = next(iter(self.memory_cache))
                self.memory_cache.pop(oldest_key, None)
            
            # 存储新项
            self.memory_cache[cache_id] = (content, current_time + ttl)
        
        return cache_id
    
    def _get_from_memory_cache(self, cache_id: str) -> Optional[Any]:
        """从内存缓存获取内容"""
        with self.cache_lock:
            if cache_id not in self.memory_cache:
                return None
            
            content, expire_time = self.memory_cache[cache_id]
            current_time = time.time()
            
            if current_time > expire_time:
                # 过期，删除项
                self.memory_cache.pop(cache_id, None)
                return None
            
            # 移动到末尾（LRU策略）
            self.memory_cache.pop(cache_id)
            self.memory_cache[cache_id] = (content, expire_time)
            
            return content
    
    def cache_result(self, content: Any, server_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """根据内容大小和配置决定缓存策略"""
        # 获取配置参数
        if server_config is None:
            server_config = {}
        
        # 兼容旧配置名称 max_output_length，优先使用新名称 max_output_bytes
        max_output_bytes = server_config.get("max_output_bytes", server_config.get("max_output_length", 1000))
        cache_large_results = server_config.get("cache_large_results", True)
        result_cache_ttl = server_config.get("result_cache_ttl", 300)
        max_memory_cache_size = server_config.get("max_memory_cache_size", 10240)  # 10KB
        
        # 序列化内容以计算大小（字节数）
        if isinstance(content, str):
            content_str = content
        else:
            content_str = json.dumps(content, ensure_ascii=False)
        
        content_size = len(content_str.encode('utf-8'))
        
        if cache_large_results and content_size > max_output_bytes:
            # 内容超过阈值，需要缓存
            if content_size <= max_memory_cache_size:
                # 使用内存缓存
                cache_id = self._store_in_memory_cache(content, result_cache_ttl)
                cache_type = "memory"
            else:
                # 使用文件缓存
                cache_id = self._store_in_file_cache(content, result_cache_ttl)
                cache_type = "file"
            
            return {
                "result_type": "cached_reference",
                "cache_id": cache_id,
                "cache_type": cache_type,
                "total_size": content_size,
                "message": f"结果过大({content_size}字节)，已存储在{'内存' if cache_type == 'memory' else '文件'}缓存中，使用 /result/{cache_id} 获取完整结果"
            }
        else:
            # 内容较小，直接返回
            return {
                "result_type": "direct",
                "result": content
            }
    
    def get_cached_result(self, cache_id: str) -> Optional[Any]:
        """获取缓存结果"""
        # 首先尝试从内存缓存获取
        result = self._get_from_memory_cache(cache_id)
        if result is not None:
            return result
        
        # 如果内存中没有，尝试从文件缓存获取
        return self._get_from_file_cache(cache_id)
    
    def get_cached_result_partial(self, cache_id: str, start: int = 0, end: Optional[int] = None) -> Dict[str, Any]:
        """获取缓存结果的部分内容"""
        content = self.get_cached_result(cache_id)
        if content is None:
            return {"error": "缓存ID不存在或已过期"}
        
        if isinstance(content, str):
            # 字符串内容的分段
            total_len = len(content)
            actual_end = min(end, total_len) if end is not None else total_len
            actual_start = max(0, start)
            
            return {
                "content": content[actual_start:actual_end],
                "total_length": total_len,
                "start": actual_start,
                "end": actual_end,
                "has_more": actual_end < total_len
            }
        elif isinstance(content, list):
            # 列表内容的分段
            total_len = len(content)
            actual_end = min(end, total_len) if end is not None else total_len
            actual_start = max(0, start)
            
            return {
                "content": content[actual_start:actual_end],
                "total_length": total_len,
                "start": actual_start,
                "end": actual_end,
                "has_more": actual_end < total_len
            }
        else:
            # 其他类型（如dict、对象）：序列化为JSON字符串后分段
            content_str = json.dumps(content, ensure_ascii=False, indent=2)
            total_len = len(content_str)
            actual_end = min(end, total_len) if end is not None else total_len
            actual_start = max(0, start)
            
            return {
                "content": content_str[actual_start:actual_end],
                "total_length": total_len,
                "start": actual_start,
                "end": actual_end,
                "has_more": actual_end < total_len
            }
    
    def search_in_cache(self, cache_id: str, keyword: str, 
                       case_sensitive: bool = False,
                       max_results: int = 50) -> Dict[str, Any]:
        """
        在缓存内容中搜索关键词（流式处理，性能优化）
        
        Args:
            cache_id: 缓存ID
            keyword: 搜索关键词
            case_sensitive: 是否区分大小写
            max_results: 最大返回结果数
        
        Returns:
            搜索结果，包含匹配的行号、列号和内容片段
        """
        # 首先尝试从内存缓存获取
        content = self._get_from_memory_cache(cache_id)
        
        if content is not None:
            # 内存缓存：直接搜索
            return self._search_in_memory(content, keyword, case_sensitive, max_results)
        
        # 尝试从文件缓存获取
        cache_file = self._get_cache_directory() / f"{cache_id}.txt"
        if cache_file.exists():
            # 文件缓存：流式读取搜索
            return self._search_in_file_streaming(cache_file, keyword, case_sensitive, max_results)
        
        raise ValueError("缓存不存在或已过期")
    
    def _search_in_memory(self, content: Any, keyword: str, 
                         case_sensitive: bool, max_results: int) -> Dict[str, Any]:
        """在内存中的内容进行搜索"""
        # 转换为字符串
        if isinstance(content, str):
            text = content
        else:
            text = json.dumps(content, ensure_ascii=False, indent=2)
        
        return self._search_in_text(text, keyword, case_sensitive, max_results)
    
    def _search_in_file_streaming(self, cache_file: Path, keyword: str,
                                  case_sensitive: bool, max_results: int) -> Dict[str, Any]:
        """流式读取文件并搜索（内存占用恒定）"""
        matches = []
        search_keyword = keyword if case_sensitive else keyword.lower()
        line_num = 0
        
        try:
            # 使用缓冲读取，每次读取 8KB
            with open(cache_file, 'r', encoding='utf-8', buffering=8192) as f:
                for line in f:
                    line_num += 1
                    search_line = line if case_sensitive else line.lower()
                    
                    # 查找所有匹配位置
                    pos = 0
                    while True:
                        idx = search_line.find(search_keyword, pos)
                        if idx == -1:
                            break
                        
                        matches.append({
                            "line": line_num,
                            "column": idx,
                            "content": line.strip()[:200]  # 限制长度避免过长
                        })
                        
                        if len(matches) >= max_results:
                            break
                        
                        pos = idx + 1
                    
                    if len(matches) >= max_results:
                        break
        except Exception as e:
            print(f"流式搜索文件失败: {e}")
            raise
        
        return {
            "keyword": keyword,
            "total_matches": len(matches),
            "matches": matches,
            "truncated": len(matches) >= max_results
        }
    
    def _search_in_text(self, text: str, keyword: str,
                       case_sensitive: bool, max_results: int) -> Dict[str, Any]:
        """在文本中搜索关键词"""
        matches = []
        search_keyword = keyword if case_sensitive else keyword.lower()
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            search_line = line if case_sensitive else line.lower()
            
            # 查找所有匹配位置
            pos = 0
            while True:
                idx = search_line.find(search_keyword, pos)
                if idx == -1:
                    break
                
                matches.append({
                    "line": line_num,
                    "column": idx,
                    "content": line.strip()[:200]  # 限制长度
                })
                
                if len(matches) >= max_results:
                    break
                
                pos = idx + 1
            
            if len(matches) >= max_results:
                break
        
        return {
            "keyword": keyword,
            "total_matches": len(matches),
            "matches": matches,
            "truncated": len(matches) >= max_results
        }
    
    def get_context_around_line(self, cache_id: str, line_num: int,
                                context_lines: int = 3) -> Dict[str, Any]:
        """
        获取指定行及其上下文
        
        Args:
            cache_id: 缓存ID
            line_num: 目标行号（从1开始）
            context_lines: 上下文行数
        
        Returns:
            包含目标行及上下文的内容
        """
        content = self.get_cached_result(cache_id)
        if content is None:
            raise ValueError("缓存不存在或已过期")
        
        # 转换为字符串
        if isinstance(content, str):
            text = content
        else:
            text = json.dumps(content, ensure_ascii=False, indent=2)
        
        lines = text.split('\n')
        total_lines = len(lines)
        
        # 计算上下文范围
        start_line = max(1, line_num - context_lines)
        end_line = min(total_lines, line_num + context_lines)
        
        # 提取上下文内容
        context_content = '\n'.join(lines[start_line-1:end_line])
        
        return {
            "target_line": line_num,
            "context_start": start_line,
            "context_end": end_line,
            "total_lines": total_lines,
            "content": context_content
        }
    
    async def restart_server(self, server_name: str, server_config: Optional[Dict[str, Any]] = None):
        """重启指定的服务器"""
        # 如果没有提供配置，使用缓存的配置
        if server_config is None:
            if server_name not in self.config_cache.get("mcpServers", {}):
                raise ValueError(f"服务器 {server_name} 的配置不存在")
            server_config = self.config_cache["mcpServers"][server_name]
        
        # 先关闭
        await self.shutdown_server(server_name)
        
        # 等待一下确保资源释放
        await asyncio.sleep(0.5)
        
        # 重新初始化
        await self.init_server(server_name, server_config)


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
        print(f"   GET  /health                     - 健康检查")
        print(f"   GET  /tools                      - 获取所有[服务]的列表和描述")
        print(f"   GET  /tools?serverName=<name>    - 获取指定服务下的[工具]列表")
        print(f"   GET  /tool-detail?toolName=<n>   - 获取工具的详细参数定义")
        print(f"   POST /execute                    - 执行工具（可选 serverName 参数）")
        print(f"   POST /result                     - 获取缓存结果（分段）")
        print(f"   GET  /result/{'{cache_id}'}            - 获取缓存结果（分段，简单接口）")
        print(f"   POST /search-cache               - 在缓存中搜索关键词")
        print(f"   POST /get-cache-context          - 获取缓存指定行的上下文")
        print(f"   GET  /config                     - 读取配置文件内容")
        print(f"   POST /config                     - 更新配置文件并重载")
        print(f"   POST /reload                     - 手动重载所有服务")
        print(f"   POST /restart-server             - 重启指定服务")
        print(f"   POST /shutdown-server            - 关闭指定服务")
        print(f"   POST /reset-history              - 重置调用历史\n")
    
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


@app.get("/tool-detail")
async def get_tool_detail(
    toolName: str = Query(..., description="工具名称"),
    serverName: Optional[str] = Query(None, description="服务名称（可选）")
):
    """
    获取工具的详细信息
    
    参数:
        - toolName: 工具名称（必需）
        - serverName: 服务名称（可选，如果有重名工具建议指定）
    
    返回工具的完整定义，包括参数 schema，用于调试和了解工具的参数要求
    """
    try:
        detail = manager.get_tool_detail(toolName, serverName)
        return {"success": True, "tool": detail}
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute")
async def execute_tool(request: ExecuteRequest):
    """
    执行工具
    
    请求体:
        - name: 工具名称（必需）
        - arguments: 工具参数（可选，默认为空对象）
        - serverName: 服务名称（可选，指定从哪个服务调用工具）
    
    示例:
        不指定服务（兼容旧版本）:
        {"name": "read_file", "arguments": {"path": "/tmp/test.txt"}}
        
        指定服务（推荐，避免重名工具冲突）:
        {"name": "read_file", "arguments": {"path": "/tmp/test.txt"}, "serverName": "filesystem"}
    """
    try:
        result = await manager.execute_tool(
            request.name, 
            request.arguments,
            request.serverName  # 传递可选的服务名称
        )
        
        # 检查结果类型
        if isinstance(result, dict) and result.get("result_type") == "cached_reference":
            # 返回缓存引用
            return {
                "success": True,
                "result_type": result["result_type"],
                "cache_id": result["cache_id"],
                "cache_type": result["cache_type"],
                "total_size": result["total_size"],
                "message": result["message"]
            }
        else:
            # 返回直接结果
            content = result.get("result") if isinstance(result, dict) and "result" in result else result
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


@app.post("/restart-server")
async def restart_server(request: ServerRestartRequest):
    """重启指定的服务器"""
    try:
        server_name = request.serverName
        
        # 检查服务是否存在
        if server_name not in manager.clients and server_name not in manager.config_cache.get("mcpServers", {}):
            raise HTTPException(status_code=404, detail=f"服务 {server_name} 不存在")
        
        # 重启服务
        await manager.restart_server(server_name, request.config)
        
        return {
            "success": True,
            "message": f"服务 {server_name} 已重启",
            "toolCount": len(manager.clients[server_name]["tools"]) if server_name in manager.clients else 0
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/shutdown-server")
async def shutdown_server(request: ServerRestartRequest):
    """关闭指定的服务器"""
    try:
        server_name = request.serverName
        
        # 检查服务是否存在
        if server_name not in manager.clients:
            raise HTTPException(status_code=404, detail=f"服务 {server_name} 不存在或未运行")
        
        # 关闭服务
        await manager.shutdown_server(server_name)
        
        return {
            "success": True,
            "message": f"服务 {server_name} 已关闭"
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/result")
async def get_cached_result(request: GetResultRequest):
    """获取缓存的结果"""
    try:
        result = manager.get_cached_result_partial(request.cache_id, request.start, request.end)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {
            "success": True,
            "result": result["content"],
            "metadata": {
                "total_length": result["total_length"],
                "start": result["start"],
                "end": result["end"],
                "has_more": result["has_more"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/result/{cache_id}")
async def get_cached_result_simple(cache_id: str, start: int = 0, end: Optional[int] = None):
    """获取缓存结果的简单接口"""
    try:
        result = manager.get_cached_result_partial(cache_id, start, end)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {
            "success": True,
            "result": result["content"],
            "metadata": {
                "total_length": result["total_length"],
                "start": result["start"],
                "end": result["end"],
                "has_more": result["has_more"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search-cache")
async def search_cache(request: SearchCacheRequest):
    """
    在缓存内容中搜索关键词
    
    请求体:
        - cache_id: 缓存ID
        - keyword: 搜索关键词
        - case_sensitive: 是否区分大小写（可选，默认false）
        - max_results: 最大返回结果数（可选，默认50）
    
    返回:
        搜索结果，包含匹配的行号、列号和内容片段
    """
    try:
        result = manager.search_in_cache(
            request.cache_id,
            request.keyword,
            request.case_sensitive,
            request.max_results
        )
        return {"success": True, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/get-cache-context")
async def get_cache_context(request: GetCacheContextRequest):
    """
    获取缓存中指定行的上下文
    
    请求体:
        - cache_id: 缓存ID
        - line_num: 目标行号（从1开始）
        - context_lines: 上下文行数（可选，默认3）
    
    返回:
        目标行及其上下文内容
    """
    try:
        result = manager.get_context_around_line(
            request.cache_id,
            request.line_num,
            request.context_lines
        )
        return {"success": True, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def signal_handler(sig, frame):
    """处理终止信号"""
    print("\n接收到终止信号，正在关闭...")
    sys.exit(0)


if __name__ == "__main__":
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description=f'MCP Bridge Server v{__version__}',
        epilog='详细文档: https://github.com/your-repo/mcp-bridge-server'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'MCP Bridge Server v{__version__}'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=PORT, 
        help=f'服务器端口 (默认: {PORT})'
    )
    parser.add_argument(
        '--auto-kill-port',
        action='store_true',
        help='自动结束占用端口的进程'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径'
    )
    args = parser.parse_args()
    
    # 更新端口
    PORT = args.port
    
    # 设置配置文件路径环境变量
    if args.config:
        os.environ['MCP_CONFIG_PATH'] = args.config
    
    # 检查端口
    print(f"MCP Bridge Server v{__version__}")
    print(f"正在检查端口 {PORT}...")
    
    if not check_and_handle_port(PORT, args.auto_kill_port):
        print("\n无法启动服务器: 端口不可用")
        sys.exit(1)
    
    print(f"✓ 端口 {PORT} 可用\n")
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动服务器
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=PORT,
            log_level="info"
        )
    except OSError as e:
        if "address already in use" in str(e).lower():
            print(f"\n✗ 错误: 端口 {PORT} 已被占用")
            print(f"   请使用 --port 参数指定其他端口，或使用 --auto-kill-port 自动结束占用进程")
        else:
            print(f"\n✗ 启动失败: {e}")
        sys.exit(1)