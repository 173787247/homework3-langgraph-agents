"""主入口文件 - 命令行交互模式"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# DeepSeek 支持（可选，如果 langchain_community 版本支持）
try:
    from langchain_community.chat_models import ChatDeepSeek
except ImportError:
    # 如果导入失败，使用 OpenAI 兼容方式
    ChatDeepSeek = None

from workflow.customer_service_graph import CustomerServiceGraph
from memory.memory_store import MemoryStore
from utils.logger import setup_logging, get_logger

# 加载环境变量
load_dotenv()

# 设置日志
setup_logging(level="INFO")
logger = get_logger(__name__)


def create_llm():
    """创建语言模型"""
    provider = os.getenv("LLM_PROVIDER", "deepseek").lower()
    
    if provider == "deepseek":
        if ChatDeepSeek is None:
            raise ValueError("ChatDeepSeek 不可用，请使用 OpenAI 或安装支持 DeepSeek 的 langchain_community 版本")
        
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            # 如果没有设置 DEEPSEEK_API_KEY，尝试使用 OPENAI_API_KEY（兼容性）
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量")
        
        return ChatDeepSeek(
            model=os.getenv("LLM_MODEL", "deepseek-chat"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            api_key=api_key
        )
    else:  # openai
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("请设置 OPENAI_API_KEY 环境变量")
        
        return ChatOpenAI(
            model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            api_key=api_key
        )


async def main():
    """主函数"""
    print("=" * 60)
    print("多角色协作智能客服系统")
    print("=" * 60)
    print()
    
    try:
        # 初始化组件
        print("正在初始化系统...")
        
        # 先检查环境变量
        provider_env = os.getenv("LLM_PROVIDER", "deepseek").lower()
        print(f"环境变量 LLM_PROVIDER: {provider_env}")
        
        llm = create_llm()
        
        # 根据实际创建的 LLM 类型判断
        if ChatDeepSeek and isinstance(llm, ChatDeepSeek):
            provider = "deepseek"
            model = os.getenv("LLM_MODEL", "deepseek-chat")
        else:
            provider = "openai"
            model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        
        print(f"实际使用的 LLM 提供商: {provider.upper()}")
        print(f"实际使用的 LLM 模型: {model}")
        
        memory_store = MemoryStore()
        graph = CustomerServiceGraph(llm=llm, memory_store=memory_store)
        print("系统初始化完成！")
        print()
        
        # 获取用户ID
        user_id = input("请输入您的用户ID（直接回车使用默认ID）: ").strip()
        if not user_id:
            user_id = "default_user"
        
        session_id = None
        
        print()
        print("开始对话（输入 'quit' 或 'exit' 退出）")
        print("-" * 60)
        
        while True:
            # 获取用户输入
            user_input = input("\n您: ").strip()
            
            if user_input.lower() in ["quit", "exit", "退出"]:
                print("\n感谢使用，再见！")
                break
            
            if not user_input:
                continue
            
            # 处理消息
            try:
                result = await graph.process_message(
                    user_id=user_id,
                    message=user_input,
                    session_id=session_id
                )
                
                session_id = result.get("session_id")
                response = result.get("response", "抱歉，我无法理解您的问题。")
                
                print(f"\n助手: {response}")
                
                # 如果需要人工介入
                if result.get("needs_human_intervention"):
                    print("\n[提示] 系统建议转接人工客服，请稍候...")
                
            except Exception as e:
                logger.error(f"处理消息失败: {e}")
                print(f"\n抱歉，处理过程中出现了错误: {e}")
    
    except KeyboardInterrupt:
        print("\n\n程序已中断")
    except Exception as e:
        logger.error(f"程序运行失败: {e}")
        print(f"\n程序运行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
