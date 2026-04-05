"""
AI 分析器
使用 Claude API 进行内容分类、总结和情感分析
"""

from anthropic import Anthropic
from typing import List, Dict, Optional
from loguru import logger
import os
from dotenv import load_dotenv
import json

load_dotenv()


class AIAnalyzer:
    """AI 内容分析器"""

    def __init__(self, config: dict):
        """
        初始化 AI 分析器

        Args:
            config: AI 配置字典
        """
        self.config = config
        self.client = self._init_client()
        self.categories = self.config.get("categories", [])

    def _init_client(self) -> Anthropic:
        """初始化 Claude API 客户端"""
        try:
            # 尝试多种方式获取 API 密钥
            api_key = os.getenv("ANTHROPIC_API_KEY")

            # 如果环境变量没有，尝试直接初始化（Claude Code 环境）
            if not api_key:
                try:
                    client = Anthropic()  # 使用默认配置
                    logger.info("Claude API 初始化成功（使用默认配置）")
                    return client
                except Exception as e:
                    logger.warning(f"默认初始化失败: {e}")
                    logger.warning("ANTHROPIC_API_KEY 未设置，将使用简化分析")
                    return None

            client = Anthropic(api_key=api_key)
            logger.info("Claude API 初始化成功")
            return client

        except Exception as e:
            logger.error(f"Claude API 初始化失败: {e}")
            logger.warning("将使用简化分析")
            return None

    def analyze_batch(self, items: List[Dict]) -> List[Dict]:
        """
        批量分析内容

        Args:
            items: 内容列表

        Returns:
            分析后的内容列表
        """
        analyzed_items = []

        # 如果没有 Claude API，使用简化分析
        if not self.client:
            logger.info("使用简化分析（无 AI API）")
            return self._simple_analyze(items)

        for item in items:
            try:
                # 分类
                category = self._classify(item.get("raw_text", ""))

                # 总结
                summary = self._summarize(item)

                # 提取关键点
                key_points = self._extract_key_points(item)

                # 情感分析
                sentiment = self._analyze_sentiment(item.get("raw_text", ""))

                # 重要性评分
                importance = self._calculate_importance(item, sentiment)

                # 添加分析结果
                item["analysis"] = {
                    "category": category,
                    "summary": summary,
                    "key_points": key_points,
                    "sentiment": sentiment,
                    "importance": importance,
                }

                analyzed_items.append(item)
                logger.debug(f"分析完成: {item.get('title', '')[:50]}")

            except Exception as e:
                logger.error(f"分析失败: {e}")
                # 保留原始数据
                analyzed_items.append(item)
                continue

        return analyzed_items

    def _classify(self, text: str) -> str:
        """
        内容分类

        Args:
            text: 文本内容

        Returns:
            分类名称
        """
        # 基于关键词的快速分类
        text_lower = text.lower()

        for category in self.categories:
            keywords = category.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return category["name"]

        # 如果没有匹配，使用 AI 分类
        return self._ai_classify(text)

    def _ai_classify(self, text: str) -> str:
        """使用 AI 进行分类"""
        try:
            category_names = [cat["name"] for cat in self.categories]

            prompt = f"""请将以下内容分类到最合适的类别中：

类别选项：
{', '.join(category_names)}

内容：
{text[:500]}

只返回类别名称，不需要其他解释。"""

            message = self.client.messages.create(
                model=self.config.get("model", "claude-sonnet-4-5"),
                max_tokens=50,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )

            category = message.content[0].text.strip()

            # 验证分类结果
            if category in category_names:
                return category
            else:
                return category_names[0]  # 默认第一个分类

        except Exception as e:
            logger.error(f"AI 分类失败: {e}")
            return self.categories[0]["name"] if self.categories else "未分类"

    def _summarize(self, item: Dict) -> str:
        """
        生成摘要

        Args:
            item: 内容项

        Returns:
            摘要文本
        """
        try:
            title = item.get("title", "")
            text = item.get("raw_text", "")[:2000]

            prompt = f"""请用中文总结以下 AI 相关内容，一句话概括（不超过30字）：

标题: {title}
内容: {text}

只返回概括，不需要其他内容。"""

            message = self.client.messages.create(
                model=self.config.get("model", "claude-sonnet-4-5"),
                max_tokens=100,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}],
            )

            summary = message.content[0].text.strip()
            return summary

        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            return item.get("title", "")[:50]

    def _extract_key_points(self, item: Dict) -> List[str]:
        """
        提取关键点

        Args:
            item: 内容项

        Returns:
            关键点列表
        """
        try:
            text = item.get("raw_text", "")[:2000]

            prompt = f"""请从以下 AI 内容中提取 3-5 个关键点（每个不超过15字）：

{text}

以 JSON 数组格式返回，例如：["关键点1", "关键点2", "关键点3"]"""

            message = self.client.messages.create(
                model=self.config.get("model", "claude-sonnet-4-5"),
                max_tokens=200,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text.strip()

            # 尝试解析 JSON
            try:
                key_points = json.loads(response_text)
                if isinstance(key_points, list):
                    return key_points[:5]
            except:
                # 如果不是有效 JSON，按行分割
                lines = [
                    line.strip("- •")
                    for line in response_text.split("\n")
                    if line.strip()
                ]
                return lines[:5]

            return []

        except Exception as e:
            logger.error(f"提取关键点失败: {e}")
            return []

    def _analyze_sentiment(self, text: str) -> Dict:
        """
        情感分析

        Args:
            text: 文本内容

        Returns:
            情感分析结果
        """
        try:
            prompt = f"""分析以下文本的情感倾向：

{text[:500]}

返回 JSON 格式：
{{
    "sentiment": "positive/neutral/negative",
    "confidence": 0.0-1.0,
    "emoji": "😊/😐/😞"
}}"""

            message = self.client.messages.create(
                model=self.config.get("model", "claude-sonnet-4-5"),
                max_tokens=100,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text.strip()

            try:
                sentiment_data = json.loads(response_text)
                return sentiment_data
            except:
                return {"sentiment": "neutral", "confidence": 0.5, "emoji": "😐"}

        except Exception as e:
            logger.error(f"情感分析失败: {e}")
            return {"sentiment": "neutral", "confidence": 0.5, "emoji": "😐"}

    def _calculate_importance(self, item: Dict, sentiment: Dict) -> int:
        """
        计算重要性评分（1-5星）

        Args:
            item: 内容项
            sentiment: 情感分析结果

        Returns:
            评分 (1-5)
        """
        score = 3  # 基础分

        # 根据互动数据调整
        engagement = item.get("engagement", {})

        source = item.get("source", "")

        if source == "reddit":
            score_val = engagement.get("score", 0)
            if score_val > 1000:
                score += 1
            if score_val > 5000:
                score += 1

        elif source == "youtube":
            views = engagement.get("views", 0)
            if views > 100000:
                score += 1
            if views > 500000:
                score += 1

        elif source == "twitter":
            likes = engagement.get("likes", 0)
            if likes > 1000:
                score += 1
            if likes > 10000:
                score += 1

        # 确保在 1-5 范围内
        return max(1, min(5, score))

    def _simple_analyze(self, items: List[Dict]) -> List[Dict]:
        """简化分析（无需 API）"""
        for item in items:
            # 基于关键词的简单分类
            text = item.get("raw_text", "").lower()
            category = "AI 应用和工具"  # 默认

            for cat in self.categories:
                keywords = cat.get("keywords", [])
                for kw in keywords:
                    if kw.lower() in text:
                        category = cat["name"]
                        break

            # 简单分析
            item["analysis"] = {
                "category": category,
                "summary": item.get("title", "")[:50] + "...",
                "key_points": [],
                "sentiment": {"sentiment": "neutral", "emoji": "😐", "confidence": 0.5},
                "importance": self._calculate_importance(item, {}),
            }

        return items


def test_analyzer():
    """测试分析器"""
    config = {
        "model": "claude-sonnet-4-5",
        "categories": [
            {
                "name": "AI 模型发布和更新",
                "keywords": ["GPT", "Claude", "model", "release"],
            },
            {"name": "AI 硬件", "keywords": ["GPU", "chip", "hardware"]},
        ],
    }

    analyzer = AIAnalyzer(config)

    test_items = [
        {
            "title": "GPT-5 发布日期曝光",
            "raw_text": "OpenAI CEO Sam Altman 暗示 GPT-5 将在 Q2 发布，性能提升 10 倍",
            "source": "reddit",
            "engagement": {"score": 5000, "comments": 200},
        }
    ]

    analyzed = analyzer.analyze_batch(test_items)

    print("\n分析结果:")
    for item in analyzed:
        analysis = item.get("analysis", {})
        print(f"\n标题: {item['title']}")
        print(f"分类: {analysis.get('category')}")
        print(f"摘要: {analysis.get('summary')}")
        print(f"关键点: {analysis.get('key_points')}")
        print(f"情感: {analysis.get('sentiment')}")
        print(f"重要性: {'⭐' * analysis.get('importance', 3)}")


if __name__ == "__main__":
    test_analyzer()
