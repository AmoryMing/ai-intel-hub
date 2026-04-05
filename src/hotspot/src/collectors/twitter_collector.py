"""
X (Twitter) 数据收集器
使用 Nitter 或 RSSHub 收集推文（无需官方 API）
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict
from loguru import logger
import time


class TwitterCollector:
    """X (Twitter) 热点收集器"""

    def __init__(self, config: dict):
        """
        初始化 Twitter 收集器

        Args:
            config: Twitter 配置字典
        """
        self.config = config
        self.use_nitter = config.get("use_nitter", True)
        self.nitter_instance = "nitter.net"  # 可选实例: nitter.nl, nitter.poast.org
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; AI-Hotspot-Collector/1.0)"}
        )

    def collect(self, lookback_hours: int = 24) -> List[Dict]:
        """
        收集推文

        Args:
            lookback_hours: 回溯时间（小时）

        Returns:
            推文列表
        """
        if self.use_nitter:
            return self._collect_via_nitter(lookback_hours)
        else:
            return self._collect_via_rsshub(lookback_hours)

    def _collect_via_nitter(self, lookback_hours: int) -> List[Dict]:
        """使用 Nitter 收集推文"""
        all_tweets = []
        cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)

        for account in self.config.get("accounts", []):
            try:
                logger.info(f"正在收集 @{account}...")
                tweets = self._collect_from_account_nitter(account, cutoff_time)
                all_tweets.extend(tweets)
                logger.info(f"从 @{account} 收集到 {len(tweets)} 条推文")

                # 避免请求过快
                time.sleep(2)

            except Exception as e:
                logger.error(f"收集 @{account} 失败: {e}")
                continue

        logger.info(f"X/Twitter 总共收集到 {len(all_tweets)} 条推文")
        return all_tweets

    def _collect_from_account_nitter(
        self, username: str, cutoff_time: datetime
    ) -> List[Dict]:
        """从 Nitter 收集账号推文"""
        tweets = []

        try:
            url = f"https://{self.nitter_instance}/{username}"
            response = self.session.get(url, timeout=10)

            if response.status_code != 200:
                logger.warning(f"Nitter 请求失败: {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, "html.parser")

            # 解析推文
            tweet_elements = soup.find_all("div", class_="timeline-item")

            for tweet_el in tweet_elements:
                try:
                    tweet_data = self._parse_nitter_tweet(tweet_el, username)

                    if not tweet_data:
                        continue

                    # 检查时间
                    if tweet_data["created_at"] < cutoff_time:
                        continue

                    tweets.append(tweet_data)

                except Exception as e:
                    logger.debug(f"解析推文失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"Nitter 收集失败: {e}")

        return tweets

    def _parse_nitter_tweet(self, tweet_el, username: str) -> Dict:
        """解析 Nitter 推文元素"""
        try:
            # 提取文本
            text_el = tweet_el.find("div", class_="tweet-content")
            text = text_el.get_text(strip=True) if text_el else ""

            # 提取链接
            link_el = tweet_el.find("a", class_="tweet-link")
            tweet_id = ""
            if link_el and "href" in link_el.attrs:
                href = link_el["href"]
                tweet_id = href.split("/")[-1].replace("#m", "")

            # 提取时间
            time_el = tweet_el.find("span", class_="tweet-date")
            created_at = datetime.utcnow()  # 默认值
            if time_el and "title" in time_el.attrs:
                try:
                    created_at = datetime.strptime(
                        time_el["title"], "%b %d, %Y · %I:%M %p %Z"
                    )
                except:
                    pass

            # 提取互动数据
            stats_el = tweet_el.find("div", class_="tweet-stats")
            retweets = 0
            likes = 0
            replies = 0

            if stats_el:
                stats = stats_el.find_all("span", class_="tweet-stat")
                for stat in stats:
                    stat_text = stat.get_text(strip=True)
                    if "retweet" in stat.get("class", []):
                        retweets = self._parse_count(stat_text)
                    elif "quote" in stat.get("class", []):
                        pass
                    elif "heart" in stat.get("class", []):
                        likes = self._parse_count(stat_text)

            return {
                "id": tweet_id,
                "username": username,
                "text": text,
                "url": f"https://twitter.com/{username}/status/{tweet_id}",
                "created_at": created_at,
                "source": "twitter",
                # 互动指标
                "engagement": {
                    "retweets": retweets,
                    "likes": likes,
                    "replies": replies,
                },
                "retweets": retweets,
                "likes": likes,
                # 用于后续分析
                "raw_text": text,
            }

        except Exception as e:
            logger.debug(f"解析推文详情失败: {e}")
            return None

    def _parse_count(self, text: str) -> int:
        """解析数字（支持 K, M 后缀）"""
        text = text.strip().replace(",", "")

        if "K" in text:
            return int(float(text.replace("K", "")) * 1000)
        elif "M" in text:
            return int(float(text.replace("M", "")) * 1000000)
        else:
            try:
                return int(text)
            except:
                return 0

    def _collect_via_rsshub(self, lookback_hours: int) -> List[Dict]:
        """
        使用 RSSHub 收集推文

        RSSHub: https://rsshub.app/twitter/user/:username
        尝试多个实例以提高可靠性
        """
        import feedparser

        all_tweets = []
        cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)

        # 多个 RSSHub 实例备选
        rsshub_instances = [
            self.config.get("rsshub_instance", "https://rsshub.app"),
            "https://rsshub.rssforever.com",
            "https://rsshub.feeded.xyz",
            "https://rsshub.pseudoyu.com",
        ]

        rsshub_base = None
        for instance in rsshub_instances:
            try:
                # 测试实例可用性
                test_response = self.session.get(instance, timeout=5)
                if test_response.status_code == 200:
                    rsshub_base = instance
                    logger.info(f"使用 RSSHub 实例: {instance}")
                    break
            except:
                continue

        if not rsshub_base:
            logger.error("所有 RSSHub 实例均不可用")
            return []

        for account in self.config.get("accounts", []):
            account_tweets = []
            try:
                rss_url = f"{rsshub_base}/twitter/user/{account}"
                feed = feedparser.parse(rss_url)

                for entry in feed.entries:
                    published = datetime.fromtimestamp(
                        time.mktime(entry.published_parsed)
                    )

                    if published < cutoff_time:
                        continue

                    tweet_data = {
                        "id": entry.link.split("/")[-1],
                        "username": account,
                        "text": entry.summary,
                        "url": entry.link,
                        "created_at": published,
                        "source": "twitter",
                        "engagement": {"retweets": 0, "likes": 0, "replies": 0},
                        "raw_text": entry.summary,
                    }

                    account_tweets.append(tweet_data)

                all_tweets.extend(account_tweets)
                logger.info(f"从 @{account} 收集到 {len(account_tweets)} 条推文")

                time.sleep(1)  # 避免请求过快

            except Exception as e:
                logger.error(f"RSSHub 收集失败 {account}: {e}")
                continue

        logger.info(f"Twitter 总共收集到 {len(all_tweets)} 条推文")
        return all_tweets


def test_collector():
    """测试收集器"""
    config = {"accounts": ["sama", "AnthropicAI", "OpenAI"], "use_nitter": True}

    collector = TwitterCollector(config)
    tweets = collector.collect(lookback_hours=48)

    print(f"\n收集到 {len(tweets)} 条推文:")
    for tweet in tweets[:5]:
        print(f"\n@{tweet['username']}: {tweet['text'][:100]}...")
        print(f"点赞: {tweet['likes']} | 转推: {tweet['retweets']}")
        print(f"链接: {tweet['url']}")


if __name__ == "__main__":
    test_collector()
