"""记忆管理模块"""

import sys
from pathlib import Path

# 确保可以导入项目模块
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from .memory_store import MemoryStore
    from .conversation_manager import ConversationManager
except ImportError:
    from memory.memory_store import MemoryStore
    from memory.conversation_manager import ConversationManager

__all__ = ["MemoryStore", "ConversationManager"]
