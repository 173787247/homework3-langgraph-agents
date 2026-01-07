"""简单的导入测试 - 用于调试"""

import sys
from pathlib import Path

# 确保项目根目录在路径中
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("=" * 60)
print("简单导入测试")
print("=" * 60)
print(f"项目根目录: {project_root}")
print(f"Python 路径: {sys.path[:3]}")
print()

# 测试 1: 基础模块
print("1. 测试 utils.logger...")
try:
    from utils.logger import get_logger
    print("   ✅ 成功")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 2: BaseAgent
print("\n2. 测试 agents.base_agent...")
try:
    from agents.base_agent import BaseAgent
    print("   ✅ 成功")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 3: ReceptionistAgent
print("\n3. 测试 agents.receptionist_agent...")
try:
    from agents.receptionist_agent import ReceptionistAgent
    print("   ✅ 成功")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 4: 从 __init__ 导入
print("\n4. 测试从 agents 包导入...")
try:
    import agents
    print(f"   agents 包: {agents}")
    print(f"   BaseAgent: {agents.BaseAgent}")
    print("   ✅ 成功")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
