import sqlite3
import json
import aiosqlite
from astrbot.api import logger
from datetime import datetime

class MessageStorage:
    def __init__(self, db_path: str = "wechat_helper.db"):
        self.db_path = db_path
        self.db = None
        
    async def initialize(self):
        """初始化数据库"""
        self.db = await aiosqlite.connect(self.db_path)
        await self._create_tables()
        logger.info("数据库初始化完成")
        
    async def close(self):
        """关闭数据库连接"""
        if self.db:
            await self.db.close()
            
    async def _create_tables(self):
        """创建数据表"""
        # 消息记录表
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id TEXT,
                sender_name TEXT,
                message TEXT,
                message_chain TEXT,
                timestamp INTEGER,
                platform TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 备忘录表
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS memos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id TEXT,
                sender_name TEXT,
                content TEXT,
                timestamp INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 笔记记录表
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                url TEXT,
                message_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await self.db.commit()
        
    async def save_message(self, message_info: dict):
        """保存消息记录"""
        try:
            await self.db.execute('''
                INSERT INTO messages (sender_id, sender_name, message, message_chain, timestamp, platform)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                message_info['sender_id'],
                message_info['sender_name'],
                message_info['message_str'],
                json.dumps([msg.to_dict() for msg in message_info['message_chain']]) if message_info['message_chain'] else '',
                message_info['timestamp'],
                message_info['platform']
            ))
            await self.db.commit()
        except Exception as e:
            logger.error(f"保存消息失败: {e}")
            
    async def save_memo(self, message_info: dict):
        """保存备忘录"""
        try:
            await self.db.execute('''
                INSERT INTO memos (sender_id, sender_name, content, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (
                message_info['sender_id'],
                message_info['sender_name'],
                message_info['message_str'],
                message_info['timestamp']
            ))
            await self.db.commit()
        except Exception as e:
            logger.error(f"保存备忘录失败: {e}")
            
    async def save_note_record(self, title: str, content: str, url: str, message_id: int = None):
        """保存笔记记录"""
        try:
            await self.db.execute('''
                INSERT INTO notes (title, content, url, message_id)
                VALUES (?, ?, ?, ?)
            ''', (title, content, url, message_id))
            await self.db.commit()
        except Exception as e:
            logger.error(f"保存笔记记录失败: {e}")