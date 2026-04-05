"""
AI 内容过滤器
只保留 AI 相关的内容
"""

from typing import List, Dict
from loguru import logger


class AIContentFilter:
    """AI 内容过滤器"""

    def __init__(self, ai_keywords: List[str]):
        """
        初始化过滤器

        Args:
            ai_keywords: AI 关键词列表
        """
        self.ai_keywords = [kw.lower() for kw in ai_keywords]
        logger.info(f"AI 过滤器初始化，关键词数量: {len(self.ai_keywords)}")

    def is_ai_related(self, text: str) -> bool:
        """
        判断文本是否与 AI 相关

        Args:
            text: 待检测文本

        Returns:
            是否 AI 相关
        """
        text_lower = text.lower()

        for keyword in self.ai_keywords:
            if keyword in text_lower:
                return True

        return False

    def filter_items(self, items: List[Dict]) -> List[Dict]:
        """
        过滤出 AI 相关内容

        Args:
            items: 内容列表

        Returns:
            过滤后的列表
        """
        filtered = []

        for item in items:
            # 检查标题和内容
            title = item.get("title", "")
            raw_text = item.get("raw_text", "")
            combined_text = f"{title} {raw_text}"

            if self.is_ai_related(combined_text):
                filtered.append(item)
            else:
                logger.debug(f"过滤掉非 AI 内容: {title[:50]}")

        logger.info(f"AI 过滤: {len(items)} → {len(filtered)} ({len(filtered)/len(items)*100:.1f}%)")

        return filtered


def test_filter():
    """测试过滤器"""
    keywords = ["AI", "GPT", "Claude", "machine learning", "neural"]

    filter = AIContentFilter(keywords)

    test_items = [
        {"title": "GPT-5 发布", "raw_text": "OpenAI 发布了新模型"},
        {"title": "iPhone 新功能", "raw_text": "苹果发布了新手机"},
        {"title": "Claude AI 更新", "raw_text": "Anthropic 发布更新"},
    ]

    filtered = filter.filter_items(test_items)

    print(f"\n原始: {len(test_items)} 条")
    print(f"过滤后: {len(filtered)} 条")

    for item in filtered:
        print(f"  - {item['title']}")


if __name__ == "__main__":
    test_filter()
