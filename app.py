"""FastAPI 应用 - Web API 模式"""

import os
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import os

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

# 创建 FastAPI 应用
app = FastAPI(
    title="多角色协作智能客服系统",
    description="基于 LangGraph 的多智能体协作客服系统",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
graph: Optional[CustomerServiceGraph] = None


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
        
        # 如果模型名称是 deepseek-chat，自动改为 gpt-3.5-turbo
        model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        if model == "deepseek-chat":
            model = "gpt-3.5-turbo"
            logger.warning("检测到 LLM_MODEL=deepseek-chat 但使用 OpenAI，自动改为 gpt-3.5-turbo")
        
        return ChatOpenAI(
            model=model,
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            api_key=api_key
        )


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    global graph
    try:
        logger.info("正在初始化系统...")
        
        # 先检查环境变量
        provider_env = os.getenv("LLM_PROVIDER", "deepseek").lower()
        logger.info(f"环境变量 LLM_PROVIDER: {provider_env}")
        
        llm = create_llm()
        
        # 根据实际创建的 LLM 类型判断
        if ChatDeepSeek and isinstance(llm, ChatDeepSeek):
            provider = "deepseek"
            model = os.getenv("LLM_MODEL", "deepseek-chat")
        else:
            provider = "openai"
            model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        
        logger.info(f"实际使用的 LLM 提供商: {provider.upper()}")
        logger.info(f"实际使用的 LLM 模型: {model}")
        
        memory_store = MemoryStore()
        graph = CustomerServiceGraph(llm=llm, memory_store=memory_store)
        logger.info("系统初始化完成！")
    except Exception as e:
        logger.error(f"系统初始化失败: {e}")
        raise


# 请求模型
class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    needs_human_intervention: bool
    error: Optional[str] = None


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    处理聊天请求
    
    Args:
        request: 聊天请求
        
    Returns:
        聊天响应
    """
    if graph is None:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    try:
        result = await graph.process_message(
            user_id=request.user_id,
            message=request.message,
            session_id=request.session_id
        )
        
        # 检查 result 是否为 None
        if result is None:
            logger.error("process_message 返回了 None")
            return ChatResponse(
                session_id=request.session_id or "unknown",
                response="抱歉，系统处理出现错误，请稍后重试。",
                needs_human_intervention=True,
                error="处理结果为空"
            )
        
        return ChatResponse(
            session_id=result.get("session_id") if result else (request.session_id or "unknown"),
            response=result.get("response", "抱歉，我无法理解您的问题。") if result else "抱歉，系统处理出现错误。",
            needs_human_intervention=result.get("needs_human_intervention", False) if result else True,
            error=result.get("error") if result else "处理结果为空"
        )
    except Exception as e:
        logger.error(f"处理聊天请求失败: {e}", exc_info=True)
        return ChatResponse(
            session_id=request.session_id or "unknown",
            response=f"抱歉，处理过程中出现了错误：{str(e)}",
            needs_human_intervention=True,
            error=str(e)
        )


@app.get("/api/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "graph_initialized": graph is not None
    }


# 静态文件服务
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def index():
    """返回前端页面"""
    static_file = os.path.join(static_dir, "index.html")
    if os.path.exists(static_file):
        return FileResponse(static_file, media_type="text/html")
    # 如果文件不存在，返回简单的 HTML
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>智能客服系统</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <h1>多角色协作智能客服系统</h1>
        <p>Web 界面文件未找到，请使用 API 端点：</p>
        <ul>
            <li><a href="/docs">API 文档</a></li>
            <li><a href="/api/health">健康检查</a></li>
        </ul>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
