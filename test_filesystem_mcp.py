"""测试文件系统 MCP 服务"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools.filesystem_tool import FilesystemTool
from utils.logger import setup_logging, get_logger

# 设置日志
setup_logging(level="INFO")
logger = get_logger(__name__)


async def test_filesystem_mcp():
    """测试文件系统 MCP 服务"""
    print("=" * 50)
    print("测试文件系统 MCP 服务")
    print("=" * 50)
    
    tool = FilesystemTool()
    print(f"使用 MCP: {tool.use_mcp}")
    print(f"MCP 命令: {tool.mcp_command}")
    print(f"MCP 参数: {tool.mcp_args}")
    print()
    
    # 测试列出目录
    print("测试列出目录: /app/data")
    try:
        result = await tool.list_directory("/app/data")
        print(f"查询成功: {result.get('success')}")
        if result.get('success'):
            files = result.get('files', [])
            print(f"找到 {len(files)} 个文件/目录")
            print(f"数据来源: {result.get('source')}")
            if files:
                print(f"第一个文件: {files[0]}")
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
    asyncio.run(test_filesystem_mcp())
