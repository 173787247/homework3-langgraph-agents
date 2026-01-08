"""测试所有 MCP 服务"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools.time_tool import TimeTool
from tools.memory_tool import MemoryTool
from tools.filesystem_tool import FilesystemTool
from utils.logger import setup_logging, get_logger

# 设置日志
setup_logging(level="INFO")
logger = get_logger(__name__)


async def test_all_mcp():
    """测试所有 MCP 服务"""
    print("=" * 60)
    print("测试所有 MCP 服务")
    print("=" * 60)
    
    # 1. 测试时间 MCP
    print("\n1. 时间 MCP 服务")
    print("-" * 60)
    time_tool = TimeTool()
    result = await time_tool.get_current_time()
    print(f"✓ 时间查询: {result.get('source')}")
    
    # 2. 测试记忆 MCP
    print("\n2. 记忆/知识库 MCP 服务")
    print("-" * 60)
    memory_tool = MemoryTool()
    result = await memory_tool.search_memory("订单查询")
    print(f"✓ 知识库搜索: {result.get('source')}, 找到 {result.get('count', 0)} 条结果")
    
    # 3. 测试文件系统 MCP
    print("\n3. 文件系统 MCP 服务")
    print("-" * 60)
    fs_tool = FilesystemTool()
    result = await fs_tool.list_directory("/app/data")
    print(f"✓ 目录列表: {result.get('source')}")
    
    print("\n" + "=" * 60)
    print("所有 MCP 服务测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_all_mcp())
