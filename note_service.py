import aiohttp
import json
from astrbot.api import logger

class NoteService:
    def __init__(self, api_url: str = None, api_token: str = None):
        """
        初始化笔记服务
        :param api_url: 第三方笔记API地址
        :param api_token: API认证令牌
        """
        # 这里可以配置你的笔记服务API地址和认证信息
        self.api_url = api_url or "https://api.example.com/notes"  # 替换为实际API地址
        self.api_token = api_token or "your_api_token"  # 替换为实际token
        self.session = None
        
    async def initialize(self):
        """初始化HTTP会话"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
    async def close(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            
    async def save_note(self, title: str, content: str, url: str, source_message: dict = None) -> bool:
        """
        保存笔记到第三方服务
        :param title: 笔记标题
        :param content: 笔记内容
        :param url: 原文链接
        :param source_message: 源消息信息
        :return: 是否保存成功
        """
        if not self.session:
            await self.initialize()
            
        try:
            # 构造笔记数据
            note_data = {
                "title": title,
                "content": content,
                "source_url": url,
                "tags": ["wechat", "article"],
                "metadata": {
                    "source": "wechat_helper",
                    "original_sender": source_message.get('sender_name') if source_message else None,
                    "timestamp": source_message.get('timestamp') if source_message else None
                }
            }
            
            # 发送请求到笔记服务
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_token}"  # 根据实际API要求调整认证方式
            }
            
            async with self.session.post(
                self.api_url,
                json=note_data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status in [200, 201]:
                    logger.info(f"笔记保存成功: {title}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"笔记保存失败，状态码: {response.status}, 错误: {error_text}")
                    return False
                    
        except asyncio.TimeoutError:
            logger.error("保存笔记请求超时")
            return False
        except Exception as e:
            logger.error(f"保存笔记时出错: {e}")
            return False