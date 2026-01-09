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
        
        # 检查是否有工具结果，如果有且是简单查询（如时间、日期），直接使用工具结果
        logger.info(f"检查工具结果: {list(tool_results.keys())}")
        if tool_results:
            # 时间查询
            if "time_info" in tool_results:
                time_info = tool_results.get("time_info", {})
                logger.info(f"找到时间信息: {time_info}")
                # 工具结果可能是 {"success": True, "data": {...}} 或直接是 data
                if isinstance(time_info, dict):
                    time_data = time_info.get("data", time_info)
                    if isinstance(time_data, dict) and time_data.get("success"):
                        time_str = time_data.get("time", "")
                        timezone = time_data.get("timezone", "")
                        if time_str:
                            state["solution_result"] = {
                                "agent": self.name,
                                "final_response": f"当前时间是：{time_str}（{timezone}）"
                            }
                            state["current_agent"] = self.name
                            state["next_agent"] = None
                            state["is_complete"] = True
                            logger.info(f"{self.name} 直接返回时间查询结果: {time_str}")
                            return state
            
            # 日期查询
            if "date_info" in tool_results:
                date_info = tool_results.get("date_info", {})
                logger.info(f"找到日期信息: {date_info}, 类型: {type(date_info)}")
                # 工具结果格式：{"success": True, "data": {...}}
                if isinstance(date_info, dict):
                    # 先检查是否有 success 字段（说明是工具管理器返回的格式）
                    if date_info.get("success") and "data" in date_info:
                        date_data = date_info.get("data", {})
                    else:
                        # 否则直接使用 date_info
                        date_data = date_info
                    
                    logger.info(f"日期数据: {date_data}, 类型: {type(date_data)}")
                    if isinstance(date_data, dict) and date_data.get("success"):
                        date_str = date_data.get("date", "")
                        weekday = date_data.get("weekday", "")
                        if date_str:
                            state["solution_result"] = {
                                "agent": self.name,
                                "final_response": f"今天是：{date_str} {weekday}"
                            }
                            state["current_agent"] = self.name
                            state["next_agent"] = None
                            state["is_complete"] = True
                            logger.info(f"{self.name} 直接返回日期查询结果: {date_str} {weekday}")
                            return state
                    # 如果 date_data 没有 success 字段，但直接有 date 字段，也尝试使用
                    elif isinstance(date_data, dict) and date_data.get("date"):
                        date_str = date_data.get("date", "")
                        weekday = date_data.get("weekday", "")
                        if date_str:
                            state["solution_result"] = {
                                "agent": self.name,
                                "final_response": f"今天是：{date_str} {weekday if weekday else ''}"
                            }
                            state["current_agent"] = self.name
                            state["next_agent"] = None
                            state["is_complete"] = True
                            logger.info(f"{self.name} 直接返回日期查询结果（无success字段）: {date_str}")
                            return state
            
            # 天气查询
            if "weather" in tool_results:
                weather_info = tool_results.get("weather", {})
                logger.info(f"找到天气信息: {weather_info}")
                if isinstance(weather_info, dict):
                    # 工具结果格式：{"success": True, "data": {...}}
                    if weather_info.get("success") and "data" in weather_info:
                        weather_data = weather_info.get("data", {})
                    else:
                        weather_data = weather_info
                    
                    logger.info(f"天气数据: {weather_data}")
                    if isinstance(weather_data, dict) and weather_data.get("success"):
                        city = weather_data.get("city", "该城市")
                        temp = weather_data.get("temperature", 0)
                        desc = weather_data.get("description", weather_data.get("main", "未知"))
                        feels_like = weather_data.get("feels_like", temp)
                        humidity = weather_data.get("humidity", 0)
                        wind_speed = weather_data.get("wind_speed", 0)
                        source = weather_data.get("source", "")
                        
                        # 构建简洁的天气信息
                        weather_text = f"{city}当前天气：{desc}，气温 {temp}°C"
                        if feels_like != temp:
                            weather_text += f"（体感 {feels_like}°C）"
                        weather_text += f"，湿度 {humidity}%，风速 {wind_speed}米/秒"
                        if source:
                            weather_text += f"（数据来源：{source}）"
                        
                        state["solution_result"] = {
                            "agent": self.name,
                            "final_response": weather_text
                        }
                        state["current_agent"] = self.name
                        state["next_agent"] = None
                        state["is_complete"] = True
                        logger.info(f"{self.name} 直接返回天气查询结果: {city}")
                        return state
            
            # 火车票查询
            if "train_tickets" in tool_results:
                train_info = tool_results.get("train_tickets", {})
                logger.info(f"找到火车票信息: {train_info}")
                if isinstance(train_info, dict):
                    # 工具结果格式：{"success": True, "data": {...}}
                    if train_info.get("success") and "data" in train_info:
                        train_data = train_info.get("data", {})
                    else:
                        train_data = train_info
                    
                    logger.info(f"火车票数据: {train_data}")
                    if isinstance(train_data, dict) and train_data.get("success"):
                        from_station = train_data.get("from_station", "")
                        to_station = train_data.get("to_station", "")
                        date = train_data.get("date", "")
                        trains = train_data.get("trains", [])
                        note = train_data.get("note", "")
                        
                        # 构建简洁的火车票信息
                        if trains:
                            train_text = f"{from_station}到{to_station}"
                            if date:
                                train_text += f"（{date}）"
                            train_text += "的火车票信息：\n"
                            
                            # 显示前3个车次
                            for i, train in enumerate(trains[:3], 1):
                                train_no = train.get("train_no", "")
                                train_type = train.get("train_type", "")
                                dep_time = train.get("departure_time", "")
                                arr_time = train.get("arrival_time", "")
                                duration = train.get("duration", "")
                                second_class = train.get("second_class", {})
                                
                                train_text += f"{i}. {train_no}（{train_type}）"
                                train_text += f" {dep_time}出发，{arr_time}到达"
                                if duration:
                                    train_text += f"，历时{duration}"
                                if second_class.get("available"):
                                    train_text += f"，二等座{second_class.get('price', 'N/A')}"
                                train_text += "\n"
                            
                            if len(trains) > 3:
                                train_text += f"（共{len(trains)}个车次，仅显示前3个）"
                            
                            if note:
                                train_text += f"\n注：{note}"
                        else:
                            # 检查是否有错误信息
                            error_msg = train_data.get("error", "")
                            if error_msg:
                                train_text = f"查询{from_station}到{to_station}的火车票时出错：{error_msg}"
                            else:
                                train_text = f"未找到{from_station}到{to_station}的火车票信息"
                        
                        state["solution_result"] = {
                            "agent": self.name,
                            "final_response": train_text
                        }
                        state["current_agent"] = self.name
                        state["next_agent"] = None
                        state["is_complete"] = True
                        logger.info(f"{self.name} 直接返回火车票查询结果: {from_station} -> {to_station}")
                        return state
                    # 如果查询失败（success=False）
                    elif isinstance(train_data, dict) and not train_data.get("success"):
                        error_msg = train_data.get("error", "查询失败")
                        state["solution_result"] = {
                            "agent": self.name,
                            "final_response": f"火车票查询失败：{error_msg}"
                        }
                        state["current_agent"] = self.name
                        state["next_agent"] = None
                        state["is_complete"] = True
                        logger.info(f"{self.name} 返回火车票查询错误: {error_msg}")
                        return state
            
            # 文件内容查询
            if "file_content" in tool_results:
                file_info = tool_results.get("file_content", {})
                logger.info(f"找到文件内容: {file_info}")
                if isinstance(file_info, dict):
                    # 工具结果格式：{"success": True, "data": {...}}
                    if file_info.get("success") and "data" in file_info:
                        file_data = file_info.get("data", {})
                    else:
                        file_data = file_info
                    
                    logger.info(f"文件数据: {file_data}")
                    if isinstance(file_data, dict) and file_data.get("success"):
                        content = file_data.get("content", "")
                        file_path = file_data.get("path", "")
                        if content:
                            # 显示文件内容（限制长度）
                            if len(content) > 500:
                                content_preview = content[:500] + "\n...（内容过长，仅显示前500字符）"
                            else:
                                content_preview = content
                            
                            file_text = f"文件内容（{file_path}）：\n{content_preview}"
                        else:
                            file_text = f"文件 {file_path} 为空"
                        
                        state["solution_result"] = {
                            "agent": self.name,
                            "final_response": file_text
                        }
                        state["current_agent"] = self.name
                        state["next_agent"] = None
                        state["is_complete"] = True
                        logger.info(f"{self.name} 直接返回文件内容: {file_path}")
                        return state
                    # 如果文件读取失败
                    elif isinstance(file_data, dict) and not file_data.get("success"):
                        error_msg = file_data.get("error", "文件读取失败")
                        # 简化错误信息
                        if "ENOENT" in error_msg or "no such file" in error_msg.lower():
                            error_msg = "文件不存在，请检查文件路径是否正确"
                        state["solution_result"] = {
                            "agent": self.name,
                            "final_response": f"无法读取文件：{error_msg}"
                        }
                        state["current_agent"] = self.name
                        state["next_agent"] = None
                        state["is_complete"] = True
                        logger.info(f"{self.name} 返回文件读取错误: {error_msg}")
                        return state
        
        # 添加解决方案提示
        solution_prompt = """请基于分析结果和工具结果提供简洁、直接的解决方案。

重要提示：
1. 如果工具结果中有直接答案（如时间、日期、车票信息、文件内容等），请直接使用工具结果回答用户，不要生成复杂的JSON格式。
2. 如果工具结果为空或查询失败，请提供简洁、友好的错误提示，而不是复杂的JSON格式。
3. 对于常见问题（如"如何查询订单"），请提供简洁的步骤说明，而不是复杂的JSON结构。

请用自然语言直接回答用户，格式如下：
- 如果有工具结果：直接使用工具结果回答
- 如果查询失败：简洁说明失败原因和可能的解决方案
- 如果是常见问题：提供简洁的步骤说明

不要返回JSON格式，直接返回自然语言回答。"""
        
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
