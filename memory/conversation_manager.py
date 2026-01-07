"""对话管理器"""

from typing import List, Dict, Optional
from datetime import datetime

import sys
from pathlib import Path

# 确保可以导入项目模块
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入记忆存储
from memory.memory_store import MemoryStore
from utils.logger import get_logger

logger = get_logger(__name__)


class ConversationManager:
    """对话管理器"""
    
    def __init__(self, memory_store: MemoryStore):
        """
        初始化对话管理器
        
        Args:
            memory_store: 记忆存储
        """
        self.memory_store = memory_store
    
    async def get_context(
        self,
        user_id: str,
        session_id: str,
        max_messages: int = 10
    ) -> Dict[str, any]:
        """
        获取对话上下文
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            max_messages: 最大消息数
            
        Returns:
            上下文信息
        """
        history = await self.memory_store.get_conversation_history(
            user_id=user_id,
            session_id=session_id,
            limit=max_messages
        )
        
        return {
            "history": history,
            "message_count": len(history),
            "session_id": session_id,
            "user_id": user_id
        }
    
    async def summarize_conversation(
        self,
        user_id: str,
        session_id: str
    ) -> str:
        """
        总结对话内容
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            对话总结
        """
        history = await self.memory_store.get_conversation_history(
            user_id=user_id,
            session_id=session_id
        )
        
        if not history:
            return "暂无对话记录"
        
        summary_parts = []
        for msg in history:
            role = "用户" if msg["role"] == "user" else "助手"
            summary_parts.append(f"{role}: {msg['content'][:100]}")
        
        return "\n".join(summary_parts)
