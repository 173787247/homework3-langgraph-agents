"""天气查询工具 - 使用免费的天气API"""

from typing import Dict, Any, Optional
import aiohttp
import os
from datetime import datetime

import sys
from pathlib import Path

# 确保可以导入项目模块
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger

logger = get_logger(__name__)


class WeatherTool:
    """天气查询工具 - 支持多个免费天气API"""
    
    def __init__(self):
        """初始化天气查询工具"""
        # OpenWeatherMap API（免费，每天60次请求）
        # 申请地址：https://openweathermap.org/api
        self.openweather_key = os.getenv("OPENWEATHER_API_KEY", "")
        self.openweather_url = "https://api.openweathermap.org/data/2.5"
        
        # 和风天气 API（免费额度：每天1000次）
        # 申请地址：https://dev.qweather.com/
        self.qweather_key = os.getenv("QWEATHER_API_KEY", "")
        self.qweather_url = "https://devapi.qweather.com/v7"
        
        # 选择使用的服务（优先使用和风天气，因为免费额度更高）
        self.service_type = os.getenv("WEATHER_SERVICE", "qweather" if self.qweather_key else "openweather" if self.openweather_key else "mock").lower()
        
        # 如果没有配置任何API Key，使用模拟数据
        self.use_mock = not self.openweather_key and not self.qweather_key
    
    async def query_weather(
        self,
        city: str,
        country: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询天气信息
        
        Args:
            city: 城市名称（如：北京、上海、Beijing）
            country: 国家代码（可选，如：CN、US）
            
        Returns:
            天气信息
        """
        logger.info(f"查询天气: {city}, 国家: {country}")
        
        if self.use_mock:
            return await self._mock_query_weather(city, country)
        
        # 优先使用和风天气（免费额度更高）
        if self.service_type == "qweather" and self.qweather_key:
            try:
                return await self._query_qweather(city)
            except Exception as e:
                logger.warning(f"和风天气API调用失败: {e}，尝试OpenWeatherMap")
                if self.openweather_key:
                    try:
                        return await self._query_openweather(city, country)
                    except Exception as e2:
                        logger.warning(f"OpenWeatherMap也失败: {e2}，使用模拟数据")
                        return await self._mock_query_weather(city, country)
                else:
                    return await self._mock_query_weather(city, country)
        
        # 使用 OpenWeatherMap
        if self.service_type == "openweather" and self.openweather_key:
            try:
                return await self._query_openweather(city, country)
            except Exception as e:
                logger.warning(f"OpenWeatherMap调用失败: {e}，使用模拟数据")
                return await self._mock_query_weather(city, country)
        
        # 默认使用模拟数据
        return await self._mock_query_weather(city, country)
    
    async def _query_openweather(self, city: str, country: Optional[str] = None) -> Dict[str, Any]:
        """查询 OpenWeatherMap API"""
        async with aiohttp.ClientSession() as session:
            # 构建查询参数
            q = f"{city},{country}" if country else city
            url = f"{self.openweather_url}/weather"
            params = {
                "q": q,
                "appid": self.openweather_key,
                "units": "metric",  # 使用摄氏度
                "lang": "zh_cn"  # 中文
            }
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    weather = data.get("weather", [{}])[0]
                    main = data.get("main", {})
                    wind = data.get("wind", {})
                    
                    return {
                        "success": True,
                        "city": data.get("name", city),
                        "country": data.get("sys", {}).get("country", ""),
                        "temperature": main.get("temp", 0),
                        "feels_like": main.get("feels_like", 0),
                        "humidity": main.get("humidity", 0),
                        "pressure": main.get("pressure", 0),
                        "description": weather.get("description", ""),
                        "main": weather.get("main", ""),
                        "wind_speed": wind.get("speed", 0),
                        "wind_degree": wind.get("deg", 0),
                        "visibility": data.get("visibility", 0) / 1000,  # 转换为公里
                        "source": "OpenWeatherMap"
                    }
                else:
                    error_data = await response.text()
                    raise Exception(f"OpenWeatherMap API返回错误: {response.status}, {error_data}")
    
    async def _query_qweather(self, city: str) -> Dict[str, Any]:
        """查询和风天气 API"""
        async with aiohttp.ClientSession() as session:
            # 先获取城市位置信息（使用城市搜索API）
            location_url = f"{self.qweather_url}/city/lookup"
            location_params = {
                "location": city,
                "key": self.qweather_key,
                "number": 1,
                "adm": "CN"  # 限定在中国
            }
            
            async with session.get(location_url, params=location_params, timeout=aiohttp.ClientTimeout(total=10)) as location_response:
                if location_response.status != 200:
                    error_text = await location_response.text()
                    raise Exception(f"和风天气位置查询失败: {location_response.status}, {error_text}")
                
                location_data = await location_response.json()
                if location_data.get("code") != "200" or not location_data.get("location"):
                    raise Exception(f"未找到城市: {city}")
                
                location_id = location_data["location"][0]["id"]
                
                # 查询天气
                weather_url = f"{self.qweather_url}/weather/now"
                weather_params = {
                    "location": location_id,
                    "key": self.qweather_key
                }
                
                async with session.get(weather_url, params=weather_params, timeout=aiohttp.ClientTimeout(total=10)) as weather_response:
                    if weather_response.status == 200:
                        data = await weather_response.json()
                        if data.get("code") == "200":
                            now = data.get("now", {})
                            return {
                                "success": True,
                                "city": location_data["location"][0]["name"],
                                "country": "CN",  # 和风天气主要支持中国
                                "temperature": float(now.get("temp", 0)),
                                "feels_like": float(now.get("feelsLike", 0)),
                                "humidity": int(now.get("humidity", 0)),
                                "pressure": int(now.get("pressure", 0)),
                                "description": now.get("text", ""),
                                "main": now.get("text", ""),
                                "wind_speed": float(now.get("windSpeed", 0)),
                                "wind_degree": int(now.get("wind360", 0)),
                                "visibility": float(now.get("vis", 0)),
                                "source": "和风天气"
                            }
                        else:
                            raise Exception(f"和风天气API返回错误: {data.get('code')}")
                    else:
                        raise Exception(f"和风天气API调用失败: {weather_response.status}")
    
    async def _mock_query_weather(self, city: str, country: Optional[str] = None) -> Dict[str, Any]:
        """模拟天气查询"""
        # 模拟天气数据
        mock_weather = {
            "北京": {
                "temperature": 15,
                "feels_like": 14,
                "humidity": 45,
                "pressure": 1013,
                "description": "晴朗",
                "main": "Clear",
                "wind_speed": 3.5,
                "wind_degree": 180,
                "visibility": 10
            },
            "上海": {
                "temperature": 18,
                "feels_like": 17,
                "humidity": 60,
                "pressure": 1015,
                "description": "多云",
                "main": "Clouds",
                "wind_speed": 4.2,
                "wind_degree": 135,
                "visibility": 8
            },
            "广州": {
                "temperature": 25,
                "feels_like": 26,
                "humidity": 70,
                "pressure": 1010,
                "description": "小雨",
                "main": "Rain",
                "wind_speed": 2.8,
                "wind_degree": 90,
                "visibility": 6
            }
        }
        
        weather_data = mock_weather.get(city, {
            "temperature": 20,
            "feels_like": 19,
            "humidity": 50,
            "pressure": 1012,
            "description": "晴朗",
            "main": "Clear",
            "wind_speed": 3.0,
            "wind_degree": 180,
            "visibility": 10
        })
        
        return {
            "success": True,
            "city": city,
            "country": country or "CN",
            **weather_data,
            "source": "模拟数据",
            "note": "配置 OPENWEATHER_API_KEY 或 QWEATHER_API_KEY 后可使用真实API"
        }
