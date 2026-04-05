#!/usr/bin/env python3
"""
为 Top 10 生成增强版提示词（基于intelligent-prompt-generator原则），然后用 ModelScope 生图
"""

import json
import yaml
import requests
import time
from pathlib import Path
from PIL import Image
from io import BytesIO
from loguru import logger


class EnhancedTop10ImageGenerator:
    """基于智能提示词原则的Top 10图片生成器"""

    def __init__(self, config_path="config/config.yaml"):
        """初始化"""
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.vault_path = self.config['obsidian']['vault_path']
        self.daily_notes_path = self.config['obsidian']['daily_notes_path']

        # ModelScope API 配置
        self.base_url = 'https://api-inference.modelscope.cn/'
        self.api_key = "ms-b03451a2-f308-4023-b6d8-ba0e79928a25"
        self.model_id = "Tongyi-MAI/Z-Image-Turbo"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Top 10 热点定义
        self.top10_topics = [
            {
                'rank': 1,
                'title': 'NVIDIA端到端测试时训练',
                'summary': '英伟达提出测试时训练技术，可在推理过程中实时更新模型权重以学习上下文',
                'category': 'AI 模型发布和更新',
                'style': 'tech_neural_network'
            },
            {
                'rank': 2,
                'title': '单卡RTX 5090训练DeepSeek MoE',
                'summary': '开发者在单张RTX 5090上训练2.36B参数的DeepSeek风格MoE模型',
                'category': 'AI 模型发布和更新',
                'style': 'gpu_hardware'
            },
            {
                'rank': 3,
                'title': 'ISBI 2026医学影像会议',
                'summary': 'ISBI 2026医学影像会议录取结果公布',
                'category': 'AI 模型发布和更新',
                'style': 'medical_ai'
            },
            {
                'rank': 4,
                'title': '脊柱手术AI决策系统',
                'summary': '脊柱手术决策差异大，探索工作流驱动的结果导向方法',
                'category': 'AI 应用和工具',
                'style': 'medical_surgery'
            },
            {
                'rank': 5,
                'title': 'AI服务商故障分析',
                'summary': 'AI服务提供商的故障比大多数人预想的更加频繁',
                'category': 'AI 应用和工具',
                'style': 'infrastructure'
            },
            {
                'rank': 6,
                'title': '谱球优化器训练LLM',
                'summary': '提出谱球优化器，通过对权重和更新施加谱约束实现更稳定高效的大模型训练',
                'category': 'AI 模型发布和更新',
                'style': 'algorithm_math'
            },
            {
                'rank': 7,
                'title': '10个前沿模型互评系统',
                'summary': '构建矩阵评估系统，让10个前沿AI模型相互评判',
                'category': 'AI 模型发布和更新',
                'style': 'model_evaluation'
            },
            {
                'rank': 8,
                'title': 'CUDA工作站 vs Apple Silicon',
                'summary': '深入讨论CUDA工作站和Apple Silicon在机器学习及大语言模型训练中的优劣对比',
                'category': 'AI 硬件',
                'style': 'hardware_comparison'
            },
            {
                'rank': 9,
                'title': '智谱AI摆脱美国芯片依赖',
                'summary': '智谱AI首次使用华为技术栈训练大模型GLM-Image',
                'category': 'AI 公司动态',
                'style': 'chinese_tech'
            },
            {
                'rank': 10,
                'title': 'NVIDIA Orchestrator-8B模型',
                'summary': 'NVIDIA发布新的8B参数专业化orchestrator模型',
                'category': 'AI 模型发布和更新',
                'style': 'model_architecture'
            }
        ]

    def generate_enhanced_prompt(self, topic):
        """
        基于intelligent-prompt-generator原则生成增强提示词

        原则：
        1. 结构完整（主体+风格+光影+技术参数）
        2. 语义一致（所有元素风格统一）
        3. 视觉清晰（具体的视觉描述，不用模糊词）
        """

        # 风格到视觉元素的映射（设计模式）
        style_templates = {
            'tech_neural_network': {
                'subject': 'AI neural network visualization',
                'visual_elements': 'interconnected nodes, glowing connections, data flow particles, neural pathways',
                'color_scheme': 'deep blue to purple gradient, cyan highlights, white accents',
                'lighting': 'soft glow from nodes, ambient light, volumetric fog',
                'mood': 'futuristic, innovative, dynamic',
                'technical': '16:9 composition, high detail, 8k quality, professional render'
            },
            'gpu_hardware': {
                'subject': 'RTX GPU chip close-up',
                'visual_elements': 'circuit board, metal heatsink, LED lights, precision engineering',
                'color_scheme': 'metallic silver, tech blue, green PCB, orange accents',
                'lighting': 'dramatic side lighting, rim light on edges, reflections on metal',
                'mood': 'powerful, professional, cutting-edge',
                'technical': '16:9 macro photography style, ultra detailed, 8k'
            },
            'medical_ai': {
                'subject': 'medical AI imaging system',
                'visual_elements': 'medical scans, AI analysis overlay, diagnostic interface, data visualization',
                'color_scheme': 'clinical white, medical blue, data green, soft gradients',
                'lighting': 'clean clinical lighting, screen glow, professional environment',
                'mood': 'precise, trustworthy, advanced',
                'technical': '16:9 professional photography, high clarity, 8k'
            },
            'medical_surgery': {
                'subject': 'AI-assisted surgical planning',
                'visual_elements': 'surgical interface, 3D spine model, decision flowchart, AI recommendation display',
                'color_scheme': 'medical blue, white interface, red highlights for key areas',
                'lighting': 'clean medical lighting, screen illumination, focused light',
                'mood': 'precise, professional, innovative',
                'technical': '16:9 medical visualization, detailed, 8k quality'
            },
            'infrastructure': {
                'subject': 'server room infrastructure',
                'visual_elements': 'server racks, monitoring displays, network cables, status lights',
                'color_scheme': 'dark background, blue LED lights, orange warning lights, green status indicators',
                'lighting': 'ambient server lights, screen glow, atmospheric depth',
                'mood': 'technical, professional, critical',
                'technical': '16:9 environmental shot, detailed, 8k'
            },
            'algorithm_math': {
                'subject': 'mathematical optimization visualization',
                'visual_elements': 'geometric shapes, optimization curves, mathematical formulas, spectral patterns',
                'color_scheme': 'academic blue, white background, colorful data curves',
                'lighting': 'soft even lighting, slight gradient, academic clarity',
                'mood': 'academic, precise, innovative',
                'technical': '16:9 scientific visualization, clean, 8k'
            },
            'model_evaluation': {
                'subject': 'AI models comparison matrix',
                'visual_elements': 'evaluation grid, model icons, scoring charts, comparison arrows',
                'color_scheme': 'white background, blue accents, green for success, red for comparison',
                'lighting': 'flat professional lighting, infographic style',
                'mood': 'analytical, comparative, professional',
                'technical': '16:9 infographic design, clear layout, 8k'
            },
            'hardware_comparison': {
                'subject': 'NVIDIA CUDA GPU vs Apple Silicon chip',
                'visual_elements': 'split comparison view, GPU on left, Apple chip on right, performance graphs',
                'color_scheme': 'NVIDIA green on left, Apple silver on right, blue performance data',
                'lighting': 'dramatic product lighting, equal light on both sides, professional',
                'mood': 'competitive, technical, professional',
                'technical': '16:9 product photography, detailed, 8k'
            },
            'chinese_tech': {
                'subject': 'Chinese AI chip technology',
                'visual_elements': 'Huawei chip, circuit patterns with Chinese aesthetic, technology waves',
                'color_scheme': 'tech blue with red Chinese accents, gold details, white highlights',
                'lighting': 'national pride lighting, warm highlights, professional',
                'mood': 'innovative, independent, proud',
                'technical': '16:9 tech photography, patriotic aesthetics, 8k'
            },
            'model_architecture': {
                'subject': 'AI model orchestration architecture',
                'visual_elements': 'neural network layers, orchestration nodes, task routing paths, 8B parameters visualization',
                'color_scheme': 'NVIDIA green accents, tech blue, white connections',
                'lighting': 'tech lighting, node glow, architectural depth',
                'mood': 'organized, efficient, advanced',
                'technical': '16:9 architecture diagram, detailed, 8k'
            }
        }

        # 获取风格模板
        template = style_templates.get(topic['style'], style_templates['tech_neural_network'])

        # 组合完整提示词（按照intelligent-prompt-generator的结构）
        prompt = f"{template['subject']}, {template['visual_elements']}, {template['color_scheme']}, {template['lighting']}, {template['mood']} atmosphere, {template['technical']}, professional design, no text, clean composition"

        # 中文主题注入（Tongyi-MAI支持中文）
        chinese_description = f"主题：{topic['title']}，{topic['summary']}"

        # 最终提示词：中文主题 + 英文详细描述
        final_prompt = f"{chinese_description}。{prompt}"

        return {
            'rank': topic['rank'],
            'title': topic['title'],
            'prompt': final_prompt,
            'english_prompt': prompt,
            'chinese_theme': chinese_description,
            'template': template
        }

    def generate_image_with_api(self, prompt, output_path, max_retries=3):
        """使用 ModelScope API 生成图片"""
        for attempt in range(max_retries):
            try:
                logger.info(f"生成图片 (尝试 {attempt + 1}/{max_retries})")

                # 提交异步任务
                response = requests.post(
                    f"{self.base_url}v1/images/generations",
                    headers={**self.headers, "X-ModelScope-Async-Mode": "true"},
                    data=json.dumps({
                        "model": self.model_id,
                        "prompt": prompt
                    }, ensure_ascii=False).encode('utf-8'),
                    timeout=30
                )

                response.raise_for_status()
                task_id = response.json()["task_id"]
                logger.info(f"任务已提交: {task_id}")

                # 轮询任务状态
                max_wait_time = 120
                start_time = time.time()

                while True:
                    if time.time() - start_time > max_wait_time:
                        logger.warning("任务超时")
                        break

                    result = requests.get(
                        f"{self.base_url}v1/tasks/{task_id}",
                        headers={**self.headers, "X-ModelScope-Task-Type": "image_generation"},
                        timeout=30
                    )
                    result.raise_for_status()
                    data = result.json()

                    task_status = data.get("task_status")

                    if task_status == "SUCCEED":
                        image_url = data["output_images"][0]
                        logger.info(f"下载图片: {image_url}")

                        image_response = requests.get(image_url, timeout=30)
                        image_response.raise_for_status()

                        image = Image.open(BytesIO(image_response.content))
                        image.save(output_path)

                        logger.info(f"✅ 图片已保存: {output_path}")
                        return True

                    elif task_status == "FAILED":
                        logger.error(f"图片生成失败: {data.get('error_msg', '未知错误')}")
                        break

                    time.sleep(5)

            except Exception as e:
                logger.error(f"API请求失败: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue

        return False

    def run(self, date_str=None):
        """运行完整流程"""
        from datetime import datetime

        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        logger.info("=" * 80)
        logger.info(f"🎨 生成增强版 Top 10 AI热点图片")
        logger.info(f"📅 日期: {date_str}")
        logger.info("=" * 80)

        # 创建输出目录
        output_dir = Path(self.vault_path) / self.daily_notes_path / "images" / date_str
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存提示词文档
        prompts_doc = f"# Top 10 AI热点增强版提示词\n\n"
        prompts_doc += f"生成日期: {date_str}\n"
        prompts_doc += f"生成方法: 基于 Intelligent Prompt Generator 原则\n\n"
        prompts_doc += "---\n\n"

        success_count = 0
        all_prompts = []

        # 为每个Top项生成提示词和图片
        for topic in self.top10_topics:
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"📌 Top {topic['rank']}: {topic['title']}")
            logger.info("=" * 80)

            # 生成增强提示词
            prompt_result = self.generate_enhanced_prompt(topic)
            all_prompts.append(prompt_result)

            # 添加到文档
            prompts_doc += f"## {topic['rank']}. {topic['title']}\n\n"
            prompts_doc += f"**类别**: {topic['category']}\n\n"
            prompts_doc += f"**摘要**: {topic['summary']}\n\n"
            prompts_doc += f"**视觉风格**: {topic['style']}\n\n"

            prompts_doc += f"### 中文主题\n\n"
            prompts_doc += f"```\n{prompt_result['chinese_theme']}\n```\n\n"

            prompts_doc += f"### 英文视觉描述\n\n"
            prompts_doc += f"```\n{prompt_result['english_prompt']}\n```\n\n"

            prompts_doc += f"### 完整提示词（用于生成）\n\n"
            prompts_doc += f"```\n{prompt_result['prompt']}\n```\n\n"

            # 显示模板详情
            template = prompt_result['template']
            prompts_doc += f"### 设计规格\n\n"
            prompts_doc += f"- **主体**: {template['subject']}\n"
            prompts_doc += f"- **视觉元素**: {template['visual_elements']}\n"
            prompts_doc += f"- **配色方案**: {template['color_scheme']}\n"
            prompts_doc += f"- **光影**: {template['lighting']}\n"
            prompts_doc += f"- **氛围**: {template['mood']}\n"
            prompts_doc += f"- **技术规格**: {template['technical']}\n\n"

            # 生成图片
            image_filename = f"top{topic['rank']:02d}_{date_str}_enhanced.jpg"
            image_path = output_dir / image_filename

            logger.info(f"🎨 提示词长度: {len(prompt_result['prompt'])} 字符")

            if self.generate_image_with_api(prompt_result['prompt'], image_path):
                success_count += 1
                prompts_doc += f"### 生成的图片\n\n"
                prompts_doc += f"![Top {topic['rank']}]({image_filename})\n\n"
                logger.info(f"✅ 成功 {success_count}/{len(self.top10_topics)}")
            else:
                logger.warning(f"❌ 失败")

            prompts_doc += "---\n\n"

            # 避免请求过快
            if topic['rank'] < len(self.top10_topics):
                logger.info("⏳ 等待3秒...")
                time.sleep(3)

        # 保存提示词文档
        prompts_file = output_dir / f"enhanced_prompts_{date_str}.md"
        with open(prompts_file, 'w', encoding='utf-8') as f:
            f.write(prompts_doc)

        # 总结
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ 生成完成！")
        logger.info("=" * 80)
        logger.info(f"📊 成功率: {success_count}/{len(self.top10_topics)} ({success_count/len(self.top10_topics)*100:.1f}%)")
        logger.info(f"📄 提示词文档: {prompts_file}")
        logger.info(f"📁 图片目录: {output_dir}")
        logger.info("=" * 80)

        return all_prompts


def main():
    """主函数"""
    generator = EnhancedTop10ImageGenerator()
    generator.run()


if __name__ == "__main__":
    main()
