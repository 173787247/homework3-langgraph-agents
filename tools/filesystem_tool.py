"""文件系统工具 - 使用 MCP 协议"""

from typing import Dict, Any, Optional
import os

import sys
from pathlib import Path

# 确保可以导入项目模块
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger

logger = get_logger(__name__)

# 尝试导入 MCP SDK
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("MCP SDK 不可用")


class FilesystemTool:
    """文件系统工具 - 使用 MCP 协议"""
    
    def __init__(self):
        """初始化文件系统工具"""
        # MCP 服务配置
        # Filesystem MCP 需要指定允许访问的目录
        self.mcp_command = os.getenv("FILESYSTEM_MCP_COMMAND", "npx")
        # 默认允许访问的目录：/app/data, /app/logs, /app/cache
        default_dirs = "/app/data /app/logs /app/cache"
        mcp_args_str = os.getenv("FILESYSTEM_MCP_ARGS", f"-y @modelcontextprotocol/server-filesystem {default_dirs}")
        self.mcp_args = mcp_args_str.split() if " " in mcp_args_str else mcp_args_str.split(",")
        
        # 允许访问的目录（安全限制）
        self.allowed_dirs = [
            "/app/data",
            "/app/logs",
            "/app/cache"
        ]
        
        # 如果没有配置 MCP，使用系统文件操作
        self.use_mcp = MCP_AVAILABLE and self.mcp_command
    
    async def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容
        """
        logger.info(f"读取文件: {file_path}")
        
        # 安全检查
        if not self._is_path_allowed(file_path):
            return {
                "success": False,
                "error": f"路径不在允许范围内: {file_path}"
            }
        
        if self.use_mcp:
            try:
                return await self._read_via_mcp(file_path)
            except Exception as e:
                logger.warning(f"MCP 文件读取失败: {e}，使用系统文件操作")
                return await self._read_system_file(file_path)
        else:
            return await self._read_system_file(file_path)
    
    async def list_directory(self, dir_path: str) -> Dict[str, Any]:
        """
        列出目录内容
        
        Args:
            dir_path: 目录路径
            
        Returns:
            目录内容列表
        """
        logger.info(f"列出目录: {dir_path}")
        
        # 安全检查
        if not self._is_path_allowed(dir_path):
            return {
                "success": False,
                "error": f"路径不在允许范围内: {dir_path}"
            }
        
        if self.use_mcp:
            try:
                return await self._list_via_mcp(dir_path)
            except Exception as e:
                logger.warning(f"MCP 目录列表失败: {e}，使用系统文件操作")
                return await self._list_system_directory(dir_path)
        else:
            return await self._list_system_directory(dir_path)
    
    def _is_path_allowed(self, path: str) -> bool:
        """检查路径是否在允许范围内"""
        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(allowed) for allowed in self.allowed_dirs)
    
    async def _read_via_mcp(self, file_path: str) -> Dict[str, Any]:
        """通过 MCP 协议读取文件"""
        if not MCP_AVAILABLE:
            raise Exception("MCP SDK 不可用")
        
        try:
            # 配置 MCP 服务器参数
            server_params = StdioServerParameters(
                command=self.mcp_command,
                args=self.mcp_args
            )
            
            # 连接到 MCP 服务器
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # 初始化会话
                    await session.initialize()
                    
                    # 列出可用工具
                    tools = await session.list_tools()
                    logger.info(f"Filesystem MCP 可用工具: {[tool.name for tool in tools.tools]}")
                    
                    # 查找读取文件工具
                    read_tool = None
                    for tool in tools.tools:
                        if "read" in tool.name.lower() and "file" in tool.name.lower():
                            read_tool = tool
                            break
                    
                    if not read_tool:
                        raise Exception("未找到文件读取工具")
                    
                    # 调用工具读取文件
                    logger.info(f"调用文件读取工具: {read_tool.name}, path={file_path}")
                    result = await session.call_tool(
                        read_tool.name,
                        arguments={"path": file_path}
                    )
                    
                    # 解析结果
                    if result.content:
                        content = result.content[0] if result.content else {}
                        if hasattr(content, 'text'):
                            return {
                                "success": True,
                                "path": file_path,
                                "content": content.text,
                                "source": "Filesystem MCP (真实MCP服务)"
                            }
                    else:
                        raise Exception("MCP 服务返回空结果")
                        
        except Exception as e:
            logger.error(f"MCP 文件读取失败: {e}", exc_info=True)
            raise
    
    async def _list_via_mcp(self, dir_path: str) -> Dict[str, Any]:
        """通过 MCP 协议列出目录"""
        if not MCP_AVAILABLE:
            raise Exception("MCP SDK 不可用")
        
        try:
            # 配置 MCP 服务器参数
            server_params = StdioServerParameters(
                command=self.mcp_command,
                args=self.mcp_args
            )
            
            # 连接到 MCP 服务器
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # 初始化会话
                    await session.initialize()
                    
                    # 列出可用工具
                    tools = await session.list_tools()
                    
                    # 查找列出目录工具（Filesystem MCP 使用 list_directory）
                    list_tool = None
                    for tool in tools.tools:
                        if tool.name == "list_directory" or tool.name == "list_directories":
                            list_tool = tool
                            break
                    
                    # 如果没找到，尝试其他可能的名称
                    if not list_tool:
                        for tool in tools.tools:
                            if "list" in tool.name.lower() and "directory" in tool.name.lower():
                                list_tool = tool
                                break
                    
                    if not list_tool:
                        raise Exception("未找到目录列表工具")
                    
                    # 调用工具列出目录
                    logger.info(f"调用目录列表工具: {list_tool.name}, path={dir_path}")
                    result = await session.call_tool(
                        list_tool.name,
                        arguments={"path": dir_path}
                    )
                    
                    # 解析结果
                    if result.content:
                        content = result.content[0] if result.content else {}
                        if hasattr(content, 'text'):
                            import json
                            try:
                                data = json.loads(content.text)
                            except:
                                data = {"files": content.text.split("\n")}
                            
                            return {
                                "success": True,
                                "path": dir_path,
                                "files": data.get("files", data.get("entries", [])),
                                "source": "Filesystem MCP (真实MCP服务)"
                            }
                    else:
                        raise Exception("MCP 服务返回空结果")
                        
        except Exception as e:
            logger.error(f"MCP 目录列表失败: {e}", exc_info=True)
            raise
    
    async def _read_system_file(self, file_path: str) -> Dict[str, Any]:
        """使用系统文件操作读取文件（回退方案）"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                "success": True,
                "path": file_path,
                "content": content,
                "source": "系统文件操作"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "source": "系统文件操作"
            }
    
    async def _list_system_directory(self, dir_path: str) -> Dict[str, Any]:
        """使用系统文件操作列出目录（回退方案）"""
        try:
            files = []
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                files.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file"
                })
            return {
                "success": True,
                "path": dir_path,
                "files": files,
                "source": "系统文件操作"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "source": "系统文件操作"
            }
