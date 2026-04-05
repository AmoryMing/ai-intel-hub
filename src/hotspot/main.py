"""
AI 热点收集系统 - 主程序
"""

import yaml
from datetime import datetime
from pathlib import Path
from loguru import logger
import sys

from collectors import RedditCollector, YouTubeCollector, TwitterCollector
from collectors.jike_collector import JikeCollector
from collectors.xiaohongshu_collector import XiaohongshuCollector
from processors import AIAnalyzer
from exporters import ObsidianExporter, NotebookLMSync


class AIHotspotCollector:
    """AI 热点收集系统主类"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化收集系统

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._init_components()

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.info(f"配置文件加载成功: {config_path}")
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            sys.exit(1)

    def _setup_logging(self):
        """配置日志"""
        logger.remove()  # 移除默认处理器

        # 控制台输出
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            level="INFO",
        )

        # 文件输出
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        logger.add(
            log_dir / "collector_{time:YYYY-MM-DD}.log",
            rotation="00:00",
            retention="30 days",
            level="DEBUG",
            encoding="utf-8",
        )

    def _init_components(self):
        """初始化各组件"""
        logger.info("初始化系统组件...")

        # 收集器
        self.collectors = {}

        if self.config["sources"]["reddit"].get("enabled", True):
            self.collectors["reddit"] = RedditCollector(self.config["sources"]["reddit"])

        if self.config["sources"]["youtube"].get("enabled", True):
            self.collectors["youtube"] = YouTubeCollector(self.config["sources"]["youtube"])

        if self.config["sources"]["twitter"].get("enabled", True):
            self.collectors["twitter"] = TwitterCollector(self.config["sources"]["twitter"])

        if self.config["sources"]["jike"].get("enabled", True):
            self.collectors["jike"] = JikeCollector(self.config["sources"]["jike"])

        if self.config["sources"]["xiaohongshu"].get("enabled", True):
            self.collectors["xiaohongshu"] = XiaohongshuCollector(self.config["sources"]["xiaohongshu"])

        # AI 分析器
        self.analyzer = AIAnalyzer(
            {
                **self.config["ai_summary"],
                "categories": self.config["categories"],
            }
        )

        # 导出器
        self.obsidian_exporter = ObsidianExporter(self.config["obsidian"])

        self.notebooklm_sync = NotebookLMSync(self.config["notebooklm"])

        logger.info(f"已初始化 {len(self.collectors)} 个收集器")

    def collect_all(self, lookback_hours: int = None) -> list:
        """
        从所有来源收集数据

        Args:
            lookback_hours: 回溯时间（小时）

        Returns:
            收集到的所有数据
        """
        if lookback_hours is None:
            lookback_hours = self.config["general"].get("lookback_hours", 24)

        logger.info(f"开始收集数据（回溯 {lookback_hours} 小时）")

        all_items = []

        for name, collector in self.collectors.items():
            try:
                logger.info(f"收集 {name} 数据...")
                items = collector.collect(lookback_hours)
                all_items.extend(items)
                logger.info(f"{name} 收集完成: {len(items)} 条")

            except Exception as e:
                logger.error(f"{name} 收集失败: {e}")
                continue

        logger.info(f"总共收集到 {len(all_items)} 条数据")
        return all_items

    def analyze_all(self, items: list) -> list:
        """
        分析所有数据

        Args:
            items: 待分析数据

        Returns:
            分析后的数据
        """
        logger.info("开始 AI 分析...")

        try:
            analyzed_items = self.analyzer.analyze_batch(items)
            logger.info(f"分析完成: {len(analyzed_items)} 条")
            return analyzed_items

        except Exception as e:
            logger.error(f"AI 分析失败: {e}")
            return items  # 返回原始数据

    def export_to_obsidian(self, items: list, date: datetime = None) -> str:
        """
        导出到 Obsidian

        Args:
            items: 数据列表
            date: 日期

        Returns:
            文件路径
        """
        if date is None:
            date = datetime.now()

        logger.info(f"导出到 Obsidian: {date.strftime('%Y-%m-%d')}")

        try:
            filepath = self.obsidian_exporter.export(items, date)
            logger.info(f"Obsidian 文件已生成: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"导出 Obsidian 失败: {e}")
            raise

    def sync_to_notebooklm(self, filepath: str, items: list = None) -> dict:
        """
        同步到 NotebookLM，并可选生成图片

        Args:
            filepath: Obsidian 文件路径
            items: 可选的热点数据列表（用于图片生成）

        Returns:
            同步信息
        """
        logger.info("同步到 NotebookLM...")

        try:
            sync_info = self.notebooklm_sync.sync_file(filepath, items)

            if sync_info:
                logger.info("NotebookLM 同步成功")
                if sync_info.get("image_artifacts"):
                    logger.info(f"生成了 {len(sync_info['image_artifacts'])} 个图片内容")
            else:
                logger.warning("NotebookLM 同步跳过或失败")

            return sync_info

        except Exception as e:
            logger.error(f"NotebookLM 同步失败: {e}")
            return None

    def run(self, lookback_hours: int = None):
        """
        运行完整流程

        Args:
            lookback_hours: 回溯时间（小时）
        """
        logger.info("=" * 60)
        logger.info("AI 热点收集系统启动")
        logger.info("=" * 60)

        try:
            # 1. 收集数据
            items = self.collect_all(lookback_hours)

            if not items:
                logger.warning("没有收集到数据，流程结束")
                return

            # 2. AI 分析
            analyzed_items = self.analyze_all(items)

            # 3. 导出到 Obsidian
            filepath = self.export_to_obsidian(analyzed_items)

            # 4. 同步到 NotebookLM（传递数据用于图片生成）
            notebooklm_info = self.sync_to_notebooklm(filepath, analyzed_items)

            # 5. 如果有同步信息，更新 Obsidian 文件
            if notebooklm_info:
                logger.info("更新 Obsidian 文件（添加 NotebookLM 信息）")
                self.obsidian_exporter.export(
                    analyzed_items, datetime.now(), notebooklm_info
                )

            logger.info("=" * 60)
            logger.info("✅ 流程完成")
            logger.info(f"📄 生成文件: {filepath}")
            logger.info(f"📊 总计条目: {len(analyzed_items)}")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"运行失败: {e}")
            raise


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="AI 热点收集系统")
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="配置文件路径",
    )
    parser.add_argument(
        "--hours",
        type=int,
        help="回溯小时数（覆盖配置文件）",
    )

    args = parser.parse_args()

    # 创建并运行收集器
    collector = AIHotspotCollector(args.config)
    collector.run(args.hours)


if __name__ == "__main__":
    main()
