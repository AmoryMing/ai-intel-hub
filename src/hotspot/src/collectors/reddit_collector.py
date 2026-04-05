"""
Reddit 数据收集器
使用 RSS 方式收集（无需 API）
"""

import feedparser
from datetime import datetime, timedelta
from typing import List, Dict
from loguru import logger
import time


class RedditCollector:
    """Reddit 热点收集器（RSS方式）"""

    def __init__(self, config: dict):
        """
        初始化 Reddit 收集器

        Args:
            config: Reddit 配置字典
        """
        self.config = config
        self.use_rss = config.get("use_rss", True)
        logger.info("Reddit 收集器初始化（RSS 模式）")

    def collect(self, lookback_hours: int = 24) -> List[Dict]:
        """
        收集热门帖子

        Args:
            lookback_hours: 回溯时间（小时）

        Returns:
            帖子列表
        """
        all_posts = []
        cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)

        for subreddit_name in self.config.get("subreddits", []):
            try:
                logger.info(f"正在收集 r/{subreddit_name} (RSS)...")

                # 使用 RSS
                posts = self._collect_via_rss(subreddit_name, cutoff_time)

                all_posts.extend(posts)
                logger.info(f"从 r/{subreddit_name} 收集到 {len(posts)} 个帖子")

                # 避免请求过快
                time.sleep(1)

            except Exception as e:
                logger.error(f"收集 r/{subreddit_name} 失败: {e}")
                continue

        logger.info(f"Reddit 总共收集到 {len(all_posts)} 个帖子")
        return all_posts

    def _collect_via_rss(self, subreddit: str, cutoff_time: datetime) -> List[Dict]:
        """使用 RSS 收集 subreddit"""
        posts = []
        min_score = self.config.get("min_score", 50)

        try:
            # Reddit RSS URL
            rss_url = f"https://www.reddit.com/r/{subreddit}/.rss"

            feed = feedparser.parse(rss_url)

            for entry in feed.entries:
                try:
                    # 解析时间
                    published = datetime.fromtimestamp(
                        time.mktime(entry.published_parsed)
                    )

                    # 检查时间
                    if published < cutoff_time:
                        continue

                    # 从摘要中提取分数（RSS 中包含）
                    # Reddit RSS 格式: "submitted by username to r/subreddit \n[link] [comments]"
                    # 分数信息在 content 中
                    score = 0
                    num_comments = 0

                    # 尝试从 summary 中提取
                    if hasattr(entry, 'summary'):
                        import re
                        score_match = re.search(r'(\d+) points?', entry.summary)
                        comments_match = re.search(r'(\d+) comments?', entry.summary)

                        if score_match:
                            score = int(score_match.group(1))
                        if comments_match:
                            num_comments = int(comments_match.group(1))

                    # 检查分数（注意：RSS 中的分数可能为 0）
                    # 因此我们降低门槛或跳过分数检查
                    # if score < min_score:
                    #     continue

                    # 提取帖子数据
                    post_data = {
                        "id": entry.id.split('/')[-1] if hasattr(entry, 'id') else "",
                        "title": entry.title,
                        "author": entry.author if hasattr(entry, 'author') else "unknown",
                        "subreddit": subreddit,
                        "url": entry.link,
                        "permalink": entry.link,
                        "score": score,
                        "upvote_ratio": 0.9,  # RSS 中没有
                        "num_comments": num_comments,
                        "created_utc": published,
                        "selftext": entry.summary if hasattr(entry, 'summary') else "",
                        "link_flair_text": "",
                        "is_self": True,
                        "source": "reddit",
                        # 互动指标
                        "engagement": {
                            "score": score,
                            "comments": num_comments,
                            "upvote_ratio": 0.9,
                            "awards": 0,
                        },
                        # 用于后续分析
                        "raw_text": f"{entry.title} {entry.summary if hasattr(entry, 'summary') else ''}",
                    }

                    posts.append(post_data)

                except Exception as e:
                    logger.debug(f"解析帖子失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"RSS 收集失败: {e}")

        return posts


def test_collector():
    """测试收集器"""
    config = {
        "use_rss": True,
        "subreddits": ["MachineLearning", "LocalLLaMA"],
        "min_score": 0,  # RSS 模式降低门槛
        "sort_by": "hot",
    }

    collector = RedditCollector(config)
    posts = collector.collect(lookback_hours=48)

    print(f"\n收集到 {len(posts)} 个帖子:")
    for post in posts[:5]:
        print(f"\n标题: {post['title']}")
        print(f"分数: {post['score']} | 评论: {post['num_comments']}")
        print(f"链接: {post['permalink']}")


if __name__ == "__main__":
    test_collector()
