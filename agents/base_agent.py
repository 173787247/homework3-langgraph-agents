"""智能体基类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

import sys
from pathlib import Path

# 确保可以导入项目模块
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """智能体基类"""
    
    def __init__(
        self,
        llm: BaseChatModel,
        name: str,
        role: str,
        system_prompt: Optional[str] = None
    ):
        """
        初始化智能体
        
        Args:
            llm: 语言模型
            name: 智能体名称
            role: 智能体角色描述
            system_prompt: 系统提示词
        """
        self.llm = llm
        self.name = name
        self.role = role
        self.system_prompt = system_prompt or self._default_system_prompt()
        
    def _default_system_prompt(self) -> str:
        """默认系统提示词"""
        return f"""你是一个专业的{self.name}，你的角色是：{self.role}

请遵循以下原则：
1. 保持专业和友好的态度
2. 准确理解用户意图
3. 提供清晰、有用的回复
4. 如果信息不足，主动询问用户
"""
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理状态并返回更新后的状态
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        pass
    
    async def _invoke_llm(
        self,
        messages: List[BaseMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        调用语言模型
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            LLM 回复
        """
        try:
            response = await self.llm.ainvoke(
                messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.content
        except Exception as e:
            logger.error(f"{self.name} LLM调用失败: {e}")
            raise
    
    def _build_messages(
        self,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[BaseMessage]:
        """
        构建消息列表
        
        Args:
            user_input: 用户输入
            conversation_history: 对话历史
            context: 上下文信息
            
        Returns:
            消息列表
        """
        messages = []
        
        # 添加系统提示词
        if self.system_prompt:
            messages.append(HumanMessage(content=self.system_prompt))
        
        # 添加上下文信息
        if context:
            context_str = self._format_context(context)
            if context_str:
                messages.append(HumanMessage(content=f"上下文信息：\n{context_str}"))
        
        # 添加对话历史
        if conversation_history:
            for msg in conversation_history[-5:]:  # 只保留最近5轮对话
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg.get("content", "")))
        
        # 添加当前用户输入
        messages.append(HumanMessage(content=user_input))
        
        return messages
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """格式化上下文信息"""
        if not context:
            return ""
        
        context_parts = []
        for key, value in context.items():
            if value:
                context_parts.append(f"{key}: {value}")
        
        return "\n".join(context_parts)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, role={self.role})"
