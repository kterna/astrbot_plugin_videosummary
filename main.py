from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig
import requests
import re

@register("videosummary", "AstrBot", "视频内容智能总结插件", "1.2.0", "")
class VideoSummaryPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.api_url = config.get("api_url", "")
        self.proxy_url = config.get("proxy_url", "")
    
    @filter.command("videosummary", alias=['总结视频', '视频总结'])
    async def summarize_video(self, event: AstrMessageEvent, video_url: str = None):
        '''总结视频内容 (支持各大视频平台)'''
        # 使用完整的消息文本来提取URL
        message_text = event.message_str
        if not message_text:
            yield event.plain_result("请提供视频链接")
            return
        
        # 提取并清理URL
        url = self._extract_url(message_text)
        if not url:
            yield event.plain_result("请提供有效的视频链接")
            return
        
        # 检查API URL是否已配置
        if not self.api_url:
            yield event.plain_result("请先在管理面板中配置视频总结API地址")
            return
        
        try:
            # 发送请求获取视频摘要
            yield event.plain_result(f"正在获取视频内容摘要，请稍候...")
            summary_data = self._get_video_summary(url)
            
            if not summary_data or not summary_data.get('success'):
                yield event.plain_result("获取视频摘要失败，请检查视频链接是否有效或稍后再试")
                return
            
            # 构建回复消息
            result = self._format_summary(summary_data)
            yield event.plain_result(result)
            
        except Exception as e:
            yield event.plain_result(f"获取视频摘要时发生错误: {str(e)}")
    
    def _extract_url(self, text: str) -> str:
        """从文本中提取并清理URL"""
        # 简单匹配http(s)开头的URL
        url_pattern = r'https?://\S+'
        match = re.search(url_pattern, text)
        if not match:
            return None
        
        # 获取匹配的URL并清理
        url = match.group(0)
        # 移除URL末尾可能的标点符号和其他字符
        url = url.rstrip('.,;!?】】）】 \t\n\r')
        return url
    
    def _get_video_summary(self, video_url: str) -> dict:
        """获取视频摘要"""
        params = {"url": video_url}
        proxies = {'http': self.proxy_url, 'https': self.proxy_url} if self.proxy_url else None
        
        try:
            response = requests.get(
                self.api_url, 
                params=params, 
                proxies=proxies,
                timeout=30  # 添加超时设置
            )
            response.raise_for_status()  # 检查响应状态
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"请求API失败: {str(e)}")
    
    def _format_summary(self, data: dict) -> str:
        """格式化摘要信息"""
        result = f"# 视频《{data.get('id', '未知视频')}》内容总结\n\n"
        
        # 添加摘要
        summary = data.get('summary', '')
        if summary:
            result += f"## 内容摘要\n{summary}\n\n"
        
        # 添加源视频链接
        source_url = data.get('sourceUrl', '') or data.get('url', '')
        if source_url:
            result += f"## 源视频\n[点击查看原视频]({source_url})\n\n"
        
        # 添加时间戳
        timestamps = data.get('timestamps', [])
        if timestamps:
            result += "## 关键时间点\n"
            for ts in timestamps:
                result += f"- [{ts['time']}] {ts['content']}\n"
            result += "\n"
        
        return result
