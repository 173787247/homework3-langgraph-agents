"""订单查询工具"""

from typing import Dict, Any
import os

import sys
from pathlib import Path

# 确保可以导入项目模块
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger

logger = get_logger(__name__)


class OrderQueryTool:
    """订单查询工具"""
    
    def __init__(self):
        """初始化订单查询工具"""
        self.order_service_url = os.getenv(
            "ORDER_SERVICE_URL",
            "http://localhost:8003"
        )
        
        # 模拟订单数据（实际应该连接真实的订单系统）
        self.mock_orders = {
            "ORD123456": {
                "order_id": "ORD123456",
                "status": "已发货",
                "create_time": "2024-01-05 10:30:00",
                "delivery_time": "预计2024-01-08 18:00:00",
                "items": [
                    {"name": "产品A", "quantity": 2, "price": 99.00}
                ],
                "total_amount": 198.00,
                "shipping_address": "北京市朝阳区xxx街道xxx号"
            },
            "ORD789012": {
                "order_id": "ORD789012",
                "status": "处理中",
                "create_time": "2024-01-07 14:20:00",
                "delivery_time": "预计2024-01-10 18:00:00",
                "items": [
                    {"name": "产品B", "quantity": 1, "price": 199.00}
                ],
                "total_amount": 199.00,
                "shipping_address": "上海市浦东新区xxx路xxx号"
            }
        }
    
    async def query(self, order_id: str) -> Dict[str, Any]:
        """
        查询订单信息
        
        Args:
            order_id: 订单号
            
        Returns:
            订单信息
        """
        logger.info(f"查询订单: {order_id}")
        
        # 模拟查询逻辑（实际应该调用真实的订单API）
        order_id_upper = order_id.upper()
        
        if order_id_upper in self.mock_orders:
            return self.mock_orders[order_id_upper]
        else:
            # 返回模拟的订单信息（即使订单号不存在）
            return {
                "order_id": order_id,
                "status": "未找到",
                "message": f"未找到订单号为 {order_id} 的订单，请确认订单号是否正确。"
            }
