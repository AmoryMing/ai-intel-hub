"""
Obsidian 导出器
将分析后的数据导出为 Obsidian Markdown 格式
"""

from datetime import datetime
from typing import List, Dict
from pathlib import Path
from loguru import logger
import os


class ObsidianExporter:
    """Obsidian 文件导出器"""

    def __init__(self, config: dict):
        """
        初始化导出器

        Args:
            config: Obsidian 配置字典
        """
        self.config = config
        self.vault_path = Path(config.get("vault_path", "./data/obsidian"))
        self.daily_notes_path = self.vault_path / config.get(
            "daily_notes_path", "AI-Hotspots/Daily"
        )
        self.tags = config.get("tags", [])

        # 确保目录存在
        self.daily_notes_path.mkdir(parents=True, exist_ok=True)

    def export(
        self, items: List[Dict], date: datetime, notebooklm_info: Dict = None
    ) -> str:
        """
        导出为 Obsidian 文件

        Args:
            items: 分析后的内容列表
            date: 日期
            notebooklm_info: NotebookLM 信息

        Returns:
            生成的文件路径
        """
        try:
            # 按分类组织数据
            categorized_items = self._categorize_items(items)

            # 生成 Markdown 内容
            content = self._generate_markdown(items, categorized_items, date, notebooklm_info)

            # 写入文件
            filename = f"{date.strftime('%Y-%m-%d')}.md"
            filepath = self.daily_notes_path / filename

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Obsidian 文件已生成: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"导出 Obsidian 文件失败: {e}")
            raise

    def _categorize_items(self, items: List[Dict]) -> Dict:
        """按分类组织内容"""
        categorized = {}

        for item in items:
            analysis = item.get("analysis", {})
            category = analysis.get("category", "未分类")

            if category not in categorized:
                categorized[category] = []

            categorized[category].append(item)

        # 按重要性排序
        for category in categorized:
            categorized[category].sort(
                key=lambda x: x.get("analysis", {}).get("importance", 0), reverse=True
            )

        return categorized

    def _generate_markdown(
        self, items: List[Dict], categorized_items: Dict, date: datetime, notebooklm_info: Dict
    ) -> str:
        """生成 Markdown 内容"""
        # 统计数据
        sources_count = self._count_by_source(items)

        # 前置元数据
        frontmatter = self._generate_frontmatter(date, sources_count, len(items))

        # 标题和概览
        header = f"# 🔥 AI 热点速递 - {date.strftime('%Y-%m-%d')}\n\n"
        overview = self._generate_overview(sources_count, len(items))

        # 分类内容
        content_sections = []
        for category, cat_items in categorized_items.items():
            icon = self._get_category_icon(category)
            section = f"\n## {icon} {category}\n\n"

            for item in cat_items:
                section += self._format_item(item)

            content_sections.append(section)

        # 趋势分析
        trends = self._generate_trends(items, categorized_items)

        # NotebookLM 信息
        notebooklm_section = self._generate_notebooklm_section(notebooklm_info)

        # 组合所有部分
        full_content = (
            frontmatter
            + header
            + overview
            + "---\n\n"
            + "\n".join(content_sections)
            + "\n"
            + trends
            + "\n"
            + notebooklm_section
            + "\n---\n\n"
            + "*本文档由 AI 热点收集系统自动生成*\n"
        )

        return full_content

    def _generate_frontmatter(
        self, date: datetime, sources_count: Dict, total: int
    ) -> str:
        """生成前置元数据"""
        tags = ", ".join(self.tags)
        sources = ", ".join(sources_count.keys())

        return f"""---
date: {date.strftime('%Y-%m-%d')}
tags: [{tags}]
sources: [{sources}]
total_items: {total}
---

"""

    def _generate_overview(self, sources_count: Dict, total: int) -> str:
        """生成概览部分"""
        return f"""## 📊 今日概览

- **总计条目**: {total}
- **YouTube 视频**: {sources_count.get('youtube', 0)}
- **Reddit 讨论**: {sources_count.get('reddit', 0)}
- **X 帖子**: {sources_count.get('twitter', 0)}

"""

    def _format_item(self, item: Dict) -> str:
        """格式化单个内容项"""
        analysis = item.get("analysis", {})

        title = item.get("title", "无标题")
        source = item.get("source", "unknown")
        url = item.get("url", "")

        # 作者信息
        author = self._get_author_display(item)

        # 重要性星级
        importance = analysis.get("importance", 3)
        stars = "⭐" * importance

        # 互动数据
        engagement_text = self._format_engagement(item)

        # 情感分析
        sentiment = analysis.get("sentiment", {})
        sentiment_emoji = sentiment.get("emoji", "😐")
        sentiment_label = sentiment.get("sentiment", "neutral")

        # 摘要和关键点
        summary = analysis.get("summary", "")
        key_points = analysis.get("key_points", [])

        content = f"""### {title}

- **来源**: {source.capitalize()} - {author}
- **热度**: {stars} {engagement_text}
- **情感**: {sentiment_emoji} {sentiment_label}
- **AI 摘要**: {summary}

"""

        if key_points:
            content += "**关键点**:\n"
            for point in key_points:
                content += f"- {point}\n"
            content += "\n"

        content += f"**链接**: [查看原文]({url})\n\n---\n\n"

        return content

    def _get_author_display(self, item: Dict) -> str:
        """获取作者显示名称"""
        source = item.get("source", "")

        if source == "reddit":
            return f"u/{item.get('author', 'unknown')} @ r/{item.get('subreddit', 'unknown')}"
        elif source == "youtube":
            return item.get("channel_title", "Unknown Channel")
        elif source == "twitter":
            return f"@{item.get('username', 'unknown')}"
        else:
            return "Unknown"

    def _format_engagement(self, item: Dict) -> str:
        """格式化互动数据"""
        engagement = item.get("engagement", {})
        source = item.get("source", "")

        if source == "reddit":
            return f"👍 {engagement.get('score', 0)} | 💬 {engagement.get('comments', 0)}"
        elif source == "youtube":
            views = engagement.get("views", 0)
            likes = engagement.get("likes", 0)
            return f"👁️ {self._format_number(views)} | 👍 {self._format_number(likes)}"
        elif source == "twitter":
            likes = engagement.get("likes", 0)
            retweets = engagement.get("retweets", 0)
            return f"❤️ {self._format_number(likes)} | 🔄 {self._format_number(retweets)}"
        else:
            return ""

    def _format_number(self, num: int) -> str:
        """格式化数字（添加 K, M 后缀）"""
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        else:
            return str(num)

    def _count_by_source(self, items: List[Dict]) -> Dict:
        """按来源统计数量"""
        counts = {"youtube": 0, "reddit": 0, "twitter": 0}

        for item in items:
            source = item.get("source", "unknown")
            if source in counts:
                counts[source] += 1

        return counts

    def _get_category_icon(self, category: str) -> str:
        """获取分类图标"""
        icons = {
            "AI 模型发布和更新": "🤖",
            "AI 硬件（芯片、设备）": "💻",
            "AI 公司动态": "🏢",
            "AI 应用和工具": "🛠️",
        }

        return icons.get(category, "📌")

    def _generate_trends(self, items: List[Dict], categorized_items: Dict) -> str:
        """生成趋势分析部分"""
        trends = "## 📈 今日趋势分析\n\n"

        # 最热话题分布
        total = len(items)
        trends += "### 最热话题\n\n"

        for category, cat_items in categorized_items.items():
            percentage = (len(cat_items) / total * 100) if total > 0 else 0
            trends += f"- **{category}**: {percentage:.1f}% ({len(cat_items)} 条)\n"

        # Top 10
        trends += "\n### Top 10 热点\n\n"
        sorted_items = sorted(
            items, key=lambda x: x.get("analysis", {}).get("importance", 0), reverse=True
        )

        for i, item in enumerate(sorted_items[:10], 1):
            title = item.get("title", "")[:60]
            importance = item.get("analysis", {}).get("importance", 3)
            stars = "⭐" * importance
            trends += f"{i}. {title} - {stars}\n"

        return trends + "\n"

    def _generate_notebooklm_section(self, notebooklm_info: Dict) -> str:
        """生成 NotebookLM 部分"""
        section = "## 🔗 NotebookLM 集成\n\n"

        if notebooklm_info and notebooklm_info.get("notebook_id"):
            section += f"""- **Notebook ID**: `{notebooklm_info.get('notebook_id')}`
- **Notebook 名称**: "{notebooklm_info.get('notebook_name', 'AI Weekly Digest')}"
- **状态**: ✅ 已同步

"""
        else:
            section += "- **状态**: ⏳ 等待同步\n\n"

        return section


def test_exporter():
    """测试导出器"""
    config = {
        "vault_path": "./data/obsidian",
        "daily_notes_path": "AI-Hotspots/Daily",
        "tags": ["ai-hotspots", "daily", "auto-generated"],
    }

    exporter = ObsidianExporter(config)

    test_items = [
        {
            "title": "GPT-5 发布日期曝光",
            "source": "reddit",
            "author": "ai_researcher",
            "subreddit": "MachineLearning",
            "url": "https://reddit.com/r/MachineLearning/...",
            "engagement": {"score": 5000, "comments": 200},
            "analysis": {
                "category": "AI 模型发布和更新",
                "summary": "OpenAI CEO 暗示 GPT-5 将在 Q2 发布",
                "key_points": ["Q2 发布", "性能提升 10 倍", "支持多模态"],
                "sentiment": {"sentiment": "positive", "emoji": "🎉"},
                "importance": 5,
            },
        }
    ]

    filepath = exporter.export(test_items, datetime.now())
    print(f"\n文件已生成: {filepath}")


if __name__ == "__main__":
    test_exporter()
