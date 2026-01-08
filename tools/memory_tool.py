"""记忆/知识库查询工具 - 使用 MCP 协议"""

from typing import Dict, Any, Optional, List
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


class MemoryTool:
    """记忆/知识库查询工具 - 使用 MCP 协议"""
    
    def __init__(self):
        """初始化记忆工具"""
        # MCP 服务配置
        self.mcp_command = os.getenv("MEMORY_MCP_COMMAND", "npx")
        mcp_args_str = os.getenv("MEMORY_MCP_ARGS", "-y @modelcontextprotocol/server-memory")
        self.mcp_args = mcp_args_str.split() if " " in mcp_args_str else mcp_args_str.split(",")
        
        # 如果没有配置 MCP，使用模拟数据
        self.use_mcp = MCP_AVAILABLE and self.mcp_command
    
    async def search_memory(
        self,
        query: str,
        limit: Optional[int] = 5
    ) -> Dict[str, Any]:
        """
        搜索记忆/知识库
        
        Args:
            query: 搜索查询
            limit: 返回结果数量限制
            
        Returns:
            搜索结果
        """
        logger.info(f"搜索记忆: {query}")
        
        if self.use_mcp:
            try:
                return await self._search_via_mcp(query, limit)
            except Exception as e:
                logger.warning(f"MCP 记忆搜索失败: {e}，使用模拟数据")
                return await self._mock_search(query, limit)
        else:
            return await self._mock_search(query, limit)
    
    async def store_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        存储记忆/知识
        
        Args:
            content: 内容
            metadata: 元数据（可选）
            
        Returns:
            存储结果
        """
        logger.info(f"存储记忆: {content[:50]}...")
        
        if self.use_mcp:
            try:
                return await self._store_via_mcp(content, metadata)
            except Exception as e:
                logger.warning(f"MCP 记忆存储失败: {e}")
                return {"success": False, "error": str(e)}
        else:
            return {"success": False, "error": "MCP 不可用"}
    
    async def _search_via_mcp(self, query: str, limit: int) -> Dict[str, Any]:
        """通过 MCP 协议搜索记忆"""
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
                    logger.info(f"Memory MCP 可用工具: {[tool.name for tool in tools.tools]}")
                    
                    # 查找搜索工具（Memory MCP 使用 search_nodes）
                    search_tool = None
                    for tool in tools.tools:
                        if tool.name == "search_nodes" or "search" in tool.name.lower():
                            search_tool = tool
                            break
                    
                    if not search_tool:
                        # 如果没有找到，尝试使用 read_graph 或其他工具
                        for tool in tools.tools:
                            if "read" in tool.name.lower() or "query" in tool.name.lower():
                                search_tool = tool
                                break
                    
                    if not search_tool:
                        raise Exception("未找到搜索工具")
                    
                    # 调用工具搜索
                    arguments = {"query": query}
                    if limit:
                        arguments["limit"] = limit
                    
                    logger.info(f"调用记忆搜索工具: {search_tool.name}, arguments={arguments}")
                    result = await session.call_tool(search_tool.name, arguments=arguments)
                    
                    # 解析结果
                    if result.content:
                        content = result.content[0] if result.content else {}
                        if hasattr(content, 'text'):
                            import json
                            try:
                                data = json.loads(content.text)
                            except:
                                data = {"results": [{"content": content.text}]}
                        else:
                            data = content
                        
                        return {
                            "success": True,
                            "query": query,
                            "results": data.get("results", data.get("data", [])),
                            "count": len(data.get("results", data.get("data", []))),
                            "source": "Memory MCP (真实MCP服务)"
                        }
                    else:
                        raise Exception("MCP 服务返回空结果")
                        
        except Exception as e:
            logger.error(f"MCP 记忆搜索失败: {e}", exc_info=True)
            raise
    
    async def _store_via_mcp(self, content: str, metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """通过 MCP 协议存储记忆"""
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
                    
                    # 查找存储工具
                    store_tool = None
                    for tool in tools.tools:
                        if "store" in tool.name.lower() or "save" in tool.name.lower() or "create" in tool.name.lower():
                            store_tool = tool
                            break
                    
                    if not store_tool:
                        raise Exception("未找到存储工具")
                    
                    # 调用工具存储
                    arguments = {"content": content}
                    if metadata:
                        arguments.update(metadata)
                    
                    logger.info(f"调用记忆存储工具: {store_tool.name}")
                    result = await session.call_tool(store_tool.name, arguments=arguments)
                    
                    return {
                        "success": True,
                        "message": "记忆已存储",
                        "source": "Memory MCP (真实MCP服务)"
                    }
                        
        except Exception as e:
            logger.error(f"MCP 记忆存储失败: {e}", exc_info=True)
            raise
    
    async def _mock_search(self, query: str, limit: int) -> Dict[str, Any]:
        """模拟搜索（回退方案）"""
        # 模拟知识库
        mock_kb = {
            "订单": [
                {"content": "订单查询：可以通过订单号查询订单状态", "score": 0.9},
                {"content": "订单取消：订单在发货前可以取消", "score": 0.8}
            ],
            "退款": [
                {"content": "退款申请：7天内可以申请退款", "score": 0.9},
                {"content": "退款流程：提交申请后3-5个工作日处理", "score": 0.8}
            ],
            "产品": [
                {"content": "产品咨询：我们有多种产品可供选择", "score": 0.9}
            ]
        }
        
        results = []
        query_lower = query.lower()
        for category, items in mock_kb.items():
            if category in query_lower or any(keyword in query_lower for keyword in ["订单", "退款", "产品"]):
                results.extend(items)
        
        return {
            "success": True,
            "query": query,
            "results": results[:limit],
            "count": len(results[:limit]),
            "source": "模拟数据"
        }
