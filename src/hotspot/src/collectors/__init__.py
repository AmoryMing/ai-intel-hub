"""
收集器包初始化
"""

from .reddit_collector import RedditCollector
from .youtube_collector import YouTubeCollector
from .twitter_collector import TwitterCollector

__all__ = ["RedditCollector", "YouTubeCollector", "TwitterCollector"]
