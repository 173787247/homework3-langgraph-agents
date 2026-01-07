"""智能体模块"""

import sys
from pathlib import Path

# 确保可以导入项目模块
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

# 延迟导入，避免在包初始化时失败
def _import_agents():
    """延迟导入智能体类"""
    try:
        from .base_agent import BaseAgent
        from .receptionist_agent import ReceptionistAgent
        from .analyst_agent import AnalystAgent
        from .solution_expert_agent import SolutionExpertAgent
        return BaseAgent, ReceptionistAgent, AnalystAgent, SolutionExpertAgent
    except (ImportError, ValueError):
        # 如果相对导入失败，使用绝对导入
        try:
            from agents.base_agent import BaseAgent
            from agents.receptionist_agent import ReceptionistAgent
            from agents.analyst_agent import AnalystAgent
            from agents.solution_expert_agent import SolutionExpertAgent
            return BaseAgent, ReceptionistAgent, AnalystAgent, SolutionExpertAgent
        except ImportError:
            # 如果都失败，返回 None，让调用者处理
            return None, None, None, None

# 尝试导入，但不强制
try:
    BaseAgent, ReceptionistAgent, AnalystAgent, SolutionExpertAgent = _import_agents()
except Exception:
    # 如果导入失败，设置为 None，允许后续直接导入
    BaseAgent = None
    ReceptionistAgent = None
    AnalystAgent = None
    SolutionExpertAgent = None

__all__ = [
    "BaseAgent",
    "ReceptionistAgent",
    "AnalystAgent",
    "SolutionExpertAgent",
]
