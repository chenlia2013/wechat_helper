from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from .message_handler import MessageHandler

@register("wechat_helper", "YourName", "微信个人助手插件", "1.0.0")
class WechatHelperPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.message_handler = None

    async def initialize(self):
        """初始化插件"""
        try:
            self.message_handler = MessageHandler()
            await self.message_handler.initialize()
            logger.info("微信个人助手插件初始化成功")
        except Exception as e:
            logger.error(f"微信个人助手插件初始化失败: {e}")

    async def terminate(self):
        """插件销毁方法"""
        if self.message_handler:
            await self.message_handler.close()
        logger.info("微信个人助手插件已停止")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_all_message(self, event: AstrMessageEvent):
        """处理所有消息"""
        try:
            # 异步处理消息
            await self.message_handler.process_message(event)
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
        
        # 不中断消息传递
        # return MessageEventResult.EMPTY