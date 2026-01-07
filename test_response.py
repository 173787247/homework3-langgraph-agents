"""测试回复提取"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from workflow.customer_service_graph import CustomerServiceGraph
from memory.memory_store import MemoryStore
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
        api_key=os.getenv("OPENAI_API_KEY")
    )
    graph = CustomerServiceGraph(llm=llm, memory_store=MemoryStore())
    
    result = await graph.process_message("test_user", "我的订单什么时候能到?")
    
    print("=" * 50)
    print("Result keys:", list(result.keys()) if result else "None")
    print("Response:", result.get("response", "No response")[:500] if result else "No result")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test())
