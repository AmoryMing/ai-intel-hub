"""
NotebookLM 同步器
自动将 Obsidian 文件同步到 NotebookLM
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Optional
from loguru import logger
from datetime import datetime


class NotebookLMSync:
    """NotebookLM 自动同步器"""

    def __init__(self, config: dict):
        """
        初始化同步器

        Args:
            config: NotebookLM 配置字典
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.auto_sync = config.get("auto_sync", True)
        self.notebook_name = config.get("notebook_name", "AI Weekly Digest")

    def sync_file(self, filepath: str, items: list = None) -> Optional[Dict]:
        """
        同步单个文件到 NotebookLM，并可选生成图片

        Args:
            filepath: 文件路径
            items: 可选的热点数据列表（用于图片生成）

        Returns:
            同步信息字典
        """
        if not self.enabled or not self.auto_sync:
            logger.info("NotebookLM 同步已禁用")
            return None

        try:
            # 1. 查找或创建 notebook
            notebook_id = self._get_or_create_notebook()

            if not notebook_id:
                logger.error("无法获取或创建 Notebook")
                return None

            # 2. 添加文件作为 source
            source_id = self._add_source(notebook_id, filepath)

            if not source_id:
                logger.error("添加 source 失败")
                return None

            # 3. 等待处理完成
            self._wait_for_source(notebook_id, source_id)

            # 4. 生成图片（如果启用且提供了数据）
            image_artifacts = []
            if items and self.config.get("generate_images", False):
                image_artifacts = self._generate_images_for_items(items, notebook_id)

            logger.info(f"NotebookLM 同步成功: {filepath}")

            return {
                "notebook_id": notebook_id,
                "notebook_name": self.notebook_name,
                "source_id": source_id,
                "image_artifacts": image_artifacts,
                "synced_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"NotebookLM 同步失败: {e}")
            return None

    def _get_or_create_notebook(self) -> Optional[str]:
        """获取或创建 notebook"""
        try:
            # 先列出所有 notebooks
            result = subprocess.run(
                ["notebooklm", "list", "--json"],
                capture_output=True,
                text=True,
                check=True,
            )

            notebooks = json.loads(result.stdout)

            # 查找已存在的 notebook
            for notebook in notebooks.get("notebooks", []):
                if notebook.get("title") == self.notebook_name:
                    notebook_id = notebook.get("id")
                    logger.info(f"找到已存在的 Notebook: {notebook_id}")
                    return notebook_id

            # 不存在则创建新的
            logger.info(f"创建新 Notebook: {self.notebook_name}")

            result = subprocess.run(
                ["notebooklm", "create", self.notebook_name, "--json"],
                capture_output=True,
                text=True,
                check=True,
            )

            response = json.loads(result.stdout)
            notebook_id = response.get("id")

            if notebook_id:
                # 设置为当前上下文
                subprocess.run(
                    ["notebooklm", "use", notebook_id],
                    capture_output=True,
                    check=True,
                )

            return notebook_id

        except subprocess.CalledProcessError as e:
            logger.error(f"notebooklm 命令执行失败: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"获取/创建 Notebook 失败: {e}")
            return None

    def _add_source(self, notebook_id: str, filepath: str) -> Optional[str]:
        """添加文件为 source"""
        try:
            logger.info(f"添加 source: {filepath}")

            result = subprocess.run(
                [
                    "notebooklm",
                    "source",
                    "add",
                    filepath,
                    "--notebook",
                    notebook_id,
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            response = json.loads(result.stdout)
            source_id = response.get("source_id")

            logger.info(f"Source 已添加: {source_id}")
            return source_id

        except subprocess.CalledProcessError as e:
            logger.error(f"添加 source 失败: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"添加 source 失败: {e}")
            return None

    def _wait_for_source(
        self, notebook_id: str, source_id: str, timeout: int = 120
    ) -> bool:
        """等待 source 处理完成"""
        try:
            logger.info(f"等待 source 处理完成: {source_id}")

            result = subprocess.run(
                [
                    "notebooklm",
                    "source",
                    "wait",
                    source_id,
                    "-n",
                    notebook_id,
                    "--timeout",
                    str(timeout),
                ],
                capture_output=True,
                text=True,
                timeout=timeout + 10,
            )

            if result.returncode == 0:
                logger.info("Source 处理完成")
                return True
            else:
                logger.warning(f"Source 处理超时或失败: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.warning("等待 source 处理超时")
            return False
        except Exception as e:
            logger.error(f"等待 source 处理失败: {e}")
            return False

    def generate_weekly_podcast(self, notebook_id: Optional[str] = None) -> Optional[str]:
        """
        生成周报播客

        Args:
            notebook_id: Notebook ID（可选）

        Returns:
            Artifact ID
        """
        if not self.config.get("generate_weekly_podcast", False):
            return None

        try:
            if not notebook_id:
                notebook_id = self._get_or_create_notebook()

            if not notebook_id:
                return None

            logger.info("开始生成周报播客...")

            result = subprocess.run(
                [
                    "notebooklm",
                    "generate",
                    "audio",
                    "总结本周 AI 热点，重点关注重要发布和趋势变化",
                    "--notebook",
                    notebook_id,
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            response = json.loads(result.stdout)
            artifact_id = response.get("task_id")

            logger.info(f"播客生成任务已启动: {artifact_id}")
            logger.info("播客将在后台生成，请稍后使用 'notebooklm artifact list' 查看状态")

            return artifact_id

        except Exception as e:
            logger.error(f"生成播客失败: {e}")
            return None

    def check_authentication(self) -> bool:
        """检查 NotebookLM 认证状态"""
        try:
            result = subprocess.run(
                ["notebooklm", "status"],
                capture_output=True,
                text=True,
                check=True,
            )

            if "Authenticated" in result.stdout:
                logger.info("NotebookLM 认证正常")
                return True
            else:
                logger.warning("NotebookLM 未认证，请运行: notebooklm login")
                return False

        except subprocess.CalledProcessError:
            logger.error("NotebookLM CLI 未安装或认证失败")
            return False

    def _generate_images_for_items(self, items: list, notebook_id: str) -> list:
        """
        为热点数据生成图片

        Args:
            items: 热点数据列表
            notebook_id: Notebook ID

        Returns:
            生成的图片 artifact ID 列表
        """
        try:
            from exporters.image_generator import NotebookLMImageGenerator

            # 使用图片生成器
            generator = NotebookLMImageGenerator(self.config)

            # 生成图片提示词
            prompts = generator.generate_images_for_notebook(items, notebook_id)

            if not prompts:
                logger.info("未生成图片提示词")
                return []

            # 保存提示词到 NotebookLM
            generator.save_prompts_to_notebook(prompts, notebook_id)

            # 使用 CLI 生成图片
            artifacts = generator.generate_images_via_cli(prompts, notebook_id)

            return artifacts

        except ImportError:
            logger.error("无法导入 NotebookLMImageGenerator")
            return []
        except Exception as e:
            logger.error(f"生成图片失败: {e}")
            return []


def test_sync():
    """测试同步器"""
    config = {
        "enabled": True,
        "auto_sync": True,
        "notebook_name": "AI Weekly Digest Test",
        "generate_weekly_podcast": False,
    }

    sync = NotebookLMSync(config)

    # 检查认证
    if not sync.check_authentication():
        print("\n请先运行: notebooklm login")
        return

    # 测试同步（需要先创建测试文件）
    test_file = "./data/obsidian/AI-Hotspots/Daily/2026-01-14.md"

    if Path(test_file).exists():
        info = sync.sync_file(test_file)
        if info:
            print(f"\n同步成功!")
            print(f"Notebook ID: {info['notebook_id']}")
            print(f"Source ID: {info['source_id']}")
    else:
        print(f"\n测试文件不存在: {test_file}")


if __name__ == "__main__":
    test_sync()
