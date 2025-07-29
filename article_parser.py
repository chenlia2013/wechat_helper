import aiohttp
import asyncio
from astrbot.api import logger
from bs4 import BeautifulSoup

class ArticleParser:
    def __init__(self):
        self.session = None
        
    async def initialize(self):
        """初始化HTTP会话"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
    async def close(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            
    async def parse(self, url: str) -> dict:
        """解析文章内容"""
        if not self.session:
            await self.initialize()
            
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    content = await response.text()
                    return self._extract_content(content, url)
                else:
                    logger.warning(f"获取网页失败，状态码: {response.status}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"获取网页超时: {url}")
            return None
        except Exception as e:
            logger.error(f"解析文章失败 {url}: {e}")
            return None
            
    def _extract_content(self, html_content: str, url: str) -> dict:
        """从HTML中提取文章内容"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
                
            # 尝试提取标题
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
                
            # 尝试提取文章正文
            content = ""
            # 常见的文章内容选择器
            content_selectors = [
                'article', 
                '.content', 
                '.article-content',
                '.post-content',
                '.entry-content',
                'main',
                '.main-content'
            ]
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    content = content_element.get_text(strip=False).strip()
                    break
                    
            # 如果没找到特定内容区域，则使用body
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text(strip=False).strip()
                    
            # 清理内容
            content = self._clean_content(content)
            
            return {
                'title': title or "未命名文章",
                'content': content[:5000],  # 限制内容长度
                'url': url
            }
        except Exception as e:
            logger.error(f"提取文章内容失败: {e}")
            return None
            
    def _clean_content(self, content: str) -> str:
        """清理文章内容"""
        if not content:
            return ""
            
        # 移除多余的空白行
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        return '\n'.join(lines)