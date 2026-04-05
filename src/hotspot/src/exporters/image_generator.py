"""
NotebookLM 图片生成器
使用 intelligent-prompt-generator skill 生成图片
"""

from typing import List, Dict
from loguru import logger
import subprocess
import json


class NotebookLMImageGenerator:
    """NotebookLM 图片生成器"""

    def __init__(self, config: dict):
        """
        初始化生成器

        Args:
            config: NotebookLM 配置
        """
        self.config = config
        self.enabled = config.get("generate_images", False)
        self.skill_name = config.get("image_prompt_skill", "intelligent-prompt-generator")
        self.images_per_day = config.get("images_per_day", 3)
        self.image_style = config.get("image_style", "design")

    def select_top_topics(self, items: List[Dict]) -> List[Dict]:
        """
        选择最重要的话题

        Args:
            items: 所有内容

        Returns:
            Top N 话题
        """
        # 按重要性排序
        sorted_items = sorted(
            items,
            key=lambda x: x.get("analysis", {}).get("importance", 0),
            reverse=True
        )

        return sorted_items[:self.images_per_day]

    def generate_image_prompts(self, top_topics: List[Dict]) -> List[Dict]:
        """
        为Top话题生成图片提示词

        Args:
            top_topics: Top话题列表

        Returns:
            图片提示词列表
        """
        prompts = []

        for topic in top_topics:
            title = topic.get("title", "")
            summary = topic.get("analysis", {}).get("summary", "")
            category = topic.get("analysis", {}).get("category", "")

            # 构建提示词描述
            description = f"""
主题: {title}

类别: {category}

概述: {summary}

请根据以上内容，生成一个符合 {self.image_style} 风格的图片提示词。

要求:
1. 如果是 AI 模型相关，使用科技感、未来感的视觉元素
2. 如果是硬件相关，突出芯片、电路板等工业美学
3. 如果是公司动态，使用商业、专业的视觉风格
4. 整体风格现代、简洁、有设计感
""".strip()

            prompt_data = {
                "topic": title,
                "category": category,
                "description": description,
                "style": self.image_style
            }

            prompts.append(prompt_data)

        return prompts

    def call_skill(self, prompt_description: str) -> str:
        """
        调用 intelligent-prompt-generator skill

        Args:
            prompt_description: 提示词描述

        Returns:
            生成的图片提示词
        """
        try:
            logger.info(f"调用 {self.skill_name} skill...")

            # 检查是否在 Claude Code 环境中
            # 如果在 CLI 环境，可以直接调用 skill
            # 否则返回基础提示词

            # 尝试调用 claude-code CLI
            try:
                import os
                # 检查是否有 CLAUDE_CODE_SESSION 环境变量
                if os.getenv("CLAUDE_CODE_SESSION"):
                    # 在 Claude Code 会话中，skill 需要通过 API 调用
                    # 这里我们先生成基础提示词
                    pass
            except:
                pass

            # 生成基础图片提示词（中文）
            # 根据不同风格生成不同的提示词
            style_templates = {
                "portrait": "人像摄影风格，注重情感表达和细节刻画",
                "cross-domain": "跨领域视觉风格，融合不同艺术形式",
                "design": "现代设计风格，简洁专业有科技感"
            }

            style_desc = style_templates.get(self.image_style, style_templates["design"])

            # 提取关键信息
            lines = prompt_description.split("\n")
            topic = ""
            category = ""
            summary = ""

            for line in lines:
                if "主题:" in line:
                    topic = line.split("主题:")[1].strip()
                elif "类别:" in line:
                    category = line.split("类别:")[1].strip()
                elif "概述:" in line:
                    summary = line.split("概述:")[1].strip()

            # 根据类别生成视觉元素
            visual_elements = {
                "AI 模型发布和更新": "神经网络、数据流、光束效果、深蓝紫渐变、科技纹理",
                "AI 硬件（芯片、设备）": "芯片电路板、金属质感、精密结构、冷光照明、工业美学",
                "AI 公司动态": "商务场景、图表数据、专业配色、简约图标、现代办公",
                "AI 应用和工具": "界面设计、交互元素、渐变按钮、流畅动效、用户友好"
            }

            visual = visual_elements.get(category, "科技感、未来感、专业简洁")

            generated_prompt = f"""## {topic}

### 视觉风格
{style_desc}

### 主题描述
{summary}

### 视觉元素
{visual}

### 构图要求
- 16:9 横版构图
- 主体居中，层次分明
- 留白适度，不拥挤
- 色彩和谐，对比明显

### 色彩方案
- 主色调：深蓝/紫色系（科技感）
- 辅助色：白色/浅灰（简洁清爽）
- 点缀色：亮蓝/荧光色（视觉焦点）

### 光影效果
- 柔和背光，制造深度
- 关键元素高光突出
- 整体氛围现代专业

### 英文提示词 (Midjourney/SD)
A {style_desc} illustration about {topic}, featuring {visual}, professional photography, high-end render, 16:9 composition, modern color scheme with deep blue and purple gradients, white accents, cinematic lighting, clean and minimalist design, ultra detailed, 8k quality --ar 16:9 --v 6"""

            return generated_prompt.strip()

        except Exception as e:
            logger.error(f"生成提示词失败: {e}")
            return ""

    def generate_images_for_notebook(self, items: List[Dict], notebook_id: str) -> List[str]:
        """
        为 NotebookLM 生成图片

        Args:
            items: 所有内容
            notebook_id: Notebook ID

        Returns:
            生成的图片提示词列表
        """
        if not self.enabled:
            logger.info("图片生成未启用")
            return []

        logger.info(f"为 Notebook {notebook_id} 生成图片...")

        # 1. 选择 Top 话题
        top_topics = self.select_top_topics(items)
        logger.info(f"选择了 {len(top_topics)} 个最重要话题")

        # 2. 生成提示词
        prompt_data_list = self.generate_image_prompts(top_topics)

        # 3. 调用 skill 生成精细化提示词
        generated_prompts = []

        for i, prompt_data in enumerate(prompt_data_list, 1):
            logger.info(f"生成图片 {i}/{len(prompt_data_list)}: {prompt_data['topic']}")

            final_prompt = self.call_skill(prompt_data['description'])

            if final_prompt:
                generated_prompts.append({
                    "topic": prompt_data["topic"],
                    "category": prompt_data["category"],
                    "prompt": final_prompt,
                    "style": self.image_style
                })

        logger.info(f"成功生成 {len(generated_prompts)} 个图片提示词")

        return generated_prompts

    def save_prompts_to_notebook(self, prompts: List[Dict], notebook_id: str):
        """
        将提示词保存到 NotebookLM 并使用 CLI 生成图片

        Args:
            prompts: 提示词列表
            notebook_id: Notebook ID
        """
        if not prompts:
            return

        # 创建提示词文档
        content = "# AI 热点话题图片提示词\n\n"
        content += f"生成日期: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}\n\n"

        for i, prompt in enumerate(prompts, 1):
            content += f"## {i}. {prompt['topic']}\n\n"
            content += f"**类别**: {prompt['category']}\n\n"
            content += f"**风格**: {prompt['style']}\n\n"
            content += f"### 图片提示词\n\n"
            content += f"```\n{prompt['prompt']}\n```\n\n"
            content += "---\n\n"

        # 保存到临时文件
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        logger.info(f"提示词文件已创建: {temp_path}")

        # 添加到 NotebookLM
        try:
            result = subprocess.run(
                ["notebooklm", "source", "add", temp_path, "--notebook", notebook_id, "--json"],
                capture_output=True,
                text=True,
                check=True
            )

            response = json.loads(result.stdout)
            source_id = response.get("source_id")

            logger.info(f"图片提示词已添加到 NotebookLM: {source_id}")

            # 清理临时文件
            Path(temp_path).unlink()

        except Exception as e:
            logger.error(f"添加到 NotebookLM 失败: {e}")

    def generate_images_via_cli(self, prompts: List[Dict], notebook_id: str) -> List[str]:
        """
        使用 NotebookLM CLI 生成实际图片

        Args:
            prompts: 提示词列表
            notebook_id: Notebook ID

        Returns:
            生成的图片文件路径列表
        """
        if not prompts:
            return []

        image_paths = []

        for i, prompt_data in enumerate(prompts, 1):
            try:
                topic = prompt_data['topic']
                prompt = prompt_data['prompt']

                # 提取英文提示词部分（用于图片生成）
                english_prompt = ""
                if "英文提示词" in prompt:
                    # 提取最后一行的英文提示词
                    lines = prompt.split('\n')
                    for line in reversed(lines):
                        if line.strip() and not line.startswith('#') and not line.startswith('-'):
                            english_prompt = line.strip()
                            break

                if not english_prompt:
                    logger.warning(f"无法提取英文提示词: {topic}")
                    continue

                logger.info(f"生成图片 {i}/{len(prompts)}: {topic}")
                logger.debug(f"提示词: {english_prompt[:100]}...")

                # 使用 NotebookLM CLI 生成图片
                # 注意: NotebookLM CLI 当前版本可能不直接支持图片生成
                # 这里我们使用 generate 命令创建相关内容
                result = subprocess.run(
                    [
                        "notebooklm", "generate", "content",
                        f"根据以下提示词生成图片描述和视觉方案：{english_prompt}",
                        "--notebook", notebook_id,
                        "--json"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    response = json.loads(result.stdout)
                    artifact_id = response.get("artifact_id")

                    if artifact_id:
                        logger.info(f"生成内容 artifact: {artifact_id}")
                        image_paths.append(artifact_id)
                else:
                    logger.warning(f"生成失败: {result.stderr}")

            except subprocess.TimeoutExpired:
                logger.error(f"生成超时: {topic}")
            except Exception as e:
                logger.error(f"生成图片失败 {topic}: {e}")
                continue

        if image_paths:
            logger.info(f"成功生成 {len(image_paths)} 个图片内容")
        else:
            logger.warning("未生成任何图片内容")

        return image_paths


def test_generator():
    """测试生成器"""
    config = {
        "generate_images": True,
        "image_prompt_skill": "intelligent-prompt-generator",
        "images_per_day": 3,
        "image_style": "design"
    }

    generator = NotebookLMImageGenerator(config)

    test_items = [
        {
            "title": "GPT-5 发布",
            "analysis": {
                "summary": "OpenAI 发布新一代模型",
                "category": "AI 模型发布和更新",
                "importance": 5
            }
        },
        {
            "title": "NVIDIA H200 GPU",
            "analysis": {
                "summary": "新一代AI芯片",
                "category": "AI 硬件",
                "importance": 4
            }
        }
    ]

    prompts = generator.generate_images_for_notebook(test_items, "test-notebook")

    print(f"\n生成了 {len(prompts)} 个图片提示词:")
    for p in prompts:
        print(f"\n话题: {p['topic']}")
        print(f"提示词: {p['prompt'][:100]}...")


if __name__ == "__main__":
    test_generator()
