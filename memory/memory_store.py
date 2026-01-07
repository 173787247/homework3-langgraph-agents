"""记忆存储 - 支持多轮对话的持久化存储"""

from typing import List, Dict, Optional
from datetime import datetime
import sqlite3
import json
import os
from pathlib import Path

import sys
from pathlib import Path

# 确保可以导入项目模块
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger

logger = get_logger(__name__)


class MemoryStore:
    """记忆存储"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化记忆存储
        
        Args:
            db_path: 数据库路径
        """
        if db_path is None:
            db_path = os.getenv("DATABASE_URL", "sqlite:///./data/conversations.db")
            # 处理 SQLite URL 格式
            if db_path.startswith("sqlite:///"):
                db_path = db_path.replace("sqlite:///", "")
        
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """确保数据库目录存在"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建消息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id ON messages(session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id ON sessions(user_id)
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"数据库初始化完成: {self.db_path}")
    
    async def get_conversation_history(
        self,
        user_id: str,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, str]]:
        """
        获取对话历史
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            limit: 最大消息数
            
        Returns:
            对话历史列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT role, content, metadata
            FROM messages
            WHERE session_id = ?
            ORDER BY created_at ASC
            LIMIT ?
        """, (session_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "role": row[0],
                "content": row[1],
                "metadata": json.loads(row[2]) if row[2] else {}
            })
        
        return history
    
    async def save_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """
        保存消息
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            role: 角色（user/assistant）
            content: 消息内容
            metadata: 元数据
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 确保会话存在
        cursor.execute("""
            INSERT OR IGNORE INTO sessions (session_id, user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (session_id, user_id, datetime.now(), datetime.now()))
        
        # 更新会话更新时间
        cursor.execute("""
            UPDATE sessions
            SET updated_at = ?
            WHERE session_id = ?
        """, (datetime.now(), session_id))
        
        # 保存消息
        metadata_str = json.dumps(metadata) if metadata else None
        cursor.execute("""
            INSERT INTO messages (session_id, role, content, metadata, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, role, content, metadata_str, datetime.now()))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"消息已保存: session_id={session_id}, role={role}")
    
    async def get_user_sessions(self, user_id: str) -> List[str]:
        """
        获取用户的所有会话ID
        
        Args:
            user_id: 用户ID
            
        Returns:
            会话ID列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT session_id
            FROM sessions
            WHERE user_id = ?
            ORDER BY updated_at DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows]
    
    async def delete_session(self, session_id: str):
        """
        删除会话
        
        Args:
            session_id: 会话ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"会话已删除: session_id={session_id}")
