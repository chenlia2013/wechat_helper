from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from .message_processor import MessageProcessor

@register("wechat_helper", "YourName", "微信个人助手插件", "1.0.0")
class WechatHelperPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.message_processor = None

    async def initialize(self):
        """初始化插件"""
        try:
            self.message_processor = MessageProcessor()
            await self.message_processor.initialize()
            logger.info("微信个人助手插件初始化成功")
        except Exception as e:
            logger.error(f"微信个人助手插件初始化失败: {e}")

    async def terminate(self):
        """插件销毁方法"""
        if self.message_processor:
            await self.message_processor.close()
        logger.info("微信个人助手插件已停止")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_all_message(self, event: AstrMessageEvent):
        """处理管理员发送的消息"""
        # 只处理管理员发送的消息
        if not event.is_admin():
            return None
            
        # 处理管理员消息
        try:
            await self.message_processor.process_message(event)
        except Exception as e:
            logger.error(f"处理管理员消息时出错: {e}")
            
        return None