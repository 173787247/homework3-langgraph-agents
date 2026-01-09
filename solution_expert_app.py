"""解决方案专家智能体独立服务 - 端口 8003"""

import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
try:
    from langchain_community.chat_models import ChatDeepSeek
except ImportError:
    ChatDeepSeek = None

from agents.solution_expert_agent import SolutionExpertAgent
from memory.memory_store import MemoryStore
from utils.logger import setup_logging, get_logger

load_dotenv()
setup_logging(level="INFO")
logger = get_logger(__name__)

app = FastAPI(
    title="解决方案专家智能体服务",
    description="基于分析结果提供专业解决方案",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = None
solution_expert_agent = None
memory_store = None

def create_llm():
    """创建LLM实例"""
    global llm
    provider = os.getenv("LLM_PROVIDER", "deepseek").lower()
    model = os.getenv("LLM_MODEL", "deepseek-chat")
    
    if provider == "deepseek" and ChatDeepSeek:
        llm = ChatDeepSeek(
            model=model,
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000"))
        )
    else:
        llm = ChatOpenAI(
            model=model if provider == "openai" else "gpt-3.5-turbo",
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000"))
        )
    return llm

@app.on_event("startup")
async def startup():
    """启动时初始化"""
    global solution_expert_agent, memory_store
    try:
        llm = create_llm()
        solution_expert_agent = SolutionExpertAgent(llm)
        memory_store = MemoryStore()
        logger.info("解决方案专家智能体服务启动成功")
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)

class SolutionRequest(BaseModel):
    user_id: str
    message: str
    analysis_result: Optional[dict] = None
    tool_results: Optional[dict] = None
    session_id: Optional[str] = None

class SolutionResponse(BaseModel):
    session_id: str
    response: str
    agent: str = "solution_expert"
    solution_result: Optional[dict] = None

@app.post("/api/solve", response_model=SolutionResponse)
async def solve(request: SolutionRequest):
    """解决方案专家智能体接口"""
    if solution_expert_agent is None:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    try:
        session_id = request.session_id or f"session_{request.user_id}"
        conversation_history = await memory_store.get_conversation_history(
            user_id=request.user_id,
            session_id=session_id
        )
        
        state = {
            "user_input": request.message,
            "conversation_history": conversation_history,
            "analysis_result": request.analysis_result or {},
            "tool_results": request.tool_results or {},
            "solution_result": None
        }
        
        result = await solution_expert_agent.process(state)
        
        return SolutionResponse(
            session_id=session_id,
            response=result.get("solution_result", {}).get("final_response", "解决方案已生成"),
            agent="solution_expert",
            solution_result=result.get("solution_result")
        )
    except Exception as e:
        logger.error(f"处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "agent": "solution_expert",
        "initialized": solution_expert_agent is not None
    }

@app.get("/")
async def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>解决方案专家智能体服务</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; color: #333; }
            h1 { color: #667eea; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💡 解决方案专家智能体服务</h1>
            <p>端口: <strong>8003</strong></p>
            <p>职责：基于分析结果提供专业解决方案</p>
            <p><a href="/docs">API 文档</a> | <a href="/api/health">健康检查</a></p>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
