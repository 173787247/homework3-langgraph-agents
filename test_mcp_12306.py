"""测试 12306 MCP 服务"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools.train_ticket_tool import TrainTicketTool
from utils.logger import setup_logging, get_logger

# 设置日志
setup_logging(level="INFO")
logger = get_logger(__name__)


async def test_mcp_12306():
    """测试 12306 MCP 服务"""
    print("=" * 50)
    print("测试 12306 MCP 服务")
    print("=" * 50)
    
    tool = TrainTicketTool()
    print(f"服务类型: {tool.service_type}")
    print(f"使用模拟数据: {tool.use_mock}")
    print(f"MCP 命令: {tool.mcp_command}")
    print(f"MCP 参数: {tool.mcp_args}")
    print()
    
    # 测试查询
    print("测试查询：北京 -> 上海")
    try:
        result = await tool.query_trains("北京", "上海")
        print(f"查询成功: {result.get('success')}")
        if result.get('success'):
            print(f"出发站: {result.get('from_station')}")
            print(f"到达站: {result.get('to_station')}")
            print(f"日期: {result.get('date')}")
            print(f"数据来源: {result.get('source', '未知')}")
            trains = result.get('trains', [])
            print(f"找到 {len(trains)} 个车次")
            if trains:
                print(f"第一个车次: {trains[0].get('train_no', 'N/A')}")
        else:
            print(f"错误: {result.get('error', '未知错误')}")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_mcp_12306())
