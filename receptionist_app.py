"""接待员智能体独立服务 - 端口 8001"""

import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
try:
    from langchain_community.chat_models import ChatDeepSeek
except ImportError:
    ChatDeepSeek = None

from agents.receptionist_agent import ReceptionistAgent
from memory.memory_store import MemoryStore
from utils.logger import setup_logging, get_logger

load_dotenv()
setup_logging(level="INFO")
logger = get_logger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="接待员智能体服务",
    description="负责用户接待、问题初步分类和引导",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化
llm = None
receptionist_agent = None
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
    global receptionist_agent, memory_store
    try:
        llm = create_llm()
        receptionist_agent = ReceptionistAgent(llm)
        memory_store = MemoryStore()
        logger.info("接待员智能体服务启动成功")
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)

class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    response: str
    agent: str = "receptionist"

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """接待员智能体聊天接口"""
    if receptionist_agent is None:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    try:
        # 获取对话历史
        session_id = request.session_id or f"session_{request.user_id}"
        conversation_history = await memory_store.get_conversation_history(
            user_id=request.user_id,
            session_id=session_id
        )
        
        # 构建状态
        state = {
            "user_input": request.message,
            "conversation_history": conversation_history,
            "receptionist_result": None
        }
        
        # 调用接待员智能体
        result = await receptionist_agent.process(state)
        
        # 保存对话
        await memory_store.save_message(
            user_id=request.user_id,
            session_id=session_id,
            role="user",
            content=request.message
        )
        await memory_store.save_message(
            user_id=request.user_id,
            session_id=session_id,
            role="assistant",
            content=result.get("receptionist_result", {}).get("response", "")
        )
        
        return ChatResponse(
            session_id=session_id,
            response=result.get("receptionist_result", {}).get("response", "抱歉，我无法理解您的问题。"),
            agent="receptionist"
        )
    except Exception as e:
        logger.error(f"处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "agent": "receptionist",
        "initialized": receptionist_agent is not None
    }

@app.get("/")
async def index():
    """返回简单页面"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>接待员智能体服务</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; color: #333; }
            h1 { color: #667eea; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 接待员智能体服务</h1>
            <p>端口: <strong>8001</strong></p>
            <p>职责：负责用户接待、问题初步分类和引导</p>
            <p><a href="/docs">API 文档</a> | <a href="/api/health">健康检查</a></p>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
