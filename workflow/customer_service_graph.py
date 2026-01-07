"""客服工作流图 - 基于 LangGraph 的多智能体协作流程"""

from typing import Dict, Any, Literal
from datetime import datetime
import uuid

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.language_models import BaseChatModel

from typing import Optional
import sys
from pathlib import Path

# 确保可以导入项目模块
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入状态
from .state import CustomerServiceState

# 导入智能体（使用绝对导入，避免相对导入问题）
from agents.receptionist_agent import ReceptionistAgent
from agents.analyst_agent import AnalystAgent
from agents.solution_expert_agent import SolutionExpertAgent
from tools.mcp_tools import MCPToolManager
from memory.memory_store import MemoryStore
from utils.logger import get_logger

logger = get_logger(__name__)


class CustomerServiceGraph:
    """客服工作流图"""
    
    def __init__(
        self,
        llm: BaseChatModel,
        memory_store: MemoryStore = None,
        enable_tools: bool = True
    ):
        """
        初始化工作流图
        
        Args:
            llm: 语言模型
            memory_store: 记忆存储
            enable_tools: 是否启用工具
        """
        self.llm = llm
        self.memory_store = memory_store or MemoryStore()
        self.enable_tools = enable_tools
        
        # 初始化智能体
        self.receptionist = ReceptionistAgent(llm)
        self.analyst = AnalystAgent(llm)
        self.solution_expert = SolutionExpertAgent(llm)
        
        # 初始化工具管理器
        self.tool_manager = MCPToolManager() if enable_tools else None
        
        # 构建工作流图
        self.graph = self._build_graph()
        
        # 编译图（带记忆检查点）
        self.checkpointer = MemorySaver()
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
    
    def _build_graph(self) -> StateGraph:
        """构建工作流图"""
        workflow = StateGraph(CustomerServiceState)
        
        # 添加节点
        workflow.add_node("receptionist", self._receptionist_node)
        workflow.add_node("analyst", self._analyst_node)
        workflow.add_node("solution_expert", self._solution_expert_node)
        workflow.add_node("call_tools", self._call_tools_node)
        workflow.add_node("human_intervention", self._human_intervention_node)
        
        # 设置入口点
        workflow.set_entry_point("receptionist")
        
        # 添加条件路由
        workflow.add_conditional_edges(
            "receptionist",
            self._route_after_receptionist,
            {
                "analyst": "analyst",
                "solution_expert": "solution_expert",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "analyst",
            self._route_after_analyst,
            {
                "call_tools": "call_tools",
                "solution_expert": "solution_expert"
            }
        )
        
        workflow.add_conditional_edges(
            "call_tools",
            self._route_after_tools,
            {
                "solution_expert": "solution_expert",
                "human_intervention": "human_intervention"
            }
        )
        
        workflow.add_conditional_edges(
            "solution_expert",
            self._route_after_solution,
            {
                "human_intervention": "human_intervention",
                "end": END
            }
        )
        
        workflow.add_edge("human_intervention", END)
        
        return workflow
    
    async def _receptionist_node(self, state: CustomerServiceState) -> CustomerServiceState:
        """接待员节点"""
        logger.info("进入接待员节点")
        state = await self.receptionist.process(state)
        return state
    
    async def _analyst_node(self, state: CustomerServiceState) -> CustomerServiceState:
        """问题分析师节点"""
        logger.info("进入问题分析师节点")
        state = await self.analyst.process(state)
        return state
    
    async def _solution_expert_node(self, state: CustomerServiceState) -> CustomerServiceState:
        """解决方案专家节点"""
        logger.info("进入解决方案专家节点")
        state = await self.solution_expert.process(state)
        return state
    
    async def _call_tools_node(self, state: CustomerServiceState) -> CustomerServiceState:
        """工具调用节点"""
        logger.info("进入工具调用节点")
        
        if not self.tool_manager:
            state["tool_results"] = {}
            return state
        
        analysis_result = state.get("analysis_result", {})
        if not isinstance(analysis_result, dict):
            analysis_result = {}
        key_parameters = analysis_result.get("key_parameters", {})
        if not isinstance(key_parameters, dict):
            key_parameters = {}
        
        receptionist_result = state.get("receptionist_result", {})
        if not isinstance(receptionist_result, dict):
            receptionist_result = {}
        problem_category = receptionist_result.get("problem_category", "")
        
        tool_results = {}
        
        # 根据问题类型调用相应工具
        if problem_category == "订单问题" and "订单号" in key_parameters:
            order_id = key_parameters["订单号"]
            try:
                order_info = await self.tool_manager.query_order(order_id)
                tool_results["order_info"] = order_info
            except Exception as e:
                logger.error(f"订单查询失败: {e}")
                tool_results["order_info"] = {"error": str(e)}
        
        # 查询知识库
        try:
            knowledge_result = await self.tool_manager.query_knowledge_base(
                query=state.get("user_input", ""),
                category=problem_category
            )
            tool_results["knowledge_base"] = knowledge_result
        except Exception as e:
            logger.error(f"知识库查询失败: {e}")
            tool_results["knowledge_base"] = {"error": str(e)}
        
        state["tool_results"] = tool_results
        return state
    
    async def _human_intervention_node(self, state: CustomerServiceState) -> CustomerServiceState:
        """人工介入节点"""
        logger.info("进入人工介入节点")
        state["needs_human_intervention"] = True
        return state
    
    def _route_after_receptionist(self, state: CustomerServiceState) -> Literal["analyst", "solution_expert", "end"]:
        """接待员后的路由决策"""
        next_agent = state.get("next_agent")
        receptionist_result = state.get("receptionist_result", {})
        if not isinstance(receptionist_result, dict):
            receptionist_result = {}
        needs_analysis = receptionist_result.get("needs_analysis", True)
        
        if not needs_analysis:
            return "end"
        
        if next_agent == "analyst":
            return "analyst"
        elif next_agent == "solution_expert":
            return "solution_expert"
        else:
            return "analyst"  # 默认路由到分析师
    
    def _route_after_analyst(self, state: CustomerServiceState) -> Literal["call_tools", "solution_expert"]:
        """分析师后的路由决策"""
        # 根据问题复杂度决定是否需要调用工具
        analysis_result = state.get("analysis_result", {})
        if not isinstance(analysis_result, dict):
            analysis_result = {}
        complexity = analysis_result.get("complexity", "中等")
        has_key_params = bool(analysis_result.get("key_parameters", {}))
        
        if self.enable_tools and (complexity in ["复杂", "中等"] or has_key_params):
            return "call_tools"
        else:
            return "solution_expert"
    
    def _route_after_tools(self, state: CustomerServiceState) -> Literal["solution_expert", "human_intervention"]:
        """工具调用后的路由决策"""
        tool_results = state.get("tool_results", {})
        if not isinstance(tool_results, dict):
            tool_results = {}
        
        # 如果工具调用失败且是关键信息，需要人工介入
        order_info = tool_results.get("order_info", {})
        if isinstance(order_info, dict) and order_info.get("error") and "订单" in state.get("user_input", ""):
            return "human_intervention"
        
        return "solution_expert"
    
    def _route_after_solution(self, state: CustomerServiceState) -> Literal["human_intervention", "end"]:
        """解决方案专家后的路由决策"""
        # 如果解决方案复杂度高，可能需要人工确认
        analysis_result = state.get("analysis_result", {})
        if not isinstance(analysis_result, dict):
            analysis_result = {}
        complexity = analysis_result.get("complexity", "中等")
        
        solution_result = state.get("solution_result", {})
        if not isinstance(solution_result, dict):
            solution_result = {}
        
        if complexity == "复杂" and solution_result.get("needs_confirmation", False):
            return "human_intervention"
        
        return "end"
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理用户消息
        
        Args:
            user_id: 用户ID
            message: 用户消息
            session_id: 会话ID（可选）
            
        Returns:
            处理结果
        """
        # 获取或创建会话ID
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # 加载对话历史
        conversation_history = await self.memory_store.get_conversation_history(
            user_id=user_id,
            session_id=session_id
        )
        
        # 构建初始状态
        initial_state: CustomerServiceState = {
            "user_id": user_id,
            "user_input": message,
            "conversation_history": conversation_history,
            "receptionist_result": None,
            "analysis_result": None,
            "solution_result": None,
            "tool_results": {},
            "current_agent": None,
            "next_agent": None,
            "is_complete": False,
            "needs_human_intervention": False,
            "context": {},
            "error": None,
            "retry_count": 0,
            "session_id": session_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # 执行工作流
        try:
            config = {"configurable": {"thread_id": session_id}}
            final_state = await self.compiled_graph.ainvoke(initial_state, config)
            
            # 检查 final_state 是否为 None
            if final_state is None:
                logger.error("工作流返回的状态为 None")
                return {
                    "session_id": session_id,
                    "response": "抱歉，系统处理出现错误，请稍后重试。",
                    "error": "工作流返回状态为空",
                    "needs_human_intervention": True
                }
            
            # 确保 final_state 是字典类型
            if not isinstance(final_state, dict):
                logger.error(f"工作流返回的状态类型错误: {type(final_state)}")
                return {
                    "session_id": session_id,
                    "response": "抱歉，系统处理出现错误，请稍后重试。",
                    "error": f"状态类型错误: {type(final_state)}",
                    "needs_human_intervention": True
                }
            
            # 保存对话历史
            await self.memory_store.save_message(
                user_id=user_id,
                session_id=session_id,
                role="user",
                content=message
            )
            
            # 获取最终回复
            final_response = self._extract_final_response(final_state)
            
            await self.memory_store.save_message(
                user_id=user_id,
                session_id=session_id,
                role="assistant",
                content=final_response
            )
            
            return {
                "session_id": session_id,
                "response": final_response,
                "state": final_state,
                "needs_human_intervention": final_state.get("needs_human_intervention", False) if isinstance(final_state, dict) else False
            }
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}", exc_info=True)
            return {
                "session_id": session_id,
                "response": "抱歉，处理过程中出现了错误，请稍后重试。",
                "error": str(e),
                "needs_human_intervention": True
            }
    
    def _extract_final_response(self, state: CustomerServiceState) -> str:
        """提取最终回复"""
        # 确保 state 是字典类型
        if not isinstance(state, dict):
            logger.error(f"状态类型错误: {type(state)}")
            return "抱歉，系统处理出现错误，请稍后重试。"
        
        # 优先使用解决方案专家的回复
        solution_result = state.get("solution_result")
        if solution_result and isinstance(solution_result, dict):
            response = solution_result.get("final_response", "")
            if response and isinstance(response, str) and response.strip():
                logger.info("使用解决方案专家的回复")
                return response
        
        # 其次使用分析师的回复
        analysis_result = state.get("analysis_result")
        if analysis_result and isinstance(analysis_result, dict):
            response = analysis_result.get("analysis_report", "")
            if response and isinstance(response, str) and response.strip():
                logger.info("使用分析师的回复")
                return response
        
        # 最后使用接待员的回复
        receptionist_result = state.get("receptionist_result")
        if receptionist_result and isinstance(receptionist_result, dict):
            response = receptionist_result.get("response", "")
            if response and isinstance(response, str) and response.strip():
                logger.info("使用接待员的回复")
                return response
        
        # 如果所有回复都为空，记录调试信息并返回默认消息
        logger.warning(f"无法从状态中提取有效回复。状态键: {list(state.keys())}")
        logger.warning(f"solution_result: {state.get('solution_result')}")
        logger.warning(f"analysis_result: {state.get('analysis_result')}")
        logger.warning(f"receptionist_result: {state.get('receptionist_result')}")
        return "抱歉，我无法理解您的问题，请重新描述一下。"
    
    def __repr__(self) -> str:
        return f"CustomerServiceGraph(agents=3, tools={self.enable_tools})"
