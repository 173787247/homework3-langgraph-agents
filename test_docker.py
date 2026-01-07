"""Docker 环境测试脚本"""

import sys
import os
from pathlib import Path

# 设置 Windows 控制台编码为 UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试导入"""
    print("=" * 60)
    print("测试模块导入")
    print("=" * 60)
    
    # 确保项目根目录在路径中
    project_root = Path(__file__).parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    try:
        print("1. 测试基础模块...")
        from utils.logger import get_logger, setup_logging
        print("   ✅ utils.logger 导入成功")
        
        print("2. 测试智能体模块...")
        # 直接测试单个模块导入，不通过 __init__.py
        try:
            from agents.base_agent import BaseAgent
            print("   ✅ BaseAgent 导入成功")
        except Exception as e:
            print(f"   ❌ BaseAgent 导入失败: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        try:
            from agents.receptionist_agent import ReceptionistAgent
            print("   ✅ ReceptionistAgent 导入成功")
        except Exception as e:
            print(f"   ❌ ReceptionistAgent 导入失败: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        try:
            from agents.analyst_agent import AnalystAgent
            print("   ✅ AnalystAgent 导入成功")
        except Exception as e:
            print(f"   ❌ AnalystAgent 导入失败: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        try:
            from agents.solution_expert_agent import SolutionExpertAgent
            print("   ✅ SolutionExpertAgent 导入成功")
        except Exception as e:
            print(f"   ❌ SolutionExpertAgent 导入失败: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        print("   ✅ agents 模块导入成功")
        
        print("3. 测试工作流模块...")
        from workflow.state import CustomerServiceState
        print("   ✅ CustomerServiceState 导入成功")
        from workflow.customer_service_graph import CustomerServiceGraph
        print("   ✅ CustomerServiceGraph 导入成功")
        print("   ✅ workflow 模块导入成功")
        
        print("4. 测试工具模块...")
        from tools.knowledge_base_tool import KnowledgeBaseTool
        from tools.order_query_tool import OrderQueryTool
        from tools.mcp_tools import MCPToolManager
        print("   ✅ tools 模块导入成功")
        
        print("5. 测试记忆模块...")
        from memory.memory_store import MemoryStore
        from memory.conversation_manager import ConversationManager
        print("   ✅ memory 模块导入成功")
        
        print("\n" + "=" * 60)
        print("✅ 所有模块导入成功！")
        print("=" * 60)
        return True
        
    except ImportError as e:
        import traceback
        print(f"\n❌ 导入失败: {e}")
        print(f"详细错误:\n{traceback.format_exc()}")
        return False
    except Exception as e:
        import traceback
        print(f"\n❌ 测试失败: {e}")
        print(f"详细错误:\n{traceback.format_exc()}")
        return False


def test_dependencies():
    """测试依赖"""
    print("\n" + "=" * 60)
    print("测试依赖包")
    print("=" * 60)
    
    dependencies = [
        ("langgraph", "langgraph"),
        ("langchain", "langchain"),
        ("langchain_openai", "langchain_openai"),
        ("langchain_community", "langchain_community"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pydantic", "pydantic"),
        ("sqlalchemy", "sqlalchemy"),
        ("aiosqlite", "aiosqlite"),
        ("python-dotenv", "dotenv"),  # 安装名是 python-dotenv，导入是 dotenv
        ("pyyaml", "yaml"),  # 安装名是 pyyaml，导入是 yaml
        ("loguru", "loguru")
    ]
    
    failed = []
    for install_name, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"   ✅ {install_name}")
        except ImportError:
            print(f"   ❌ {install_name} (未安装)")
            failed.append(install_name)
    
    if failed:
        print(f"\n❌ 以下依赖未安装: {', '.join(failed)}")
        print("   请运行: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ 所有依赖已安装！")
        return True


def test_gpu():
    """测试 GPU"""
    print("\n" + "=" * 60)
    print("测试 GPU 支持")
    print("=" * 60)
    
    try:
        import torch
        print(f"   PyTorch 版本: {torch.__version__}")
        
        if torch.cuda.is_available():
            print(f"   ✅ GPU 可用")
            print(f"   GPU 设备数量: {torch.cuda.device_count()}")
            print(f"   当前 GPU: {torch.cuda.get_device_name(0)}")
            print(f"   CUDA 版本: {torch.version.cuda}")
            return True
        else:
            print("   ⚠️  GPU 不可用（CPU 模式）")
            return False
    except ImportError:
        print("   ⚠️  PyTorch 未安装（不影响 LangGraph 运行）")
        return False
    except Exception as e:
        print(f"   ⚠️  GPU 测试失败: {e}")
        return False


def test_database():
    """测试数据库"""
    print("\n" + "=" * 60)
    print("测试数据库连接")
    print("=" * 60)
    
    # 确保项目根目录在路径中
    project_root = Path(__file__).parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    try:
        from memory.memory_store import MemoryStore
        
        # 创建测试数据库
        test_db_path = "./data/test_conversations.db"
        os.makedirs(os.path.dirname(test_db_path), exist_ok=True)
        
        memory_store = MemoryStore(db_path=test_db_path)
        print("   ✅ 数据库初始化成功")
        
        # 清理测试数据库
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        return True
    except Exception as e:
        import traceback
        print(f"   ❌ 数据库测试失败: {e}")
        print(f"   详细错误:\n{traceback.format_exc()}")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Docker 环境测试")
    print("=" * 60)
    print()
    
    results = []
    
    # 测试导入
    results.append(("模块导入", test_imports()))
    
    # 测试依赖
    results.append(("依赖包", test_dependencies()))
    
    # 测试 GPU
    results.append(("GPU 支持", test_gpu()))
    
    # 测试数据库
    results.append(("数据库", test_database()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统可以正常运行。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试未通过，请检查相关配置。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
