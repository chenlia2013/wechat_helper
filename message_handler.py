import asyncio
import re
from astrbot.api import logger
from astrbot.api.message_components import MessageType
from .storage import MessageStorage
from .article_parser import ArticleParser
from .note_service import NoteService

class MessageHandler:
    def __init__(self):
        self.storage = None
        self.article_parser = None
        self.note_service = None
        
    async def initialize(self):
        """初始化消息处理器"""
        self.storage = MessageStorage()
        await self.storage.initialize()
        
        self.article_parser = ArticleParser()
        self.note_service = NoteService()
        
        logger.info("消息处理器初始化完成")
        
    async def close(self):
        """关闭处理器"""
        if self.storage:
            await self.storage.close()
            
    async def process_message(self, event: AstrMessageEvent):
        """处理消息"""
        # 提取消息基本信息
        message_info = {
            'sender_id': event.get_sender_id(),
            'sender_name': event.get_sender_name(),
            'message_str': event.message_str,
            'message_chain': event.get_messages(),
            'timestamp': event.timestamp,
            'platform': event.get_platform_name()
        }
        
        # 记录所有消息
        await self.storage.save_message(message_info)
        logger.info(f"已记录消息: {message_info['sender_name']} -> {message_info['message_str'][:50]}...")
        
        # 检查是否来自文件传输助手
        if self._is_file_transfer_assistant(event):
            await self._handle_file_transfer_message(event, message_info)
            
    def _is_file_transfer_assistant(self, event: AstrMessageEvent) -> bool:
        """判断是否来自文件传输助手"""
        sender_name = event.get_sender_name().lower()
        # 常见的文件传输助手名称
        file_assistant_names = ['file', '文件传输助手', 'filehelper', '文件']
        return any(name in sender_name for name in file_assistant_names)
        
    async def _handle_file_transfer_message(self, event: AstrMessageEvent, message_info: dict):
        """处理文件传输助手的消息"""
        message_str = message_info['message_str']
        message_chain = message_info['message_chain']
        
        # 检查是否包含链接
        urls = self._extract_urls(message_str)
        if urls:
            # 处理链接文章
            for url in urls:
                await self._process_article(url, message_info)
        else:
            # 单独记录为备忘录
            await self.storage.save_memo(message_info)
            logger.info("已将消息保存为备忘录")
            
    def _extract_urls(self, text: str) -> list:
        """从文本中提取URL"""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)
        
    async def _process_article(self, url: str, message_info: dict):
        """处理文章链接"""
        try:
            # 解析文章内容
            article_data = await self.article_parser.parse(url)
            if article_data:
                # 保存为笔记
                result = await self.note_service.save_note(
                    title=article_data['title'],
                    content=article_data['content'],
                    url=url,
                    source_message=message_info
                )
                
                if result:
                    logger.info(f"文章已保存为笔记: {article_data['title']}")
                else:
                    logger.error(f"保存笔记失败: {article_data['title']}")
            else:
                logger.warning(f"无法解析文章内容: {url}")
        except Exception as e:
            logger.error(f"处理文章时出错 {url}: {e}")