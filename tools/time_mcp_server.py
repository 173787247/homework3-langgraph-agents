"""时间 MCP 服务器（Python 实现）"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Sequence
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_SERVER_AVAILABLE = True
except ImportError:
    MCP_SERVER_AVAILABLE = False
    print("MCP Server SDK 不可用", file=sys.stderr)
    sys.exit(1)


if MCP_SERVER_AVAILABLE:
    # 创建 MCP 服务器
    app = Server("time-server")
    
    @app.list_tools()
    async def list_tools() -> list[Tool]:
        """列出可用工具"""
        return [
            Tool(
                name="get_current_time",
                description="获取当前时间",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "时区（可选，如：Asia/Shanghai, UTC）"
                        }
                    }
                }
            ),
            Tool(
                name="get_date_info",
                description="获取日期信息（今天几号、星期几等）",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]
    
    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
        """调用工具"""
        if name == "get_current_time":
            timezone = arguments.get("timezone")
            now = datetime.now()
            result = {
                "time": now.strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": timezone or "本地时区",
                "timestamp": now.timestamp()
            }
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
        elif name == "get_date_info":
            now = datetime.now()
            weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            result = {
                "date": now.strftime("%Y-%m-%d"),
                "year": now.year,
                "month": now.month,
                "day": now.day,
                "weekday": weekdays[now.weekday()],
                "time": now.strftime("%H:%M:%S")
            }
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
        else:
            raise ValueError(f"未知工具: {name}")
    
    async def main():
        """运行 MCP 服务器"""
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    
    if __name__ == "__main__":
        asyncio.run(main())
