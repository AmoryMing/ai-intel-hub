"""
YouTube 数据收集器
收集指定频道的最新 AI 相关视频
"""

from googleapiclient.discovery import build
from datetime import datetime, timedelta
from typing import List, Dict
from loguru import logger
import os
from dotenv import load_dotenv

load_dotenv()


class YouTubeCollector:
    """YouTube 热点收集器"""

    def __init__(self, config: dict):
        """
        初始化 YouTube 收集器

        Args:
            config: YouTube 配置字典
        """
        self.config = config
        self.youtube = self._init_youtube()

    def _init_youtube(self):
        """初始化 YouTube API 客户端"""
        try:
            api_key = os.getenv("YOUTUBE_API_KEY")
            if not api_key:
                logger.warning("YouTube API 密钥未设置，使用 RSS fallback")
                return None

            youtube = build("youtube", "v3", developerKey=api_key)
            logger.info("YouTube API 初始化成功")
            return youtube

        except Exception as e:
            logger.error(f"YouTube API 初始化失败: {e}")
            return None

    def collect(self, lookback_hours: int = 24) -> List[Dict]:
        """
        收集最新AI视频（优先使用RSS，更稳定）

        Args:
            lookback_hours: 回溯时间（小时）

        Returns:
            视频列表
        """
        if not self.youtube:
            logger.info("使用 RSS 方式收集 YouTube 数据")
            return self._collect_via_rss(lookback_hours)

        all_videos = []
        cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)

        for channel_id in self.config.get("channels", []):
            try:
                logger.info(f"正在收集频道 {channel_id}...")
                videos = self._collect_from_channel(channel_id, cutoff_time)
                all_videos.extend(videos)
                logger.info(f"从频道 {channel_id} 收集到 {len(videos)} 个视频")

            except Exception as e:
                logger.error(f"收集频道 {channel_id} 失败: {e}")
                continue

        logger.info(f"YouTube 总共收集到 {len(all_videos)} 个视频")
        return all_videos

    def _collect_from_channel(
        self, channel_id: str, cutoff_time: datetime
    ) -> List[Dict]:
        """从单个频道收集视频"""
        videos = []
        min_views = self.config.get("min_views", 1000)

        try:
            # 获取频道最新上传的视频
            request = self.youtube.search().list(
                part="id,snippet",
                channelId=channel_id,
                maxResults=50,
                order="date",
                type="video",
                publishedAfter=cutoff_time.isoformat() + "Z",
            )

            response = request.execute()

            for item in response.get("items", []):
                video_id = item["id"]["videoId"]

                # 获取视频详细信息（包括观看数）
                video_details = self._get_video_details(video_id)

                if video_details and video_details["views"] >= min_views:
                    videos.append(video_details)

        except Exception as e:
            logger.error(f"收集频道视频失败: {e}")

        return videos

    def _get_video_details(self, video_id: str) -> Dict:
        """获取视频详细信息"""
        try:
            request = self.youtube.videos().list(
                part="snippet,statistics,contentDetails", id=video_id
            )

            response = request.execute()

            if not response.get("items"):
                return None

            item = response["items"][0]
            snippet = item["snippet"]
            statistics = item["statistics"]

            return {
                "id": video_id,
                "title": snippet["title"],
                "channel_title": snippet["channelTitle"],
                "channel_id": snippet["channelId"],
                "description": snippet["description"],
                "published_at": datetime.fromisoformat(
                    snippet["publishedAt"].replace("Z", "+00:00")
                ),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "thumbnail": snippet["thumbnails"]["high"]["url"],
                "source": "youtube",
                # 互动指标
                "engagement": {
                    "views": int(statistics.get("viewCount", 0)),
                    "likes": int(statistics.get("likeCount", 0)),
                    "comments": int(statistics.get("commentCount", 0)),
                },
                # 便于访问
                "views": int(statistics.get("viewCount", 0)),
                "likes": int(statistics.get("likeCount", 0)),
                "comments": int(statistics.get("commentCount", 0)),
                # 用于后续分析
                "raw_text": f"{snippet['title']} {snippet['description']}",
            }

        except Exception as e:
            logger.error(f"获取视频详情失败 {video_id}: {e}")
            return None

    def _collect_via_rss(self, lookback_hours: int = 24) -> List[Dict]:
        """
        使用 RSS 方式收集（无需 API 密钥）

        YouTube RSS: https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
        """
        import feedparser
        import requests

        all_videos = []
        cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)

        for channel_id in self.config.get("channels", []):
            channel_videos = []
            try:
                rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
                feed = feedparser.parse(rss_url)

                channel_name = feed.feed.get("title", channel_id) if hasattr(feed, "feed") else channel_id

                for entry in feed.entries:
                    published = datetime.fromisoformat(
                        entry.published.replace("Z", "+00:00")
                    )

                    if published < cutoff_time.replace(tzinfo=published.tzinfo):
                        continue

                    video_data = {
                        "id": entry.yt_videoid,
                        "title": entry.title,
                        "channel_title": entry.author,
                        "channel_id": channel_id,
                        "description": entry.summary,
                        "published_at": published,
                        "url": entry.link,
                        "thumbnail": entry.media_thumbnail[0]["url"]
                        if hasattr(entry, "media_thumbnail")
                        else "",
                        "source": "youtube",
                        "engagement": {
                            "views": 0,  # RSS 不提供观看数
                            "likes": 0,
                            "comments": 0,
                        },
                        "views": 0,
                        "raw_text": f"{entry.title} {entry.summary}",
                    }

                    channel_videos.append(video_data)

                all_videos.extend(channel_videos)
                logger.info(f"从频道 {channel_name} 收集到 {len(channel_videos)} 个视频")

            except Exception as e:
                logger.error(f"RSS 收集失败 {channel_id}: {e}")
                continue

        logger.info(f"YouTube RSS 总共收集到 {len(all_videos)} 个视频")
        return all_videos


def test_collector():
    """测试收集器"""
    config = {
        "channels": [
            "UCbfYPyITQ-7l4upoX8nvctg",  # Two Minute Papers
        ],
        "min_views": 1000,
    }

    collector = YouTubeCollector(config)
    videos = collector.collect(lookback_hours=48)

    print(f"\n收集到 {len(videos)} 个视频:")
    for video in videos[:5]:
        print(f"\n标题: {video['title']}")
        print(f"频道: {video['channel_title']}")
        print(f"观看: {video['views']} | 点赞: {video['likes']}")
        print(f"链接: {video['url']}")


if __name__ == "__main__":
    test_collector()
