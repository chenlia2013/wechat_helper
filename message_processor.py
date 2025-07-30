import re
import aiohttp
from astrbot.api import logger
from urllib.parse import urlparse
from .joplin_service import JoplinService

class MessageProcessor:
    def __init__(self):
        self.joplin_service = None
        
    async def initialize(self):
        """初始化消息处理器"""
        self.joplin_service = JoplinService()
        await self.joplin_service.initialize()
        logger.info("消息处理器初始化完成")
        
    async def close(self):
        """关闭处理器"""
        if self.joplin_service:
            await self.joplin_service.close()
            
    async def process_message(self, event):
        """处理管理员消息"""
        message_str = event.message_str
        
        # 检查是否包含链接
        urls = self._extract_urls(message_str)
        if urls:
            # 处理包含链接的消息
            for url in urls:
                await self._process_url_message(message_str, url)
        else:
            # 处理纯文本消息
            await self._process_text_message(message_str)
            
    def _extract_urls(self, text: str) -> list:
        """从文本中提取URL"""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)
        
    async def _process_text_message(self, text: str):
        """处理纯文本消息"""
        try:
            # 对文本进行整理（这里可以接入AI进行处理）
            processed_text = await self._organize_text_with_ai(text)
            
            # 保存到Joplin笔记
            note_title = self._generate_title_from_text(processed_text)
            await self.joplin_service.create_note(
                title=note_title,
                content=processed_text,
                tags=["wechat", "memo"]
            )
            
            logger.info(f"已将文本消息保存为笔记: {note_title}")
        except Exception as e:
            logger.error(f"处理文本消息时出错: {e}")
            
    async def _process_url_message(self, message: str, url: str):
        """处理包含链接的消息"""
        try:
            # 判断是否为内网链接
            if self._is_internal_url(url):
                # 内网链接直接保存
                content = f"内网链接消息:\n\n{message}\n\n链接: {url}"
                title = self._generate_title_from_text(message)
            else:
                # 互联网链接需要获取内容
                content = await self._fetch_and_process_url_content(message, url)
                title = self._generate_title_from_url_content(content, url)
                
            # 保存到Joplin笔记
            await self.joplin_service.create_note(
                title=title,
                content=content,
                tags=["wechat", "link"],
                source_url=url
            )
            
            logger.info(f"已将链接消息保存为笔记: {title}")
        except Exception as e:
            logger.error(f"处理链接消息时出错: {e}")
            
    def _is_internal_url(self, url: str) -> bool:
        """判断是否为内网链接"""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            
            # 检查是否为内网IP地址
            if hostname:
                # 本地地址
                if hostname == 'localhost':
                    return True
                    
                # 检查是否为内网IP
                if hostname.startswith('192.168.') or \
                   hostname.startswith('10.') or \
                   hostname.startswith('172.'):
                    return True
                    
                # 检查是否为本地网络地址
                if hostname.endswith('.local') or hostname.endswith('.lan'):
                    return True
                    
            return False
        except Exception:
            # 出错时默认当作外网处理
            return False
            
    async def _fetch_and_process_url_content(self, message: str, url: str) -> str:
        """获取并处理URL内容"""
        try:
            # 这里可以使用AI来处理内容，目前先简单实现
            content = f"消息内容:\n{message}\n\n原链接: {url}\n\n"
            
            # 获取网页内容
            page_content = await self._fetch_webpage_content(url)
            if page_content:
                content += f"\n--- 网页内容 ---\n{page_content}"
            else:
                content += "\n--- 无法获取网页内容 ---"
                
            return content
        except Exception as e:
            logger.error(f"获取URL内容时出错: {e}")
            return f"消息内容:\n{message}\n\n原链接: {url}\n\n--- 获取内容失败 ---"
            
    async def _fetch_webpage_content(self, url: str) -> str:
        """获取网页内容"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        # 读取内容并简单处理
                        content = await response.text()
                        # 这里可以使用BeautifulSoup等库解析内容，为了减少依赖，暂时只做简单处理
                        return self._simple_extract_text(content)
                    else:
                        logger.warning(f"获取网页失败，状态码: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"获取网页内容时出错: {e}")
            return None
            
    def _simple_extract_text(self, html_content: str) -> str:
        """简单提取HTML文本内容"""
        try:
            # 简单移除HTML标签
            import re
            # 移除script和style标签内容
            html_content = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            # 移除HTML注释
            html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
            # 移除所有HTML标签
            text = re.sub(r'<[^>]+>', '', html_content)
            # 清理多余空白字符
            text = re.sub(r'\s+', ' ', text).strip()
            # 限制长度
            return text[:2000] if text else None
        except Exception as e:
            logger.error(f"提取文本内容时出错: {e}")
            return None
            
    def _generate_title_from_text(self, text: str) -> str:
        """根据文本生成标题"""
        # 简单地从文本中提取前50个字符作为标题
        lines = text.strip().split('\n')
        first_line = lines[0].strip() if lines else "微信笔记"
        return first_line[:50] + ("..." if len(first_line) > 50 else "")
        
    def _generate_title_from_url_content(self, content: str, url: str) -> str:
        """根据URL内容生成标题"""
        # 尝试从内容中提取标题
        lines = content.strip().split('\n')
        for line in lines[:3]:  # 检查前3行
            if line.strip():
                title = line.strip()[:50] + ("..." if len(line.strip()) > 50 else "")
                return title
                
        # 如果没有合适的标题，使用URL域名
        try:
            parsed = urlparse(url)
            return f"来自 {parsed.netloc} 的内容"
        except Exception:
            return "链接内容"
            
    async def _organize_text_with_ai(self, text: str) -> str:
        """使用AI整理文本（目前为简单实现，后续可接入AI服务）"""
        # 这里可以接入AI服务来整理文本
        # 暂时只做简单的文本格式化
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines) if lines else text