"""工作流模块"""

import sys
from pathlib import Path

# 确保可以导入项目模块
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from .state import CustomerServiceState
    from .customer_service_graph import CustomerServiceGraph
except ImportError:
    from workflow.state import CustomerServiceState
    from workflow.customer_service_graph import CustomerServiceGraph

__all__ = ["CustomerServiceState", "CustomerServiceGraph"]
