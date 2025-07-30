import aiohttp
import json
import time
from astrbot.api import logger

class JoplinService:
    def __init__(self, base_url: str = None, token: str = None):
        """
        初始化Joplin服务
        :param base_url: Joplin API基础URL，例如: http://localhost:41184
        :param token: Joplin API令牌
        """
        # 可以从配置文件或环境变量中读取
        self.base_url = base_url or "http://localhost:41184"
        self.token = token or "your_joplin_api_token"  # 请替换为实际的token
        self.session = None
        
    async def initialize(self):
        """初始化HTTP会话"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
    async def close(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            
    async def create_note(self, title: str, content: str, tags: list = None, source_url: str = None) -> str:
        """
        创建笔记
        :param title: 笔记标题
        :param content: 笔记内容
        :param tags: 标签列表
        :param source_url: 源URL
        :return: 笔记ID
        """
        try:
            # 构造笔记数据
            note_data = {
                "title": title,
                "body": content,
                "created_time": int(time.time() * 1000),  # 毫秒
                "updated_time": int(time.time() * 1000),  # 毫秒
            }
            
            # 添加源URL（如果提供）
            if source_url:
                note_data["source_url"] = source_url
                
            # 创建笔记
            note_id = await self._create_resource("notes", note_data)
            
            # 添加标签（如果提供）
            if tags and note_id:
                await self._add_tags_to_note(note_id, tags)
                
            logger.info(f"笔记创建成功: {title}")
            return note_id
            
        except Exception as e:
            logger.error(f"创建笔记失败: {e}")
            return None
            
    async def _create_resource(self, resource_type: str, data: dict):
        """创建资源"""
        try:
            url = f"{self.base_url}/{resource_type}?token={self.token}"
            
            async with self.session.post(
                url,
                json=data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    return result.get("id")
                else:
                    error_text = await response.text()
                    logger.error(f"创建资源失败，状态码: {response.status}, 错误: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"创建资源时出错: {e}")
            return None
            
    async def _add_tags_to_note(self, note_id: str, tags: list):
        """为笔记添加标签"""
        try:
            for tag_name in tags:
                # 先查找标签是否存在
                tag_id = await self._find_or_create_tag(tag_name)
                if tag_id:
                    # 将标签关联到笔记
                    await self._link_tag_to_note(note_id, tag_id)
                    
        except Exception as e:
            logger.error(f"添加标签时出错: {e}")
            
    async def _find_or_create_tag(self, tag_name: str) -> str:
        """查找或创建标签"""
        try:
            # 查找标签
            url = f"{self.base_url}/search?query={tag_name}&type=tag&token={self.token}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    tags = result.get("items", [])
                    # 检查是否有完全匹配的标签
                    for tag in tags:
                        if tag.get("title", "").lower() == tag_name.lower():
                            return tag.get("id")
                            
                # 标签不存在，创建新标签
                return await self._create_resource("tags", {"title": tag_name})
                
        except Exception as e:
            logger.error(f"查找或创建标签时出错: {e}")
            return None
            
    async def _link_tag_to_note(self, note_id: str, tag_id: str):
        """将标签关联到笔记"""
        try:
            url = f"{self.base_url}/tags/{tag_id}/notes?token={self.token}"
            
            async with self.session.post(
                url,
                json={"id": note_id},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status not in [200, 201, 204]:
                    error_text = await response.text()
                    logger.error(f"关联标签到笔记失败，状态码: {response.status}, 错误: {error_text}")
                    
        except Exception as e:
            logger.error(f"关联标签到笔记时出错: {e}")
            
    async def get_note(self, note_id: str) -> dict:
        """获取笔记详情"""
        try:
            url = f"{self.base_url}/notes/{note_id}?token={self.token}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"获取笔记失败，状态码: {response.status}, 错误: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取笔记时出错: {e}")
            return None
            
    async def update_note(self, note_id: str, data: dict) -> bool:
        """更新笔记"""
        try:
            url = f"{self.base_url}/notes/{note_id}?token={self.token}"
            
            async with self.session.put(
                url,
                json=data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status in [200, 201, 204]:
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"更新笔记失败，状态码: {response.status}, 错误: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"更新笔记时出错: {e}")
            return False