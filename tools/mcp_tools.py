"""MCP 工具管理器"""

from typing import Dict, Any, Optional
import aiohttp
import os

import sys
from pathlib import Path

# 确保可以导入项目模块
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入工具类
from tools.knowledge_base_tool import KnowledgeBaseTool
from tools.order_query_tool import OrderQueryTool
from utils.logger import get_logger

logger = get_logger(__name__)


class MCPToolManager:
    """MCP 工具管理器"""
    
    def __init__(self):
        """初始化工具管理器"""
        self.knowledge_base_tool = KnowledgeBaseTool()
        self.order_query_tool = OrderQueryTool()
        
        # MCP 服务器配置
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
    
    async def query_knowledge_base(
        self,
        query: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询知识库
        
        Args:
            query: 查询内容
            category: 问题类别
            
        Returns:
            查询结果
        """
        try:
            result = await self.knowledge_base_tool.query(query, category)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            logger.error(f"知识库查询失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def query_order(self, order_id: str) -> Dict[str, Any]:
        """
        查询订单信息
        
        Args:
            order_id: 订单号
            
        Returns:
            订单信息
        """
        try:
            result = await self.order_query_tool.query(order_id)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            logger.error(f"订单查询失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def call_mcp_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调用 MCP 工具
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            
        Returns:
            工具执行结果
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.mcp_server_url}/tools/{tool_name}",
                    json=parameters,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"MCP工具调用失败: {response.status}")
        except Exception as e:
            logger.error(f"MCP工具调用失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
