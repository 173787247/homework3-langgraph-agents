"""测试日期查询数据格式"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools.mcp_tools import MCPToolManager
from utils.logger import setup_logging

setup_logging(level="INFO")

async def test():
    tool = MCPToolManager()
    result = await tool.get_date_info()
    print("=" * 50)
    print("get_date_info 返回结果:")
    print("=" * 50)
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 50)
    print(f"success: {result.get('success')}")
    print(f"data: {result.get('data')}")
    if result.get('data'):
        data = result.get('data')
        print(f"data.success: {data.get('success')}")
        print(f"data.date: {data.get('date')}")
        print(f"data.weekday: {data.get('weekday')}")

if __name__ == "__main__":
    asyncio.run(test())
