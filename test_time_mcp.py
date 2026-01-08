"""测试时间 MCP 服务"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools.time_tool import TimeTool
from utils.logger import setup_logging, get_logger

# 设置日志
setup_logging(level="INFO")
logger = get_logger(__name__)


async def test_time_mcp():
    """测试时间 MCP 服务"""
    print("=" * 50)
    print("测试时间 MCP 服务")
    print("=" * 50)
    
    tool = TimeTool()
    print(f"使用 MCP: {tool.use_mcp}")
    print(f"MCP 命令: {tool.mcp_command}")
    print(f"MCP 参数: {tool.mcp_args}")
    print()
    
    # 测试查询当前时间
    print("测试查询当前时间")
    try:
        result = await tool.get_current_time()
        print(f"查询成功: {result.get('success')}")
        if result.get('success'):
            print(f"时间: {result.get('time')}")
            print(f"时区: {result.get('timezone')}")
            print(f"数据来源: {result.get('source')}")
        else:
            print(f"错误: {result.get('error')}")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # 测试查询日期信息
    print("测试查询日期信息")
    try:
        result = await tool.get_date_info()
        print(f"查询成功: {result.get('success')}")
        if result.get('success'):
            print(f"日期: {result.get('date')}")
            print(f"星期: {result.get('weekday')}")
            print(f"年: {result.get('year')}")
            print(f"月: {result.get('month')}")
            print(f"日: {result.get('day')}")
            print(f"数据来源: {result.get('source')}")
        else:
            print(f"错误: {result.get('error')}")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    print("=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_time_mcp())
