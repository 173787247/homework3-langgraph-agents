"""工作流状态定义"""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime


class CustomerServiceState(TypedDict):
    """客服工作流状态"""
    
    # 用户信息
    user_id: str
    user_input: str
    conversation_history: List[Dict[str, str]]
    
    # 智能体处理结果
    receptionist_result: Optional[Dict[str, Any]]
    analysis_result: Optional[Dict[str, Any]]
    solution_result: Optional[Dict[str, Any]]
    
    # 工具调用结果
    tool_results: Dict[str, Any]
    
    # 工作流控制
    current_agent: Optional[str]
    next_agent: Optional[str]
    is_complete: bool
    needs_human_intervention: bool
    
    # 上下文信息
    context: Dict[str, Any]
    
    # 错误处理
    error: Optional[str]
    retry_count: int
    
    # 元数据
    session_id: str
    created_at: datetime
    updated_at: datetime
