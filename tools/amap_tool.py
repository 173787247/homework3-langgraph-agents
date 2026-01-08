"""高德地图地址查询工具"""

from typing import Dict, Any, Optional
import aiohttp
import os

import sys
from pathlib import Path

# 确保可以导入项目模块
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger

logger = get_logger(__name__)


class AmapTool:
    """高德地图地址查询工具"""
    
    def __init__(self):
        """初始化高德地图工具"""
        # 高德地图 API Key（必需）
        self.api_key = os.getenv("AMAP_API_KEY", "")
        self.base_url = "https://restapi.amap.com/v3"
        
        # 如果没有配置 API key，使用模拟数据
        self.use_mock = not self.api_key
    
    async def geocode(
        self,
        address: str,
        city: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        地理编码：将地址转换为经纬度
        
        Args:
            address: 地址（如：北京市朝阳区xxx街道）
            city: 城市（可选，用于限定搜索范围）
            
        Returns:
            地理编码结果（包含经纬度、详细地址等）
        """
        logger.info(f"地理编码查询: {address}, 城市: {city}")
        
        if self.use_mock:
            return await self._mock_geocode(address, city)
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/geocode/geo"
                params = {
                    "key": self.api_key,
                    "address": address
                }
                if city:
                    params["city"] = city
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1":
                            return {
                                "success": True,
                                "address": address,
                                "location": data.get("geocodes", [{}])[0].get("location", ""),
                                "formatted_address": data.get("geocodes", [{}])[0].get("formatted_address", ""),
                                "province": data.get("geocodes", [{}])[0].get("province", ""),
                                "city": data.get("geocodes", [{}])[0].get("city", ""),
                                "district": data.get("geocodes", [{}])[0].get("district", "")
                            }
                        else:
                            logger.warning(f"高德地图 API 返回错误: {data.get('info')}，使用模拟数据")
                            return await self._mock_geocode(address, city)
                    else:
                        logger.warning(f"高德地图 API 调用失败: {response.status}，使用模拟数据")
                        return await self._mock_geocode(address, city)
        except Exception as e:
            logger.error(f"高德地图 API 调用异常: {e}，使用模拟数据")
            return await self._mock_geocode(address, city)
    
    async def reverse_geocode(
        self,
        longitude: float,
        latitude: float
    ) -> Dict[str, Any]:
        """
        逆地理编码：将经纬度转换为地址
        
        Args:
            longitude: 经度
            latitude: 纬度
            
        Returns:
            地址信息
        """
        logger.info(f"逆地理编码查询: ({longitude}, {latitude})")
        
        if self.use_mock:
            return await self._mock_reverse_geocode(longitude, latitude)
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/geocode/regeo"
                params = {
                    "key": self.api_key,
                    "location": f"{longitude},{latitude}"
                }
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1":
                            regeocode = data.get("regeocode", {})
                            address_component = regeocode.get("addressComponent", {})
                            return {
                                "success": True,
                                "location": f"{longitude},{latitude}",
                                "formatted_address": regeocode.get("formatted_address", ""),
                                "province": address_component.get("province", ""),
                                "city": address_component.get("city", ""),
                                "district": address_component.get("district", ""),
                                "street": address_component.get("street", ""),
                                "street_number": address_component.get("streetNumber", "")
                            }
                        else:
                            logger.warning(f"高德地图 API 返回错误: {data.get('info')}，使用模拟数据")
                            return await self._mock_reverse_geocode(longitude, latitude)
                    else:
                        logger.warning(f"高德地图 API 调用失败: {response.status}，使用模拟数据")
                        return await self._mock_reverse_geocode(longitude, latitude)
        except Exception as e:
            logger.error(f"高德地图 API 调用异常: {e}，使用模拟数据")
            return await self._mock_reverse_geocode(longitude, latitude)
    
    async def search_poi(
        self,
        keywords: str,
        city: Optional[str] = None,
        types: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        搜索 POI（兴趣点）
        
        Args:
            keywords: 关键词（如：餐厅、酒店、银行）
            city: 城市（可选）
            types: POI 类型（可选，如：餐饮服务、购物服务）
            
        Returns:
            POI 列表
        """
        logger.info(f"POI 搜索: {keywords}, 城市: {city}")
        
        if self.use_mock:
            return await self._mock_search_poi(keywords, city)
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/place/text"
                params = {
                    "key": self.api_key,
                    "keywords": keywords
                }
                if city:
                    params["city"] = city
                if types:
                    params["types"] = types
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1":
                            pois = data.get("pois", [])
                            return {
                                "success": True,
                                "keywords": keywords,
                                "count": len(pois),
                                "pois": [
                                    {
                                        "name": poi.get("name", ""),
                                        "address": poi.get("address", ""),
                                        "location": poi.get("location", ""),
                                        "type": poi.get("type", ""),
                                        "tel": poi.get("tel", "")
                                    }
                                    for poi in pois[:10]  # 最多返回10个
                                ]
                            }
                        else:
                            logger.warning(f"高德地图 API 返回错误: {data.get('info')}，使用模拟数据")
                            return await self._mock_search_poi(keywords, city)
                    else:
                        logger.warning(f"高德地图 API 调用失败: {response.status}，使用模拟数据")
                        return await self._mock_search_poi(keywords, city)
        except Exception as e:
            logger.error(f"高德地图 API 调用异常: {e}，使用模拟数据")
            return await self._mock_search_poi(keywords, city)
    
    async def _mock_geocode(self, address: str, city: Optional[str] = None) -> Dict[str, Any]:
        """模拟地理编码"""
        # 模拟数据
        mock_locations = {
            "北京": {"longitude": 116.397128, "latitude": 39.916527},
            "上海": {"longitude": 121.473701, "latitude": 31.230416},
            "广州": {"longitude": 113.264385, "latitude": 23.129112},
            "深圳": {"longitude": 114.057868, "latitude": 22.543099}
        }
        
        location = mock_locations.get(city or address[:2] if address else "北京", mock_locations["北京"])
        
        return {
            "success": True,
            "address": address,
            "location": f"{location['longitude']},{location['latitude']}",
            "formatted_address": f"{city or '北京市'}{address}",
            "province": city or "北京市",
            "city": city or "北京市",
            "district": "朝阳区",
            "note": "当前为模拟数据，配置 AMAP_API_KEY 后可使用真实 API"
        }
    
    async def _mock_reverse_geocode(self, longitude: float, latitude: float) -> Dict[str, Any]:
        """模拟逆地理编码"""
        return {
            "success": True,
            "location": f"{longitude},{latitude}",
            "formatted_address": f"模拟地址（经度: {longitude}, 纬度: {latitude}）",
            "province": "北京市",
            "city": "北京市",
            "district": "朝阳区",
            "street": "模拟街道",
            "street_number": "123号",
            "note": "当前为模拟数据，配置 AMAP_API_KEY 后可使用真实 API"
        }
    
    async def _mock_search_poi(self, keywords: str, city: Optional[str] = None) -> Dict[str, Any]:
        """模拟 POI 搜索"""
        mock_pois = [
            {
                "name": f"{keywords}示例1",
                "address": f"{city or '北京市'}示例街道1号",
                "location": "116.397128,39.916527",
                "type": keywords,
                "tel": "010-12345678"
            },
            {
                "name": f"{keywords}示例2",
                "address": f"{city or '北京市'}示例街道2号",
                "location": "116.407128,39.926527",
                "type": keywords,
                "tel": "010-87654321"
            }
        ]
        
        return {
            "success": True,
            "keywords": keywords,
            "count": len(mock_pois),
            "pois": mock_pois,
            "note": "当前为模拟数据，配置 AMAP_API_KEY 后可使用真实 API"
        }
