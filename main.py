from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig
import requests
import re

@register("videosummary", "AstrBot", "视频内容智能总结插件", "1.1.0", "")
class VideoSummaryPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.api_url = config.get("api_url", "")
        self.proxy_url = config.get("proxy_url", "")
        
        # 通用的URL识别正则表达式
        self.url_pattern = r'https?://[^\s<>"]+'
    
    @filter.command("videosummary", alias=['总结视频', '视频总结'])
    async def summarize_video(self, event: AstrMessageEvent, video_url: str = None):
        '''总结视频内容 (支持各大视频平台)'''
        if not video_url:
            yield event.plain_result("请提供视频链接")
            return
        
        # 检查是否是有效的URL
        if not self._is_valid_url(video_url):
            yield event.plain_result("请提供有效的视频链接")
            return
        
        # 检查API URL是否已配置
        if not self.api_url:
            yield event.plain_result("请先在管理面板中配置视频总结API地址")
            return
        
        try:
            # 发送请求获取视频摘要
            yield event.plain_result(f"正在获取视频内容摘要，请稍候...")
            summary_data = self._get_video_summary(video_url)
            
            if not summary_data or not summary_data.get('success'):
                yield event.plain_result("获取视频摘要失败，请检查视频链接是否有效或稍后再试")
                return
            
            # 构建回复消息
            result = self._format_summary(summary_data)
            yield event.plain_result(result)
            
        except Exception as e:
            yield event.plain_result(f"获取视频摘要时发生错误: {str(e)}")
    
    def _is_valid_url(self, url: str) -> bool:
        """检查是否是有效的URL"""
        return bool(re.match(self.url_pattern, url))
    
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
        
        # 添加亮点
        highlights = self._extract_highlights(summary)
        if highlights:
            result += "## 视频亮点\n"
            for highlight in highlights:
                result += f"- {highlight}\n"
            result += "\n"
        
        # 添加思考
        thoughts = self._extract_thoughts(summary)
        if thoughts:
            result += "## 思考与问题\n"
            for thought in thoughts:
                result += f"- {thought}\n"
            result += "\n"
        
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
    
    def _extract_highlights(self, summary: str) -> list:
        """从摘要中提取亮点"""
        highlights = []
        if not summary:
            return highlights
        
        # 查找亮点部分
        highlight_section = re.search(r'## 亮点\n([\s\S]*?)(?:\n##|$)', summary)
        if highlight_section:
            highlight_text = highlight_section.group(1).strip()
            # 提取每个亮点（以 - 开头的行）
            highlight_items = re.findall(r'- (.+?)(?:\n|$)', highlight_text)
            highlights.extend(highlight_items)
        
        return highlights
    
    def _extract_thoughts(self, summary: str) -> list:
        """从摘要中提取思考"""
        thoughts = []
        if not summary:
            return thoughts
        
        # 查找思考部分
        thought_section = re.search(r'## 思考\n([\s\S]*?)(?:\n##|$)', summary)
        if thought_section:
            thought_text = thought_section.group(1).strip()
            # 提取每个思考（以 - 开头的行）
            thought_items = re.findall(r'- (.+?)(?:\n|$)', thought_text)
            thoughts.extend(thought_items)
        
        return thoughts
