"""问题分析师智能体 - 深入分析用户问题，提取关键信息"""

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


class AnalystAgent(BaseAgent):
    """问题分析师智能体"""
    
    def __init__(self, llm: BaseChatModel):
        system_prompt = """你是一个专业的问题分析师，负责：
1. 深入分析用户问题的根本原因
2. 提取关键信息和关键参数
3. 识别问题涉及的业务流程
4. 评估问题的复杂度和影响范围
5. 准备分析报告供解决方案专家使用

请进行深入、细致的分析，确保不遗漏关键信息。"""
        
        super().__init__(
            llm=llm,
            name="问题分析师",
            role="深入分析用户问题，提取关键信息",
            system_prompt=system_prompt
        )
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        深入分析用户问题
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        user_input = state.get("user_input", "")
        conversation_history = state.get("conversation_history", [])
        receptionist_result = state.get("receptionist_result") or {}
        if not isinstance(receptionist_result, dict):
            receptionist_result = {}
        
        # 构建分析上下文
        analysis_result = state.get("analysis_result") or {}
        if not isinstance(analysis_result, dict):
            analysis_result = {}
        
        analysis_context = {
            "problem_category": receptionist_result.get("problem_category", ""),
            "urgency": receptionist_result.get("urgency", ""),
            "previous_analysis": analysis_result
        }
        
        # 构建消息
        messages = self._build_messages(
            user_input=user_input,
            conversation_history=conversation_history,
            context=analysis_context
        )
        
        # 添加分析提示
        analysis_prompt = """请深入分析用户问题，并返回以下信息（JSON格式）：
{
    "problem_summary": "问题摘要",
    "root_cause": "根本原因分析",
    "key_parameters": {
        "订单号": "如有",
        "产品名称": "如有",
        "问题时间": "如有",
        "其他关键信息": "..."
    },
    "affected_areas": ["受影响的功能/模块列表"],
    "complexity": "复杂度（简单/中等/复杂）",
    "solution_approach": "建议的解决方向",
    "analysis_report": "详细分析报告"
}"""
        
        from langchain_core.messages import HumanMessage
        messages.append(HumanMessage(content=analysis_prompt))
        
        # 调用 LLM
        try:
            response = await self._invoke_llm(messages)
            
            # 解析分析结果
            analysis_result = self._parse_analysis(response)
            if not isinstance(analysis_result, dict):
                analysis_result = {}
            
            # 更新状态
            state["analysis_result"] = {
                "agent": self.name,
                "problem_summary": analysis_result.get("problem_summary", ""),
                "root_cause": analysis_result.get("root_cause", ""),
                "key_parameters": analysis_result.get("key_parameters", {}),
                "affected_areas": analysis_result.get("affected_areas", []),
                "complexity": analysis_result.get("complexity", "中等"),
                "solution_approach": analysis_result.get("solution_approach", ""),
                "analysis_report": analysis_result.get("analysis_report", response)
            }
            
            state["current_agent"] = self.name
            state["next_agent"] = "solution_expert"
            
            logger.info(f"{self.name} 分析完成: {analysis_result.get('complexity')}")
            
        except Exception as e:
            logger.error(f"{self.name} 分析失败: {e}")
            state["error"] = str(e)
            state["next_agent"] = None
        
        return state
    
    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """解析分析结果（简化实现）"""
        # 实际应该解析JSON，这里简化处理
        result = {
            "problem_summary": response[:200] if len(response) > 200 else response,
            "root_cause": "待分析",
            "key_parameters": {},
            "affected_areas": [],
            "complexity": "中等",
            "solution_approach": "待确定",
            "analysis_report": response
        }
        
        # 简单的参数提取
        import re
        
        # 提取订单号
        order_match = re.search(r'订单[号码]*[：:]*(\w+)', response)
        if order_match:
            result["key_parameters"]["订单号"] = order_match.group(1)
        
        return result
