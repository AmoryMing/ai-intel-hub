# Example Configuration

This directory contains example configuration files for the AI Hotspot Collector.

## config.example.yaml

Example configuration for data collection:

```yaml
# Data Sources Configuration
sources:
  # Reddit Configuration
  reddit:
    enabled: true
    use_rss: true  # Use RSS instead of API (no key needed)
    subreddits:
      - "MachineLearning"
      - "LocalLLaMA"
      - "OpenAI"
      - "ClaudeAI"
      - "ArtificialInteligence"
      - "singularity"
      - "StableDiffusion"
      - "ChatGPT"
      - "Bard"
      - "learnmachinelearning"
      - "deeplearning"
      - "LanguageTechnology"
      - "computervision"
      - "reinforcementlearning"
      - "datasets"
    min_score: 50  # Minimum upvotes to include

  # YouTube Configuration
  youtube:
    enabled: true
    use_rss: true  # Use RSS feeds
    channels:
      - "UCbfYPyITQ-7l4upoX8nvctg"  # Two Minute Papers
      - "UCUHW94eEFW7hkUMVaZz4eDg"  # Yannic Kilcher
      # Add more channel IDs

# AI Keywords Filter
filters:
  ai_keywords:
    - "AI"
    - "GPT"
    - "Claude"
    - "LLM"
    - "machine learning"
    - "deep learning"
    - "neural network"
    - "transformer"
    - "diffusion"
    - "reinforcement learning"
    - "人工智能"
    - "大模型"
    - "机器学习"

# AI Analysis Configuration
ai_analysis:
  enabled: true
  provider: "anthropic"  # Use Claude
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 1024
  temperature: 0.7

  # Prompts
  summary_prompt: |
    请用中文总结以下AI相关内容，提取关键点：

    标题: {title}
    来源: {source}
    内容: {content}

    请提供：
    1. 一句话概括（20字以内）
    2. 3-5个关键点（每个10字以内）
    3. 重要性评分（1-5星）

# Categories
categories:
  - name: "AI 模型发布和更新"
    keywords: ["model", "release", "GPT", "Claude", "LLaMA", "训练", "发布"]

  - name: "AI 应用和工具"
    keywords: ["tool", "application", "app", "应用", "工具"]

  - name: "AI 公司动态"
    keywords: ["company", "startup", "acquisition", "公司", "融资"]

  - name: "AI 硬件"
    keywords: ["GPU", "TPU", "chip", "hardware", "芯片", "硬件"]

# Obsidian Export Configuration
obsidian:
  enabled: true
  vault_path: "/Users/yourusername/Documents/Obsidian Vault"
  daily_notes_path: "AI-Hotspots/Daily"
  auto_create_folders: true

  # Document template
  template:
    include_toc: true
    include_stats: true
    include_top10: true

# Image Generation Configuration
image_generation:
  enabled: true
  provider: "modelscope"
  model: "Tongyi-MAI/Z-Image-Turbo"

  # Style templates (see generate_enhanced_top10.py)
  default_styles:
    - "tech_neural_network"
    - "gpu_hardware"
    - "medical_ai"
    - "chinese_tech"
    - "algorithm_math"

  # Image settings
  aspect_ratio: "16:9"
  quality: "high"
  output_format: "jpg"

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "logs/collector.log"
  max_size: "10MB"
  backup_count: 5
```

## .env.example

Example environment variables:

```bash
# Anthropic API Key (Required)
# Get from: https://console.anthropic.com
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# ModelScope API Key (Required)
# Get from: https://modelscope.cn
MODELSCOPE_API_KEY=your-modelscope-token-here

# Optional: Custom Obsidian Vault Path
# If not set, will auto-detect
OBSIDIAN_VAULT_PATH=/Users/yourusername/Documents/Obsidian Vault/AI-Hotspots/Daily/

# Optional: Proxy Settings (if behind corporate firewall)
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
```

## Setup Instructions

1. Copy this file to your collector project:
```bash
cp examples/config.example.yaml /path/to/ai-hotspot-collector/config/config.yaml
```

2. Copy environment file:
```bash
cp examples/.env.example /path/to/ai-hotspot-collector/config/.env
```

3. Edit with your values:
```bash
nano /path/to/ai-hotspot-collector/config/.env
# Add your API keys

nano /path/to/ai-hotspot-collector/config/config.yaml
# Customize sources and settings
```

4. Secure your keys:
```bash
chmod 600 /path/to/ai-hotspot-collector/config/.env
```

## Common Customizations

### Add More Subreddits

```yaml
sources:
  reddit:
    subreddits:
      - "YourSubreddit"  # Add here
```

### Change Collection Time

In your command:
```bash
python3 main.py --hours 48  # Last 48 hours
```

### Disable AI Analysis (Faster/Cheaper)

```yaml
ai_analysis:
  enabled: false
```

Or use flag:
```bash
python3 main.py --hours 24 --no-ai-analysis
```

### Change Output Language

Edit prompts in config:
```yaml
ai_analysis:
  summary_prompt: |
    Please summarize in English...  # Change to English
```
