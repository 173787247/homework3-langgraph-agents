"""知识库查询工具"""

from typing import Dict, Any, Optional
import os

import sys
from pathlib import Path

# 确保可以导入项目模块
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger

logger = get_logger(__name__)


class KnowledgeBaseTool:
    """知识库查询工具"""
    
    def __init__(self):
        """初始化知识库工具"""
        self.knowledge_base_url = os.getenv(
            "KNOWLEDGE_BASE_URL",
            "http://localhost:8002"
        )
        
        # 模拟知识库数据（实际应该连接真实的知识库）
        self.mock_knowledge_base = {
            "订单问题": [
                {
                    "question": "订单什么时候能到？",
                    "answer": "订单通常在3-5个工作日内送达，具体时间取决于您的地址和选择的配送方式。",
                    "related_articles": ["配送政策", "订单跟踪"]
                },
                {
                    "question": "如何查询订单状态？",
                    "answer": "您可以通过订单号在我们的官网或APP上查询订单状态，也可以联系客服查询。",
                    "related_articles": ["订单查询指南"]
                }
            ],
            "产品咨询": [
                {
                    "question": "产品有哪些规格？",
                    "answer": "我们的产品有多种规格可选，具体规格请查看产品详情页或咨询客服。",
                    "related_articles": ["产品规格说明"]
                }
            ],
            "技术支持": [
                {
                    "question": "如何使用产品？",
                    "answer": "产品使用说明请参考随产品附带的说明书，或访问我们的官网查看在线教程。",
                    "related_articles": ["使用教程", "常见问题"]
                }
            ]
        }
    
    async def query(
        self,
        query: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询知识库
        
        Args:
            query: 查询内容
            category: 问题类别
            
        Returns:
            查询结果
        """
        logger.info(f"查询知识库: {query}, 类别: {category}")
        
        # 模拟查询逻辑（实际应该调用真实的知识库API）
        results = []
        
        if category and category in self.mock_knowledge_base:
            for item in self.mock_knowledge_base[category]:
                if query.lower() in item["question"].lower() or query.lower() in item["answer"].lower():
                    results.append(item)
        
        # 如果没有指定类别或没找到，搜索所有类别
        if not results:
            for cat_items in self.mock_knowledge_base.values():
                for item in cat_items:
                    if query.lower() in item["question"].lower() or query.lower() in item["answer"].lower():
                        results.append(item)
                        if len(results) >= 3:  # 最多返回3条
                            break
                if len(results) >= 3:
                    break
        
        return {
            "query": query,
            "category": category,
            "results": results,
            "count": len(results)
        }
