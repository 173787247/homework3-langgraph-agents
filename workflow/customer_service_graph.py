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
                "call_tools": "call_tools",  # 简单查询直接调用工具
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
        user_input = state.get("user_input", "").lower()
        
        # 根据问题类型和关键词调用相应工具
        
        # 1. 天气查询（免费API）
        weather_keywords = ["天气", "温度", "气温", "下雨", "晴天", "weather", "temperature", "climate"]
        if any(keyword in user_input for keyword in weather_keywords):
            city = key_parameters.get("城市") or key_parameters.get("city") or key_parameters.get("地点")
            country = key_parameters.get("国家") or key_parameters.get("country")
            
            # 如果没有从参数中提取到，尝试从用户输入中提取城市名
            if not city:
                # 简单的城市名提取（实际应该用更智能的方式）
                common_cities = ["北京", "上海", "广州", "深圳", "杭州", "南京", "武汉", "成都", "重庆", "西安",
                               "beijing", "shanghai", "guangzhou", "shenzhen"]
                for city_name in common_cities:
                    if city_name in user_input:
                        city = city_name
                        break
                # 如果还是没找到，尝试提取"天气"关键词前后的内容
                if not city and "天气" in user_input:
                    idx = user_input.find("天气")
                    if idx > 0:
                        city = user_input[:idx].strip()
            
            if city:
                try:
                    weather_result = await self.tool_manager.query_weather(
                        city=city,
                        country=country
                    )
                    tool_results["weather"] = weather_result
                    logger.info(f"已查询天气: {city}")
                except Exception as e:
                    logger.error(f"天气查询失败: {e}")
                    tool_results["weather"] = {"error": str(e)}
        
        # 2. 地址查询（高德地图）
        address_keywords = ["地址", "位置", "在哪里", "怎么去", "导航", "地图", "address", "location", "map"]
        if any(keyword in user_input for keyword in address_keywords):
            address = key_parameters.get("地址") or key_parameters.get("位置") or key_parameters.get("address")
            city = key_parameters.get("城市") or key_parameters.get("city")
            
            # 如果没有从参数中提取到，尝试从用户输入中提取
            if not address:
                # 简单的地址提取
                for keyword in address_keywords:
                    if keyword in user_input:
                        # 提取关键词后的内容作为地址
                        idx = user_input.find(keyword)
                        if idx != -1:
                            address = user_input[idx + len(keyword):].strip()
                            break
            
            if address:
                try:
                    address_result = await self.tool_manager.query_address(
                        address=address,
                        city=city
                    )
                    tool_results["address"] = address_result
                    logger.info(f"已查询地址: {address}")
                except Exception as e:
                    logger.error(f"地址查询失败: {e}")
                    tool_results["address"] = {"error": str(e)}
        
        # 3. 地点搜索（高德地图 POI）
        poi_keywords = ["附近", "找", "搜索", "推荐", "哪里有", "poi", "search"]
        if any(keyword in user_input for keyword in poi_keywords):
            keywords = key_parameters.get("关键词") or key_parameters.get("keywords")
            city = key_parameters.get("城市") or key_parameters.get("city")
            
            if keywords:
                try:
                    poi_result = await self.tool_manager.search_location(
                        keywords=keywords,
                        city=city
                    )
                    tool_results["poi_search"] = poi_result
                    logger.info(f"已搜索地点: {keywords}")
                except Exception as e:
                    logger.error(f"地点搜索失败: {e}")
                    tool_results["poi_search"] = {"error": str(e)}
        
        # 3.5. 火车票查询（12306 MCP 服务）
        train_keywords = ["火车票", "车票", "高铁", "动车", "火车", "train", "ticket", "12306"]
        if any(keyword in user_input for keyword in train_keywords):
            from_station = key_parameters.get("出发站") or key_parameters.get("from_station") or key_parameters.get("起点")
            to_station = key_parameters.get("到达站") or key_parameters.get("to_station") or key_parameters.get("终点")
            date = key_parameters.get("日期") or key_parameters.get("date")
            
            # 尝试从用户输入中提取出发站和到达站
            if not from_station or not to_station:
                # 查找"到"或"->"或"-"
                separators = ["到", "->", "-", "至"]
                for sep in separators:
                    if sep in user_input:
                        idx = user_input.find(sep)
                        if idx > 0:
                            # 提取"到"之前的部分作为出发站
                            from_part = user_input[:idx].strip()
                            # 提取"到"之后的部分作为到达站
                            to_part = user_input[idx + len(sep):].strip()
                            
                            # 清理出发站：去除前面的"我想"、"查询"等
                            from_part = from_part.replace("我想", "").replace("查询", "").replace("查", "").strip()
                            # 清理到达站：去除后面的"火车票"、"车票"、"的"等
                            to_part = to_part.replace("火车票", "").replace("车票", "").replace("的", "").strip()
                            
                            # 提取城市名（常见城市列表）
                            common_cities = ["北京", "上海", "广州", "深圳", "杭州", "南京", "武汉", "成都", "重庆", "西安",
                                           "天津", "苏州", "长沙", "郑州", "青岛", "大连", "厦门", "福州", "济南", "合肥",
                                           "beijing", "shanghai", "guangzhou", "shenzhen"]
                            
                            # 从from_part中提取城市名
                            if not from_station:
                                for city in common_cities:
                                    if city in from_part:
                                        from_station = city
                                        break
                                # 如果没找到，使用清理后的from_part（去除常见前缀）
                                if not from_station and from_part:
                                    from_station = from_part
                            
                            # 从to_part中提取城市名
                            if not to_station:
                                for city in common_cities:
                                    if city in to_part:
                                        to_station = city
                                        break
                                # 如果没找到，使用清理后的to_part（去除常见后缀）
                                if not to_station and to_part:
                                    to_station = to_part
                            break
            
            if from_station and to_station:
                try:
                    train_result = await self.tool_manager.query_train_tickets(
                        from_station=from_station,
                        to_station=to_station,
                        date=date
                    )
                    tool_results["train_tickets"] = train_result
                    logger.info(f"已查询火车票: {from_station} -> {to_station}")
                except Exception as e:
                    logger.error(f"火车票查询失败: {e}")
                    tool_results["train_tickets"] = {"error": str(e)}
        
        # 4. 时间查询（MCP 服务）- 只在没有天气查询时才执行
        # 避免"现在天气"这样的查询被误识别为时间查询
        if "weather" not in tool_results and "天气" not in user_input:
            time_keywords = ["时间", "几点", "现在几点", "今天几号", "日期", "几号", "星期", "time", "date"]
            # 更精确的时间查询匹配：必须包含明确的时间查询关键词，且不包含天气相关词
            is_time_query = any(keyword in user_input for keyword in ["时间", "几点", "现在几点", "今天几号", "几号", "星期", "time", "date"])
            # 如果只是"现在"或"今天"但没有明确的时间查询意图，且包含天气关键词，则不查询时间
            if "现在" in user_input or "今天" in user_input:
                if "天气" in user_input or "温度" in user_input or "气温" in user_input:
                    is_time_query = False
            
            if is_time_query:
                timezone = key_parameters.get("时区") or key_parameters.get("timezone")
                
                # 判断是查询时间还是日期
                if any(kw in user_input for kw in ["几号", "日期", "date", "星期"]):
                    try:
                        date_result = await self.tool_manager.get_date_info()
                        tool_results["date_info"] = date_result
                        logger.info("已查询日期信息")
                    except Exception as e:
                        logger.error(f"日期查询失败: {e}")
                        tool_results["date_info"] = {"error": str(e)}
                else:
                    try:
                        time_result = await self.tool_manager.query_time(timezone)
                        tool_results["time_info"] = time_result
                        logger.info("已查询时间信息")
                    except Exception as e:
                        logger.error(f"时间查询失败: {e}")
                        tool_results["time_info"] = {"error": str(e)}
        
        # 5. 知识库查询（Memory MCP）- 适合接待员和解决方案专家
        kb_keywords = ["常见问题", "FAQ", "帮助", "怎么", "如何", "是什么", "知识库", "文档", "说明", "help", "faq", "knowledge"]
        if any(keyword in user_input for keyword in kb_keywords):
            query = key_parameters.get("查询") or key_parameters.get("query") or user_input
            try:
                kb_result = await self.tool_manager.search_knowledge_base(query)
                tool_results["knowledge_base"] = kb_result
                logger.info(f"已搜索知识库: {query}")
            except Exception as e:
                logger.error(f"知识库搜索失败: {e}")
                tool_results["knowledge_base"] = {"error": str(e)}
        
        # 6. 文件系统操作（Filesystem MCP）- 适合问题分析师查看日志
        file_keywords = ["日志", "文件", "查看", "读取", "log", "file", "查看日志", "读取文件"]
        if any(keyword in user_input for keyword in file_keywords):
            file_path = key_parameters.get("文件路径") or key_parameters.get("file_path")
            
            # 尝试从用户输入中提取文件路径
            if not file_path:
                for keyword in ["日志", "log"]:
                    if keyword in user_input:
                        # 默认日志路径
                        file_path = "/app/logs/app.log"
                        break
            
            if file_path:
                try:
                    file_result = await self.tool_manager.read_file(file_path)
                    tool_results["file_content"] = file_result
                    logger.info(f"已读取文件: {file_path}")
                except Exception as e:
                    logger.error(f"文件读取失败: {e}")
                    tool_results["file_content"] = {"error": str(e)}
        
        state["tool_results"] = tool_results
        return state
    
    async def _human_intervention_node(self, state: CustomerServiceState) -> CustomerServiceState:
        """人工介入节点"""
        logger.info("进入人工介入节点")
        state["needs_human_intervention"] = True
        return state
    
    def _route_after_receptionist(self, state: CustomerServiceState) -> Literal["analyst", "solution_expert", "call_tools", "end"]:
        """接待员后的路由决策"""
        next_agent = state.get("next_agent")
        receptionist_result = state.get("receptionist_result", {})
        if not isinstance(receptionist_result, dict):
            receptionist_result = {}
        needs_analysis = receptionist_result.get("needs_analysis", True)
        user_input = state.get("user_input", "").lower()
        
        # 对于简单查询（时间、日期），直接调用工具，跳过分析师
        simple_queries = ["时间", "几点", "现在", "今天", "日期", "几号", "星期", "time", "date"]
        if any(keyword in user_input for keyword in simple_queries):
            logger.info("检测到简单查询，直接调用工具")
            return "call_tools"
        
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
