"""时间查询工具 - 使用 MCP 协议"""

from typing import Dict, Any, Optional
import os
from datetime import datetime

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
    logger.warning("MCP SDK 不可用，将使用系统时间")


class TimeTool:
    """时间查询工具 - 使用 MCP 协议"""
    
    def __init__(self):
        """初始化时间查询工具"""
        # MCP 服务配置
        # 使用本地 Python MCP 服务器
        self.mcp_command = os.getenv("TIME_MCP_COMMAND", "python")
        # 注意：使用 -m 参数时，模块路径应该是 tools.time_mcp_server
        mcp_args_str = os.getenv("TIME_MCP_ARGS", "-m tools.time_mcp_server")
        self.mcp_args = mcp_args_str.split() if " " in mcp_args_str else mcp_args_str.split(",")
        
        # 如果没有配置 MCP，使用系统时间
        self.use_mcp = MCP_AVAILABLE and self.mcp_command
    
    async def get_current_time(
        self,
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取当前时间
        
        Args:
            timezone: 时区（可选，如：Asia/Shanghai, UTC）
            
        Returns:
            时间信息
        """
        logger.info(f"查询当前时间: timezone={timezone}")
        
        if self.use_mcp:
            try:
                return await self._query_via_mcp(timezone)
            except Exception as e:
                logger.warning(f"MCP 时间查询失败: {e}，使用系统时间")
                return await self._get_system_time(timezone)
        else:
            return await self._get_system_time(timezone)
    
    async def _query_via_mcp(self, timezone: Optional[str] = None) -> Dict[str, Any]:
        """通过 MCP 协议查询时间"""
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
                    logger.info(f"时间 MCP 可用工具: {[tool.name for tool in tools.tools]}")
                    
                    # 查找时间查询工具
                    time_tool = None
                    for tool in tools.tools:
                        if "time" in tool.name.lower() or "current" in tool.name.lower() or "now" in tool.name.lower():
                            time_tool = tool
                            break
                    
                    if not time_tool and tools.tools:
                        # 如果没有找到，使用第一个工具
                        time_tool = tools.tools[0]
                    
                    if not time_tool:
                        raise Exception("未找到时间查询工具")
                    
                    # 调用工具查询时间
                    arguments = {}
                    if timezone:
                        arguments["timezone"] = timezone
                    
                    logger.info(f"调用时间工具: {time_tool.name}, arguments={arguments}")
                    result = await session.call_tool(time_tool.name, arguments=arguments)
                    
                    # 解析结果
                    if result.content:
                        content = result.content[0] if result.content else {}
                        if hasattr(content, 'text'):
                            import json
                            try:
                                data = json.loads(content.text)
                            except:
                                # 如果不是 JSON，直接使用文本
                                data = {"time": content.text}
                        else:
                            data = content
                        
                        return {
                            "success": True,
                            "time": data.get("time") or data.get("current_time") or data.get("datetime", str(datetime.now())),
                            "timezone": data.get("timezone") or timezone or "UTC",
                            "source": "时间 MCP (真实MCP服务)"
                        }
                    else:
                        raise Exception("MCP 服务返回空结果")
                        
        except Exception as e:
            logger.error(f"MCP 时间查询失败: {e}", exc_info=True)
            raise
    
    async def _get_system_time(self, timezone: Optional[str] = None) -> Dict[str, Any]:
        """使用系统时间（回退方案）"""
        now = datetime.now()
        return {
            "success": True,
            "time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "time_str": now.strftime("%H:%M:%S"),
            "timezone": timezone or "本地时区",
            "source": "系统时间"
        }
    
    async def get_date_info(self) -> Dict[str, Any]:
        """
        获取日期信息（今天几号、星期几等）
        
        Returns:
            日期信息
        """
        logger.info("查询日期信息")
        
        if self.use_mcp:
            try:
                return await self._query_date_via_mcp()
            except Exception as e:
                logger.warning(f"MCP 日期查询失败: {e}，使用系统时间")
                return await self._get_system_date_info()
        else:
            return await self._get_system_date_info()
    
    async def _query_date_via_mcp(self) -> Dict[str, Any]:
        """通过 MCP 协议查询日期信息"""
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
                    
                    # 调用 get_date_info 工具
                    logger.info("调用 get_date_info 工具")
                    result = await session.call_tool("get_date_info", arguments={})
                    
                    # 解析结果
                    if result.content:
                        content = result.content[0] if result.content else {}
                        if hasattr(content, 'text'):
                            import json
                            data = json.loads(content.text)
                            return {
                                "success": True,
                                "date": data.get("date", ""),
                                "year": data.get("year", 0),
                                "month": data.get("month", 0),
                                "day": data.get("day", 0),
                                "weekday": data.get("weekday", ""),
                                "source": "时间 MCP (真实MCP服务)"
                            }
                    else:
                        raise Exception("MCP 服务返回空结果")
                        
        except Exception as e:
            logger.error(f"MCP 日期查询失败: {e}", exc_info=True)
            raise
    
    def _get_system_date_info(self) -> Dict[str, Any]:
        """使用系统时间获取日期信息（回退方案）"""
        dt = datetime.now()
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        return {
            "success": True,
            "date": dt.strftime("%Y-%m-%d"),
            "year": dt.year,
            "month": dt.month,
            "day": dt.day,
            "weekday": weekdays[dt.weekday()],
            "source": "系统时间"
        }
