"""
小红书（Xiaohongshu）数据收集器
使用 RSSHub 收集AI相关笔记
"""

import feedparser
from datetime import datetime, timedelta
from typing import List, Dict
from loguru import logger
import time
import re


class XiaohongshuCollector:
    """小红书热点收集器"""

    def __init__(self, config: dict):
        """
        初始化小红书收集器

        Args:
            config: 小红书配置字典
        """
        self.config = config
        self.rsshub_instance = config.get("rsshub_instance", "https://rsshub.app")
        self.enabled = config.get("enabled", True)
        logger.info(f"小红书收集器初始化（RSSHub: {self.rsshub_instance}）")

    def collect(self, lookback_hours: int = 24) -> List[Dict]:
        """
        收集小红书笔记

        Args:
            lookback_hours: 回溯时间（小时）

        Returns:
            笔记列表
        """
        if not self.enabled:
            logger.info("小红书收集器已禁用")
            return []

        all_items = []
        cutoff_time = datetime.now() - timedelta(hours=lookback_hours)

        # 优先使用关键词搜索模式
        if self.config.get("use_keyword_search", False):
            keywords = self.config.get("keywords", [])
            for keyword in keywords:
                try:
                    items = self._collect_by_keyword(keyword, cutoff_time)
                    all_items.extend(items)
                    logger.info(f"关键词 '{keyword}' 收集到 {len(items)} 篇笔记")
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"关键词搜索失败 '{keyword}': {e}")
                    continue
        else:
            # 用户模式
            users = self.config.get("users", []) or []
            for user in users:
                try:
                    user_id = user["id"]
                    user_name = user.get("name", "未知用户")
                    category = user.get("category", "notes")  # notes 或 collect

                    items = self._collect_user(user_id, user_name, category, cutoff_time)
                    all_items.extend(items)

                    logger.info(f"从 {user_name} 收集到 {len(items)} 篇笔记")
                    time.sleep(2)

                except Exception as e:
                    logger.error(f"收集失败 {user.get('name', user['id'])}: {e}")
                    continue

        logger.info(f"小红书总共收集到 {len(all_items)} 篇笔记")
        return all_items

    def _collect_by_keyword(self, keyword: str, cutoff_time: datetime) -> List[Dict]:
        """通过关键词搜索收集笔记"""
        items = []

        try:
            # RSSHub 小红书搜索路由: /xiaohongshu/search/note/:keyword
            import urllib.parse
            encoded_keyword = urllib.parse.quote(keyword)
            rss_url = f"{self.rsshub_instance}/xiaohongshu/search/note/{encoded_keyword}"
            logger.debug(f"RSS URL: {rss_url}")

            feed = feedparser.parse(rss_url)

            for entry in feed.entries:
                try:
                    # 解析发布时间
                    published = datetime.fromtimestamp(time.mktime(entry.published_parsed))

                    if published < cutoff_time:
                        continue

                    # 从描述中提取互动数据
                    description = entry.get("description", "")
                    likes = self._extract_number(description, r'(\d+)\s*赞')
                    comments = self._extract_number(description, r'(\d+)\s*评论')
                    collects = self._extract_number(description, r'(\d+)\s*收藏')

                    # 最低点赞过滤
                    min_likes = self.config.get("min_likes", 100)
                    if likes < min_likes:
                        continue

                    # 提取图片
                    images = self._extract_images(entry)

                    item = {
                        "id": entry.link.split("/")[-1] if "/" in entry.link else entry.link,
                        "title": entry.title,
                        "content": self._clean_html(entry.get("summary", "")),
                        "url": entry.link,
                        "created_at": published,
                        "source": "xiaohongshu",
                        "platform": "小红书",
                        "keyword": keyword,
                        # 互动指标
                        "engagement": {
                            "likes": likes,
                            "comments": comments,
                            "collects": collects,
                        },
                        "likes": likes,
                        "comments": comments,
                        "collects": collects,
                        # 图片
                        "images": images,
                        "has_images": len(images) > 0,
                        # 用于分析
                        "raw_text": f"{entry.title} {self._clean_html(entry.get('summary', ''))}",
                    }

                    items.append(item)

                except Exception as e:
                    logger.debug(f"解析笔记失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"RSS 获取失败 '{keyword}': {e}")

        return items

    def _collect_user(self, user_id: str, user_name: str, category: str, cutoff_time: datetime) -> List[Dict]:
        """收集用户笔记"""
        items = []

        try:
            # RSSHub 小红书路由: /xiaohongshu/user/:user_id/:category
            rss_url = f"{self.rsshub_instance}/xiaohongshu/user/{user_id}/{category}"
            logger.debug(f"RSS URL: {rss_url}")

            feed = feedparser.parse(rss_url)

            for entry in feed.entries:
                try:
                    # 解析发布时间
                    published = datetime.fromtimestamp(time.mktime(entry.published_parsed))

                    if published < cutoff_time:
                        continue

                    # 从描述中提取互动数据
                    description = entry.get("description", "")
                    likes = self._extract_number(description, r'(\d+)\s*赞')
                    comments = self._extract_number(description, r'(\d+)\s*评论')
                    collects = self._extract_number(description, r'(\d+)\s*收藏')

                    # 提取图片
                    images = self._extract_images(entry)

                    item = {
                        "id": entry.link.split("/")[-1] if "/" in entry.link else entry.link,
                        "title": entry.title,
                        "content": self._clean_html(entry.get("summary", "")),
                        "url": entry.link,
                        "created_at": published,
                        "source": "xiaohongshu",
                        "platform": "小红书",
                        "author": user_name,
                        # 互动指标
                        "engagement": {
                            "likes": likes,
                            "comments": comments,
                            "collects": collects,
                        },
                        "likes": likes,
                        "comments": comments,
                        "collects": collects,
                        # 图片
                        "images": images,
                        "has_images": len(images) > 0,
                        # 用于分析
                        "raw_text": f"{entry.title} {self._clean_html(entry.get('summary', ''))}",
                    }

                    items.append(item)

                except Exception as e:
                    logger.debug(f"解析笔记失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"RSS 获取失败 {user_name}: {e}")

        return items

    def _extract_number(self, text: str, pattern: str) -> int:
        """从文本中提取数字"""
        try:
            match = re.search(pattern, text)
            if match:
                num_str = match.group(1).replace(',', '')
                # 处理 1.2k, 3.5w 等格式
                if 'k' in text.lower():
                    return int(float(num_str) * 1000)
                elif 'w' in text or '万' in text:
                    return int(float(num_str) * 10000)
                return int(num_str)
        except:
            pass
        return 0

    def _extract_images(self, entry) -> List[str]:
        """提取图片URL"""
        images = []
        try:
            # 从 media_content 或 description 中提取图片
            if hasattr(entry, 'media_content'):
                for media in entry.media_content:
                    if 'url' in media:
                        images.append(media['url'])

            # 从 description HTML 中提取
            description = entry.get("description", "")
            img_urls = re.findall(r'<img[^>]+src="([^"]+)"', description)
            images.extend(img_urls)

        except:
            pass

        return images[:4]  # 最多4张图

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
        "users": [
            # AI相关博主（示例ID，实际使用需要真实用户ID）
            {"id": "5b932890f7e8b90001a5e4a9", "name": "AI科技评论", "category": "notes"},
        ]
    }

    collector = XiaohongshuCollector(config)
    items = collector.collect(lookback_hours=72)

    print(f"\n收集到 {len(items)} 篇小红书笔记:")
    for item in items[:5]:
        print(f"\n标题: {item['title']}")
        print(f"作者: {item['author']}")
        print(f"点赞: {item['likes']} | 评论: {item['comments']} | 收藏: {item['collects']}")
        print(f"图片: {len(item['images'])} 张")
        print(f"链接: {item['url']}")


if __name__ == "__main__":
    test_collector()
