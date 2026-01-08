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
from tools.weather_tool import WeatherTool
from tools.amap_tool import AmapTool
from tools.time_tool import TimeTool
from tools.memory_tool import MemoryTool
from tools.filesystem_tool import FilesystemTool
from utils.logger import get_logger

logger = get_logger(__name__)


class MCPToolManager:
    """MCP 工具管理器"""
    
    def __init__(self):
        """初始化工具管理器"""
        # 使用真实的 MCP 工具
        self.weather_tool = WeatherTool()
        self.amap_tool = AmapTool()
        self.time_tool = TimeTool()
        self.memory_tool = MemoryTool()
        self.filesystem_tool = FilesystemTool()
        
        # MCP 服务器配置
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
    
    async def query_weather(
        self,
        city: str,
        country: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询天气信息（免费API）
        
        Args:
            city: 城市名称
            country: 国家代码（可选）
            
        Returns:
            天气信息
        """
        try:
            result = await self.weather_tool.query_weather(city, country)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            logger.error(f"天气查询失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def query_address(
        self,
        address: str,
        city: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询地址信息（高德地图）
        
        Args:
            address: 地址
            city: 城市（可选）
            
        Returns:
            地址信息（包含经纬度等）
        """
        try:
            result = await self.amap_tool.geocode(address, city)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            logger.error(f"地址查询失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_location(
        self,
        keywords: str,
        city: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        搜索地点（高德地图 POI 搜索）
        
        Args:
            keywords: 关键词
            city: 城市（可选）
            
        Returns:
            POI 列表
        """
        try:
            result = await self.amap_tool.search_poi(keywords, city)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            logger.error(f"地点搜索失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def query_time(
        self,
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询时间信息（MCP 服务）
        
        Args:
            timezone: 时区（可选）
            
        Returns:
            时间信息
        """
        try:
            result = await self.time_tool.get_current_time(timezone)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            logger.error(f"时间查询失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_date_info(self) -> Dict[str, Any]:
        """
        获取日期信息（今天几号、星期几等）
        
        Returns:
            日期信息
        """
        try:
            result = await self.time_tool.get_date_info()
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            logger.error(f"日期查询失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_knowledge_base(
        self,
        query: str,
        limit: Optional[int] = 5
    ) -> Dict[str, Any]:
        """
        搜索知识库（Memory MCP）
        
        Args:
            query: 搜索查询
            limit: 返回结果数量限制
            
        Returns:
            搜索结果
        """
        try:
            result = await self.memory_tool.search_memory(query, limit)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            logger.error(f"知识库搜索失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def read_file(
        self,
        file_path: str
    ) -> Dict[str, Any]:
        """
        读取文件（Filesystem MCP）
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容
        """
        try:
            result = await self.filesystem_tool.read_file(file_path)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            logger.error(f"文件读取失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_directory(
        self,
        dir_path: str
    ) -> Dict[str, Any]:
        """
        列出目录内容（Filesystem MCP）
        
        Args:
            dir_path: 目录路径
            
        Returns:
            目录内容
        """
        try:
            result = await self.filesystem_tool.list_directory(dir_path)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            logger.error(f"目录列表失败: {e}")
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
