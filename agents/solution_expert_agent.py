"""解决方案专家智能体 - 基于分析结果提供专业解决方案"""

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


class SolutionExpertAgent(BaseAgent):
    """解决方案专家智能体"""
    
    def __init__(self, llm: BaseChatModel):
        system_prompt = """你是一个专业的解决方案专家，负责：
1. 基于问题分析结果制定解决方案
2. 提供清晰、可执行的解决步骤
3. 考虑多种解决方案并推荐最优方案
4. 提供预防措施和后续建议
5. 确保解决方案的可行性和有效性

请提供专业、详细、可操作的解决方案。"""
        
        super().__init__(
            llm=llm,
            name="解决方案专家",
            role="基于分析结果提供专业解决方案",
            system_prompt=system_prompt
        )
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成解决方案
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        user_input = state.get("user_input", "")
        conversation_history = state.get("conversation_history", [])
        analysis_result = state.get("analysis_result") or {}
        if not isinstance(analysis_result, dict):
            analysis_result = {}
        tool_results = state.get("tool_results") or {}
        if not isinstance(tool_results, dict):
            tool_results = {}
        
        # 构建解决方案上下文
        solution_context = {
            "problem_summary": analysis_result.get("problem_summary", ""),
            "root_cause": analysis_result.get("root_cause", ""),
            "key_parameters": analysis_result.get("key_parameters", {}),
            "complexity": analysis_result.get("complexity", ""),
            "solution_approach": analysis_result.get("solution_approach", ""),
            "tool_results": tool_results
        }
        
        # 构建消息
        messages = self._build_messages(
            user_input=user_input,
            conversation_history=conversation_history,
            context=solution_context
        )
        
        # 添加解决方案提示
        solution_prompt = """请基于分析结果提供解决方案，并返回以下信息（JSON格式）：
{
    "solution_summary": "解决方案摘要",
    "solution_steps": [
        {
            "step": 1,
            "description": "步骤描述",
            "action": "具体操作"
        }
    ],
    "alternative_solutions": ["备选方案列表"],
    "prevention_measures": ["预防措施"],
    "follow_up": "后续建议",
    "final_response": "给用户的最终回复"
}"""
        
        from langchain_core.messages import HumanMessage
        messages.append(HumanMessage(content=solution_prompt))
        
        # 调用 LLM
        try:
            response = await self._invoke_llm(messages)
            
            # 解析解决方案
            solution_result = self._parse_solution(response)
            if not isinstance(solution_result, dict):
                solution_result = {}
            
            # 更新状态
            state["solution_result"] = {
                "agent": self.name,
                "solution_summary": solution_result.get("solution_summary", ""),
                "solution_steps": solution_result.get("solution_steps", []),
                "alternative_solutions": solution_result.get("alternative_solutions", []),
                "prevention_measures": solution_result.get("prevention_measures", []),
                "follow_up": solution_result.get("follow_up", ""),
                "final_response": solution_result.get("final_response", response)
            }
            
            state["current_agent"] = self.name
            state["next_agent"] = None  # 流程结束
            state["is_complete"] = True
            
            logger.info(f"{self.name} 解决方案生成完成")
            
        except Exception as e:
            logger.error(f"{self.name} 解决方案生成失败: {e}")
            state["error"] = str(e)
            state["next_agent"] = None
        
        return state
    
    def _parse_solution(self, response: str) -> Dict[str, Any]:
        """解析解决方案（简化实现）"""
        # 实际应该解析JSON，这里简化处理
        result = {
            "solution_summary": response[:200] if len(response) > 200 else response,
            "solution_steps": [
                {"step": 1, "description": "请按照以下步骤操作", "action": response}
            ],
            "alternative_solutions": [],
            "prevention_measures": [],
            "follow_up": "如有问题，请随时联系我们",
            "final_response": response
        }
        
        return result
