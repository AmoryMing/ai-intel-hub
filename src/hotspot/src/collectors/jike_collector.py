"""
即刻（Jike）数据收集器
使用 RSSHub 收集AI相关动态
"""

import feedparser
from datetime import datetime, timedelta
from typing import List, Dict
from loguru import logger
import time
import re


class JikeCollector:
    """即刻热点收集器"""

    def __init__(self, config: dict):
        """
        初始化即刻收集器

        Args:
            config: 即刻配置字典
        """
        self.config = config
        self.rsshub_instance = config.get("rsshub_instance", "https://rsshub.app")
        self.enabled = config.get("enabled", True)
        logger.info(f"即刻收集器初始化（RSSHub: {self.rsshub_instance}）")

    def collect(self, lookback_hours: int = 24) -> List[Dict]:
        """
        收集即刻动态

        Args:
            lookback_hours: 回溯时间（小时）

        Returns:
            动态列表
        """
        if not self.enabled:
            logger.info("即刻收集器已禁用")
            return []

        all_items = []
        cutoff_time = datetime.now() - timedelta(hours=lookback_hours)

        # AI相关圈子和用户
        targets = self.config.get("topics", []) + [{"type": "user", "id": uid} for uid in self.config.get("users", [])]

        for target in targets:
            try:
                if target["type"] == "topic":
                    items = self._collect_topic(target["id"], target.get("name", "未知圈子"), cutoff_time)
                else:
                    items = self._collect_user(target["id"], cutoff_time)

                all_items.extend(items)
                logger.info(f"从 {target.get('name', target['id'])} 收集到 {len(items)} 条动态")

                # 避免请求过快
                time.sleep(2)

            except Exception as e:
                logger.error(f"收集失败 {target.get('name', target['id'])}: {e}")
                continue

        logger.info(f"即刻总共收集到 {len(all_items)} 条动态")
        return all_items

    def _collect_topic(self, topic_id: str, topic_name: str, cutoff_time: datetime) -> List[Dict]:
        """收集圈子动态"""
        items = []

        try:
            rss_url = f"{self.rsshub_instance}/jike/topic/{topic_id}"
            logger.debug(f"RSS URL: {rss_url}")

            feed = feedparser.parse(rss_url)

            for entry in feed.entries:
                try:
                    # 解析发布时间
                    published = datetime.fromtimestamp(time.mktime(entry.published_parsed))

                    if published < cutoff_time:
                        continue

                    # 提取互动数据（从描述中）
                    likes = self._extract_number(entry.description, r'(\d+)\s*点赞')
                    comments = self._extract_number(entry.description, r'(\d+)\s*评论')

                    item = {
                        "id": entry.link.split("/")[-1] if "/" in entry.link else entry.link,
                        "title": entry.title,
                        "content": self._clean_html(entry.get("summary", "")),
                        "url": entry.link,
                        "created_at": published,
                        "source": "jike",
                        "platform": "即刻",
                        "topic": topic_name,
                        # 互动指标
                        "engagement": {
                            "likes": likes,
                            "comments": comments,
                            "shares": 0
                        },
                        "likes": likes,
                        "comments": comments,
                        # 用于分析
                        "raw_text": f"{entry.title} {self._clean_html(entry.get('summary', ''))}",
                    }

                    items.append(item)

                except Exception as e:
                    logger.debug(f"解析动态失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"RSS 获取失败 {topic_name}: {e}")

        return items

    def _collect_user(self, user_id: str, cutoff_time: datetime) -> List[Dict]:
        """收集用户动态"""
        items = []

        try:
            rss_url = f"{self.rsshub_instance}/jike/user/{user_id}"
            feed = feedparser.parse(rss_url)

            for entry in feed.entries:
                try:
                    published = datetime.fromtimestamp(time.mktime(entry.published_parsed))

                    if published < cutoff_time:
                        continue

                    likes = self._extract_number(entry.description, r'(\d+)\s*点赞')
                    comments = self._extract_number(entry.description, r'(\d+)\s*评论')

                    item = {
                        "id": entry.link.split("/")[-1],
                        "title": entry.title,
                        "content": self._clean_html(entry.get("summary", "")),
                        "url": entry.link,
                        "created_at": published,
                        "source": "jike",
                        "platform": "即刻",
                        "engagement": {
                            "likes": likes,
                            "comments": comments,
                        },
                        "likes": likes,
                        "comments": comments,
                        "raw_text": f"{entry.title} {self._clean_html(entry.get('summary', ''))}",
                    }

                    items.append(item)

                except Exception as e:
                    logger.debug(f"解析动态失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"RSS 获取失败用户 {user_id}: {e}")

        return items

    def _extract_number(self, text: str, pattern: str) -> int:
        """从文本中提取数字"""
        try:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        except:
            pass
        return 0

    def _clean_html(self, html: str) -> str:
        """清理HTML标签"""
        import re
        clean = re.sub(r'<[^>]+>', '', html)
        return clean.strip()


def test_collector():
    """测试收集器"""
    config = {
        "enabled": True,
        "rsshub_instance": "https://rsshub.app",
        "topics": [
            {"type": "topic", "id": "553870e8e4b0cd23ec0f09ad", "name": "人工智能"},
            {"type": "topic", "id": "54dffb40e4b0a09aad0a468b", "name": "科技"},
        ],
        "users": []
    }

    collector = JikeCollector(config)
    items = collector.collect(lookback_hours=48)

    print(f"\n收集到 {len(items)} 条即刻动态:")
    for item in items[:5]:
        print(f"\n标题: {item['title']}")
        print(f"来源: {item.get('topic', '用户动态')}")
        print(f"点赞: {item['likes']} | 评论: {item['comments']}")
        print(f"链接: {item['url']}")


if __name__ == "__main__":
    test_collector()
