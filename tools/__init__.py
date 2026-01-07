"""工具模块"""

import sys
from pathlib import Path

# 确保可以导入项目模块
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from .mcp_tools import MCPToolManager
    from .knowledge_base_tool import KnowledgeBaseTool
    from .order_query_tool import OrderQueryTool
except ImportError:
    from tools.mcp_tools import MCPToolManager
    from tools.knowledge_base_tool import KnowledgeBaseTool
    from tools.order_query_tool import OrderQueryTool

__all__ = ["MCPToolManager", "KnowledgeBaseTool", "OrderQueryTool"]
