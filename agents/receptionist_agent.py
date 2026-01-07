"""接待员智能体 - 负责用户接待、问题初步分类和引导"""

from typing import Dict, Any, List
from langchain_core.language_models import BaseChatModel

import sys
from pathlib import Path

# 确保可以导入项目模块
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from .base_agent import BaseAgent
except ImportError:
    from agents.base_agent import BaseAgent

# 确保可以导入 utils
import sys
from pathlib import Path
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger

logger = get_logger(__name__)


class ReceptionistAgent(BaseAgent):
    """接待员智能体"""
    
    def __init__(self, llm: BaseChatModel):
        system_prompt = """你是一个专业的客服接待员，负责：
1. 友好地欢迎用户
2. 初步了解用户问题
3. 对问题进行初步分类（订单问题、产品咨询、技术支持、投诉建议等）
4. 引导用户提供必要信息
5. 判断问题是否需要转交给问题分析师

请保持友好、专业的态度，快速理解用户意图。"""
        
        super().__init__(
            llm=llm,
            name="接待员",
            role="负责用户接待、问题初步分类和引导",
            system_prompt=system_prompt
        )
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户输入，进行初步分类
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        user_input = state.get("user_input", "")
        conversation_history = state.get("conversation_history", [])
        
        # 构建消息
        messages = self._build_messages(
            user_input=user_input,
            conversation_history=conversation_history,
            context=state.get("context", {})
        )
        
        # 添加分类提示
        classification_prompt = """请分析用户问题，并返回以下信息（JSON格式）：
{
    "greeting": "欢迎语",
    "problem_category": "问题类别（订单问题/产品咨询/技术支持/投诉建议/其他）",
    "urgency": "紧急程度（高/中/低）",
    "needs_analysis": true/false,  // 是否需要转交给问题分析师
    "response": "你的回复内容",
    "missing_info": ["需要补充的信息列表"]
}"""
        
        from langchain_core.messages import HumanMessage
        messages.append(HumanMessage(content=classification_prompt))
        
        # 调用 LLM
        try:
            response = await self._invoke_llm(messages)
            
            # 解析响应（简化处理，实际应该解析JSON）
            classification_result = self._parse_classification(response)
            if not isinstance(classification_result, dict):
                classification_result = {}
            
            # 更新状态
            state["receptionist_result"] = {
                "agent": self.name,
                "response": classification_result.get("response", response),
                "problem_category": classification_result.get("problem_category", "其他"),
                "urgency": classification_result.get("urgency", "中"),
                "needs_analysis": classification_result.get("needs_analysis", True),
                "missing_info": classification_result.get("missing_info", [])
            }
            
            state["current_agent"] = self.name
            state["next_agent"] = "analyst" if classification_result.get("needs_analysis", True) else None
            
            logger.info(f"{self.name} 处理完成: {classification_result.get('problem_category', '未知')}")
            
        except Exception as e:
            logger.error(f"{self.name} 处理失败: {e}")
            state["error"] = str(e)
            state["next_agent"] = None
        
        return state
    
    def _parse_classification(self, response: str) -> Dict[str, Any]:
        """解析分类结果（简化实现）"""
        # 实际应该解析JSON，这里简化处理
        import re
        
        result = {
            "response": response,
            "problem_category": "其他",
            "urgency": "中",
            "needs_analysis": True,
            "missing_info": []
        }
        
        # 简单的关键词匹配
        if "订单" in response or "order" in response.lower():
            result["problem_category"] = "订单问题"
        elif "产品" in response or "product" in response.lower():
            result["problem_category"] = "产品咨询"
        elif "技术" in response or "technical" in response.lower():
            result["problem_category"] = "技术支持"
        elif "投诉" in response or "complaint" in response.lower():
            result["problem_category"] = "投诉建议"
            result["urgency"] = "高"
        
        return result
