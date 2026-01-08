"""工具模块"""

import sys
from pathlib import Path

# 确保可以导入项目模块
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from .mcp_tools import MCPToolManager
    from .weather_tool import WeatherTool
    from .amap_tool import AmapTool
    from .time_tool import TimeTool
    from .memory_tool import MemoryTool
    from .filesystem_tool import FilesystemTool
except ImportError:
    from tools.mcp_tools import MCPToolManager
    from tools.weather_tool import WeatherTool
    from tools.amap_tool import AmapTool
    from tools.time_tool import TimeTool
    from tools.memory_tool import MemoryTool
    from tools.filesystem_tool import FilesystemTool

__all__ = ["MCPToolManager", "WeatherTool", "AmapTool", "TimeTool", "MemoryTool", "FilesystemTool"]
