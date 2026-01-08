"""12306 火车票查询工具"""

from typing import Dict, Any, Optional
import aiohttp
import os
import asyncio
from datetime import datetime, timedelta

import sys
from pathlib import Path

# 确保可以导入项目模块
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger

logger = get_logger(__name__)

# 尝试导入 MCP SDK
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("MCP SDK 不可用，将使用其他方式")


class TrainTicketTool:
    """12306 火车票查询工具"""
    
    def __init__(self):
        """初始化火车票查询工具"""
        # 12306 查询服务配置
        # 免费服务：
        # 1. npx 12306-mcp (免费，通过npx运行本地MCP服务)
        # 2. UniCloud合一云: 免费5次/天 (https://www.apiuni.cn/product/uniapi/detail/20aaab164)
        # 付费服务：
        # 3. YikeAPI: 付费 (https://yikeapi.com/index/traininfo)
        
        # 选择使用的服务类型
        self.service_type = os.getenv("TRAIN_TICKET_SERVICE", "mock").lower()  # mock, mcp, apiumi, yikeapi
        
        # 本地MCP服务配置（免费）
        self.mcp_command = os.getenv("TRAIN_TICKET_MCP_COMMAND", "npx")
        self.mcp_args = os.getenv("TRAIN_TICKET_MCP_ARGS", "-y,12306-mcp").split(",")
        
        # YikeAPI 配置（付费）
        self.yikeapi_key = os.getenv("YIKEAPI_KEY", "")
        self.yikeapi_url = "https://api.yikeapi.com/train"
        
        # UniCloud API 配置（免费5次/天）
        self.apiumi_key = os.getenv("APIUMI_KEY", "")
        self.apiumi_url = "https://api.apiuni.cn/api/train"
        
        # 如果没有配置任何服务，使用模拟数据
        self.use_mock = self.service_type == "mock" or (
            self.service_type == "mcp" and not self.mcp_command or
            self.service_type == "apiumi" and not self.apiumi_key or
            self.service_type == "yikeapi" and not self.yikeapi_key
        )
    
    async def query_trains(
        self,
        from_station: str,
        to_station: str,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询火车票信息
        
        Args:
            from_station: 出发站（如：北京、上海）
            to_station: 到达站（如：上海、广州）
            date: 出发日期（格式：YYYY-MM-DD），默认为明天
            
        Returns:
            车次信息列表
        """
        logger.info(f"查询火车票: {from_station} -> {to_station}, 日期: {date}")
        
        if self.use_mock:
            return await self._mock_query_trains(from_station, to_station, date)
        
        if not date:
            date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 优先使用 MCP 服务（真正的 MCP 协议）
        if self.service_type == "mcp" and MCP_AVAILABLE and self.mcp_command:
            try:
                result = await self._query_via_mcp(from_station, to_station, date)
                if result.get("success"):
                    return result
            except Exception as e:
                logger.error(f"MCP服务调用失败: {e}，尝试其他服务", exc_info=True)
        
        try:
            async with aiohttp.ClientSession() as session:
                # 尝试使用 YikeAPI
                if self.service_type == "yikeapi" and self.yikeapi_key:
                    try:
                        url = f"{self.yikeapi_url}/query"
                        params = {
                            "key": self.yikeapi_key,
                            "from": from_station,
                            "to": to_station,
                            "date": date
                        }
                        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            if response.status == 200:
                                data = await response.json()
                                if data.get("code") == 200 or data.get("success"):
                                    trains = self._parse_yikeapi_data(data)
                                    return {
                                        "success": True,
                                        "from_station": from_station,
                                        "to_station": to_station,
                                        "date": date,
                                        "trains": trains,
                                        "source": "YikeAPI"
                                    }
                    except Exception as e:
                        logger.warning(f"YikeAPI调用失败: {e}，尝试其他服务")
                
                # 尝试使用 UniCloud API
                if self.service_type == "apiumi" and self.apiumi_key:
                    try:
                        url = f"{self.apiumi_url}/query"
                        headers = {"Authorization": f"Bearer {self.apiumi_key}"}
                        payload = {
                            "from": from_station,
                            "to": to_station,
                            "date": date
                        }
                        async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            if response.status == 200:
                                data = await response.json()
                                if data.get("code") == 200 or data.get("success"):
                                    trains = self._parse_apiumi_data(data)
                                    return {
                                        "success": True,
                                        "from_station": from_station,
                                        "to_station": to_station,
                                        "date": date,
                                        "trains": trains,
                                        "source": "UniCloud API"
                                    }
                    except Exception as e:
                        logger.warning(f"UniCloud API调用失败: {e}，使用模拟数据")
                
                # 如果所有服务都失败，使用模拟数据
                logger.info("所有在线服务都不可用，使用模拟数据")
                return await self._mock_query_trains(from_station, to_station, date)
        except Exception as e:
            logger.error(f"MCP服务调用异常: {e}，使用模拟数据")
            return await self._mock_query_trains(from_station, to_station, date)
    
    async def _mock_query_trains(
        self,
        from_station: str,
        to_station: str,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """模拟火车票查询"""
        if not date:
            date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 模拟车次数据
        mock_trains = [
            {
                "train_no": "G123",
                "train_type": "高速",
                "from_station": from_station,
                "to_station": to_station,
                "departure_time": "08:00",
                "arrival_time": "12:30",
                "duration": "4小时30分",
                "business_seat": {"available": True, "price": "¥1748"},
                "first_class": {"available": True, "price": "¥924"},
                "second_class": {"available": True, "price": "¥554"},
                "hard_seat": {"available": False, "price": "¥128"}
            },
            {
                "train_no": "D456",
                "train_type": "动车",
                "from_station": from_station,
                "to_station": to_station,
                "departure_time": "10:30",
                "arrival_time": "15:45",
                "duration": "5小时15分",
                "business_seat": {"available": False, "price": "¥1280"},
                "first_class": {"available": True, "price": "¥640"},
                "second_class": {"available": True, "price": "¥384"},
                "hard_seat": {"available": True, "price": "¥128"}
            },
            {
                "train_no": "K789",
                "train_type": "快速",
                "from_station": from_station,
                "to_station": to_station,
                "departure_time": "14:20",
                "arrival_time": "22:10",
                "duration": "7小时50分",
                "business_seat": {"available": False, "price": "N/A"},
                "first_class": {"available": False, "price": "N/A"},
                "second_class": {"available": True, "price": "¥224"},
                "hard_seat": {"available": True, "price": "¥128"}
            }
        ]
        
        return {
            "success": True,
            "from_station": from_station,
            "to_station": to_station,
            "date": date,
            "trains": mock_trains,
            "note": "当前为模拟数据，配置 TRAIN_TICKET_API_KEY 后可使用真实 API"
        }
    
    def _parse_yikeapi_data(self, data: Dict[str, Any]) -> list:
        """解析 YikeAPI 返回的数据"""
        trains = []
        result = data.get("data", {})
        train_list = result.get("trains", []) if isinstance(result, dict) else []
        
        for train in train_list:
            trains.append({
                "train_no": train.get("train_no", ""),
                "train_type": train.get("train_type", ""),
                "from_station": train.get("from_station", ""),
                "to_station": train.get("to_station", ""),
                "departure_time": train.get("departure_time", ""),
                "arrival_time": train.get("arrival_time", ""),
                "duration": train.get("duration", ""),
                "business_seat": train.get("business_seat", {}),
                "first_class": train.get("first_class", {}),
                "second_class": train.get("second_class", {}),
                "hard_seat": train.get("hard_seat", {})
            })
        return trains
    
    def _parse_apiumi_data(self, data: Dict[str, Any]) -> list:
        """解析 UniCloud API 返回的数据"""
        trains = []
        train_list = data.get("data", {}).get("trains", []) if isinstance(data.get("data"), dict) else []
        
        for train in train_list:
            trains.append({
                "train_no": train.get("train_no", ""),
                "train_type": train.get("train_type", ""),
                "from_station": train.get("from_station", ""),
                "to_station": train.get("to_station", ""),
                "departure_time": train.get("departure_time", ""),
                "arrival_time": train.get("arrival_time", ""),
                "duration": train.get("duration", ""),
                "business_seat": train.get("business_seat", {}),
                "first_class": train.get("first_class", {}),
                "second_class": train.get("second_class", {}),
                "hard_seat": train.get("hard_seat", {})
            })
        return trains
    
    async def _query_via_mcp(
        self,
        from_station: str,
        to_station: str,
        date: str
    ) -> Dict[str, Any]:
        """
        通过真正的 MCP 协议查询火车票
        
        Args:
            from_station: 出发站
            to_station: 到达站
            date: 出发日期
            
        Returns:
            车次信息
        """
        if not MCP_AVAILABLE:
            raise Exception("MCP SDK 不可用")
        
        try:
            # 配置 MCP 服务器参数（stdio 方式）
            server_params = StdioServerParameters(
                command=self.mcp_command,
                args=self.mcp_args
            )
            
            # 连接到 MCP 服务器
            # stdio_client 是一个异步上下文管理器
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # 初始化会话
                    await session.initialize()
                    
                    # 列出可用工具
                    tools = await session.list_tools()
                    logger.info(f"MCP 可用工具: {[tool.name for tool in tools.tools]}")
                    
                    # 查找查询余票的工具（get-tickets）
                    query_tool = None
                    for tool in tools.tools:
                        if tool.name == "get-tickets":
                            query_tool = tool
                            break
                    
                    if not query_tool:
                        raise Exception("未找到 get-tickets 工具")
                    
                    # 先获取车站代码（12306 需要车站代码）
                    from_code = from_station
                    to_code = to_station
                    
                    # 查找车站代码查询工具并查看参数定义
                    station_code_tool = None
                    for tool in tools.tools:
                        if tool.name == "get-station-code-by-names":
                            station_code_tool = tool
                            logger.info(f"get-station-code-by-names 工具定义: {tool.inputSchema if hasattr(tool, 'inputSchema') else 'N/A'}")
                            break
                    
                    # 查看 get-tickets 的参数定义
                    logger.info(f"get-tickets 工具定义: {query_tool.inputSchema if hasattr(query_tool, 'inputSchema') else 'N/A'}")
                    
                    # 如果找到了车站代码查询工具，先查询车站代码
                    if station_code_tool:
                        try:
                            logger.info(f"查询出发站代码: {from_station}")
                            # 根据工具定义，参数是 stationNames (字符串)
                            from_result = await session.call_tool(
                                "get-station-code-by-names",
                                arguments={"stationNames": from_station}
                            )
                            
                            if from_result.content and len(from_result.content) > 0:
                                import json
                                from_text = from_result.content[0].text if hasattr(from_result.content[0], 'text') else str(from_result.content[0])
                                logger.info(f"出发站代码查询结果: {from_text[:200]}")  # 打印前200字符用于调试
                                if from_text.strip():
                                    from_data = json.loads(from_text)
                                    # 提取车站代码（根据实际返回格式：{"北京":{"station_code":"BJP",...}}）
                                    if isinstance(from_data, dict):
                                        # 返回格式是 {城市名: {station_code: "xxx", ...}}
                                        # 取第一个值（车站信息）
                                        station_info = list(from_data.values())[0] if from_data else {}
                                        from_code = station_info.get("station_code") or station_info.get("code") or station_info.get("telecode", from_station)
                                        logger.info(f"出发站代码: {from_code}")
                                    elif isinstance(from_data, list) and len(from_data) > 0:
                                        from_code = from_data[0].get("station_code") or from_data[0].get("code") or from_data[0].get("telecode", from_station)
                                        logger.info(f"出发站代码: {from_code}")
                            
                            logger.info(f"查询到达站代码: {to_station}")
                            # 根据工具定义，参数是 stationNames (字符串)
                            to_result = await session.call_tool(
                                "get-station-code-by-names",
                                arguments={"stationNames": to_station}
                            )
                            
                            if to_result.content and len(to_result.content) > 0:
                                import json
                                to_text = to_result.content[0].text if hasattr(to_result.content[0], 'text') else str(to_result.content[0])
                                logger.info(f"到达站代码查询结果: {to_text[:200]}")  # 打印前200字符用于调试
                                if to_text.strip():
                                    to_data = json.loads(to_text)
                                    # 提取车站代码（根据实际返回格式：{"上海":{"station_code":"SHH",...}}）
                                    if isinstance(to_data, dict):
                                        # 返回格式是 {城市名: {station_code: "xxx", ...}}
                                        # 取第一个值（车站信息）
                                        station_info = list(to_data.values())[0] if to_data else {}
                                        to_code = station_info.get("station_code") or station_info.get("code") or station_info.get("telecode", to_station)
                                        logger.info(f"到达站代码: {to_code}")
                                    elif isinstance(to_data, list) and len(to_data) > 0:
                                        to_code = to_data[0].get("station_code") or to_data[0].get("code") or to_data[0].get("telecode", to_station)
                                        logger.info(f"到达站代码: {to_code}")
                        except Exception as e:
                            logger.warning(f"获取车站代码失败: {e}，尝试使用原始名称", exc_info=True)
                    
                    # 使用车站代码调用 get-tickets 工具查询火车票
                    # 根据工具定义，参数是 fromStation, toStation, date
                    logger.info(f"调用 get-tickets: fromStation={from_code}, toStation={to_code}, date={date}")
                    result = await session.call_tool(
                        "get-tickets",
                        arguments={
                            "fromStation": from_code,
                            "toStation": to_code,
                            "date": date,
                            "format": "json"  # 使用 JSON 格式便于解析
                        }
                    )
                    
                    # 解析结果
                    if result.content:
                        # MCP 返回的内容可能是文本或结构化数据
                        content = result.content[0] if result.content else {}
                        if hasattr(content, 'text'):
                            import json
                            result_text = content.text
                            logger.info(f"get-tickets 返回结果: {result_text[:500]}")  # 打印前500字符用于调试
                            try:
                                data = json.loads(result_text)
                            except:
                                # 如果不是 JSON，尝试其他格式
                                logger.warning(f"JSON 解析失败，原始内容: {result_text[:200]}")
                                data = {"raw": result_text, "trains": []}
                        else:
                            data = content
                        
                        # 提取车次数据（可能在不同字段中）
                        trains = []
                        if isinstance(data, dict):
                            trains = data.get("trains", data.get("data", data.get("result", [])))
                        elif isinstance(data, list):
                            trains = data
                        
                        logger.info(f"解析到 {len(trains)} 个车次")
                        
                        return {
                            "success": True,
                            "from_station": from_station,
                            "to_station": to_station,
                            "date": date,
                            "trains": trains,
                            "source": "12306 MCP (真实MCP服务)"
                        }
                    else:
                        raise Exception("MCP 服务返回空结果")
                        
        except Exception as e:
            logger.error(f"MCP 查询失败: {e}")
            raise
    
    async def query_station_code(self, station_name: str) -> Dict[str, Any]:
        """
        查询车站代码（12306 使用车站代码而非名称）
        
        Args:
            station_name: 车站名称
            
        Returns:
            车站代码信息
        """
        logger.info(f"查询车站代码: {station_name}")
        
        # 常用车站代码映射（实际应该从 API 获取）
        station_codes = {
            "北京": "BJP",
            "上海": "SHH",
            "广州": "GZQ",
            "深圳": "SZQ",
            "杭州": "HZH",
            "南京": "NJH",
            "武汉": "WHN",
            "成都": "CDW",
            "重庆": "CQW",
            "西安": "XAY"
        }
        
        code = station_codes.get(station_name, "")
        return {
            "success": True,
            "station_name": station_name,
            "station_code": code,
            "note": "配置 TRAIN_TICKET_API_KEY 后可查询更多车站"
        }
