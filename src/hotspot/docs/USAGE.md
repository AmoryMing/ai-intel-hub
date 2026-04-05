# Usage Guide

Learn how to use the AI Hotspot Daily Report skill to generate automated AI news reports.

## Table of Contents

- [Quick Start](#quick-start)
- [Basic Usage](#basic-usage)
- [Advanced Usage](#advanced-usage)
- [Understanding the Output](#understanding-the-output)
- [Customization](#customization)
- [Automation](#automation)
- [Best Practices](#best-practices)

---

## Quick Start

### Simplest Usage

In Claude Code, just ask:

```
请使用 ai-hotspot-dailyreport skill 生成今天的日报
```

Or in English:
```
Use the ai-hotspot-dailyreport skill to generate today's report
```

That's it! Claude will handle everything automatically.

---

## Basic Usage

### Step-by-Step Workflow

When you invoke the skill, Claude will:

1. **Check existing data** (per skill's "When to Skip Steps" logic)
2. **Activate virtual environment** (`source venv/bin/activate`)
3. **Collect data** (`python3 main.py --hours 24`)
   - Scrapes Reddit AI subreddits
   - Collects YouTube AI videos
   - Filters by AI keywords
   - ~5 minutes
4. **Generate images** (`python3 generate_enhanced_top10.py`)
   - Creates 10 professional images
   - Uses Intelligent Prompt Generator principles
   - ~8 minutes
5. **Verify output** in Obsidian vault

**Total time**: ~15 minutes

### What You'll See

Claude will provide progress updates:

```
✅ 数据收集完成: 241条AI热点
✅ AI分析完成: 中文摘要已生成
✅ Top 10提取完成
✅ 图片生成中... (1/10)
...
✅ 图片生成完成: 10/10 (100% success)
✅ 文档更新完成
```

---

## Advanced Usage

### Manual Execution (Without Skill)

If you prefer to run commands manually:

```bash
# Navigate to project
cd /Users/zhuyansen/Project/AiWriting/ai-hotspot-collector

# Activate virtual environment
source venv/bin/activate

# Step 1: Collect data
python3 main.py --hours 24

# Step 2: Generate images
python3 generate_enhanced_top10.py

# Done! Check Obsidian vault
```

### Custom Time Windows

Collect data from different time periods:

```bash
# Last 12 hours
python3 main.py --hours 12

# Last 48 hours
python3 main.py --hours 48

# Last week
python3 main.py --hours 168
```

### Regenerate Images Only

If you want to regenerate images with different styles:

```bash
# Regenerate all 10 images
python3 generate_enhanced_top10.py

# Regenerate specific date
python3 generate_enhanced_top10.py --date 2026-01-14

# Regenerate only first 3 (for testing)
python3 generate_enhanced_top10.py --limit 3
```

### Skip AI Analysis (Faster)

If Claude API is slow or expensive:

```bash
# Collect data without AI summaries
python3 main.py --hours 24 --no-ai-analysis

# Data will still be collected, but summaries will be empty
# Faster and cheaper, but lower quality
```

### Export Only

If data is already collected, just regenerate reports:

```bash
python3 main.py --export-only
```

---

## Understanding the Output

### File Structure

After running, you'll find:

```
Obsidian Vault/AI-Hotspots/Daily/
├── 2026-01-15.md                          # Main report
├── 2026-01-15-Top10总结.md                # Top 10 summary
├── 🎉-完成报告-2026-01-15.md              # Completion report
├── 🎨-增强版图片生成报告-2026-01-15.md    # Image generation report
└── images/2026-01-15/
    ├── top01_2026-01-15_enhanced.jpg
    ├── top02_2026-01-15_enhanced.jpg
    ├── ... (10 images total)
    ├── enhanced_prompts_2026-01-15.md
    └── prompts_2026-01-15.md
```

### Main Report (2026-01-15.md)

**Size**: ~151KB, ~4000 lines

**Content**:
- YAML frontmatter with metadata
- Daily overview statistics
- 241 AI hotspots organized by category:
  - 🤖 AI 模型发布和更新 (71%)
  - 🛠️ AI 应用和工具 (16%)
  - 🏢 AI 公司动态 (11%)
  - 💻 AI 硬件 (2%)

**Each item includes**:
- Title and source
- Heat score (⭐⭐⭐) and engagement (👍💬)
- Sentiment (😊😐😔)
- AI-generated Chinese summary
- 5 key points (JSON format)
- Original link

**Example**:
```markdown
### NVIDIA: End-to-End Test-Time Training

- **来源**: Reddit - r/MachineLearning
- **热度**: ⭐⭐⭐ 👍 245 | 💬 89
- **情感**: 😊 positive
- **AI 摘要**: 英伟达提出测试时训练技术，可在推理过程中实时更新模型权重。

**关键点**:
- 实时更新模型权重
- 上下文窗口作为训练数据集
- 测试时训练范式
- 快速权重更新循环
- 元学习优化可更新性

**链接**: [查看原文](https://reddit.com/...)
```

### Top 10 Summary (2026-01-15-Top10总结.md)

**Size**: ~8KB

**Content**:
- Data overview statistics
- Detailed analysis of Top 10 items
- Embedded images (professional visuals)
- Trend analysis
- Category distribution

**Example**:
```markdown
### 1️⃣ NVIDIA端到端测试时训练 (TTT)

**标题**: Nvidia: End-to-End Test-Time Training

**关键信息**:
- 🎯 **核心突破**: 实时更新模型权重学习上下文
- 💡 **技术原理**: 将上下文窗口作为训练数据集
- 🔬 **意义**: 从"检索信息"转向"实时学习"

![NVIDIA TTT](images/2026-01-15/top01_2026-01-15_enhanced.jpg)
```

### Generated Images

**Quality**:
- Format: JPG
- Size: 47KB - 136KB per image
- Resolution: High (8K quality specified in prompts)
- Aspect Ratio: 16:9 horizontal
- Style: Professional, AI-themed

**Image Types**:
1. **Neural Network Visualizations** - For AI model topics
2. **Hardware Photography** - For GPU/chip topics
3. **Medical AI Interfaces** - For healthcare topics
4. **Chinese Tech Aesthetics** - For domestic tech topics
5. **Algorithm Visualizations** - For optimization topics

---

## Customization

### Customize Data Sources

Edit `config/config.yaml`:

```yaml
sources:
  reddit:
    enabled: true
    subreddits:
      - "MachineLearning"
      - "LocalLLaMA"
      - "OpenAI"
      - "ClaudeAI"        # Add your own
      - "StableDiffusion" # Add your own
    min_score: 50  # Minimum upvotes

  youtube:
    enabled: true
    channels:
      - "UCbfYPyITQ-7l4upoX8nvctg"  # Two Minute Papers
      # Add more channels
```

### Customize AI Keywords

Filter collected items by keywords:

```yaml
filters:
  ai_keywords:
    - "AI"
    - "GPT"
    - "Claude"
    - "LLM"
    - "machine learning"
    - "deep learning"
    - "neural network"
    # Add your own keywords
```

### Customize Image Styles

Edit `generate_enhanced_top10.py` to add your own style templates:

```python
style_templates = {
    'your_custom_style': {
        'subject': 'Your visual subject',
        'visual_elements': 'Specific elements to include',
        'color_scheme': 'Color palette description',
        'lighting': 'Lighting setup',
        'mood': 'Desired atmosphere',
        'technical': '16:9, 8k, professional render'
    }
}
```

### Customize Categories

Edit `config/config.yaml`:

```yaml
categories:
  - name: "AI 模型发布和更新"
    keywords: ["model", "release", "GPT", "Claude"]

  - name: "Your Custom Category"
    keywords: ["your", "keywords"]
```

---

## Automation

### Daily Cron Job (macOS/Linux)

Set up automatic daily reports:

```bash
# Edit crontab
crontab -e

# Add this line (runs at 8 AM daily)
0 8 * * * cd /path/to/ai-hotspot-collector && source venv/bin/activate && python3 main.py --hours 24 && python3 generate_enhanced_top10.py
```

### Weekly Summary

Generate weekly digest:

```bash
# Every Sunday at 9 AM
0 9 * * 0 cd /path/to/ai-hotspot-collector && source venv/bin/activate && python3 main.py --hours 168 --weekly
```

### Notifications

Get notified when report is ready:

```bash
# macOS notification
python3 main.py --hours 24 && osascript -e 'display notification "AI报告已生成" with title "AI Hotspot Report"'

# Email notification (requires mail setup)
python3 main.py --hours 24 && echo "Report ready" | mail -s "AI Report" your@email.com
```

---

## Best Practices

### 1. Regular Collection

**Recommended**: Generate reports daily
- Captures trending discussions
- Prevents data loss (Reddit scores change)
- Builds historical archive

### 2. Review Before Sharing

**Always check**:
- AI summaries for accuracy
- Image quality and relevance
- Links are working
- No sensitive information

### 3. Backup Your Data

```bash
# Backup Obsidian vault
cp -r "/Users/yourusername/Documents/Obsidian Vault/AI-Hotspots" ~/Backups/

# Or use git
cd "/Users/yourusername/Documents/Obsidian Vault"
git init
git add AI-Hotspots/
git commit -m "Backup AI hotspots"
```

### 4. Monitor API Costs

Track your usage:

```bash
# Anthropic: Check console.anthropic.com/usage
# ModelScope: Check modelscope.cn dashboard

# Estimate costs:
# - Data collection: Free (RSS)
# - AI analysis: ~$0.01-0.05 per report
# - Image generation: ~¥0.01-0.05 per image
# Total: ~$0.15-0.30 per daily report
```

### 5. Handle Failures Gracefully

If collection fails:

```bash
# Check logs
tail -100 logs/collector.log

# Retry with smaller window
python3 main.py --hours 12

# Skip problematic sources
# Edit config.yaml: reddit.enabled: false
```

### 6. Version Control Your Config

```bash
cd ai-hotspot-collector
git init
git add config/config.yaml
git commit -m "My custom configuration"

# Exclude secrets
echo "config/.env" >> .gitignore
```

---

## Examples

### Example 1: Weekend Digest

Generate a comprehensive weekend report:

```bash
# Monday morning, collect last 72 hours
python3 main.py --hours 72
python3 generate_enhanced_top10.py
```

### Example 2: Topic-Specific Report

Focus on specific topics:

```bash
# Edit config.yaml to only include specific subreddits
subreddits: ["StableDiffusion", "comfyui"]

# Run collection
python3 main.py --hours 24
```

### Example 3: Quick Check

Fast collection without images:

```bash
# Quick data collection only
python3 main.py --hours 6 --no-ai-analysis

# Review in terminal
tail -100 /path/to/obsidian/vault/YYYY-MM-DD.md
```

---

## Troubleshooting

### Issue: No Data Collected

**Check**:
- Internet connection
- Reddit/YouTube are accessible
- Time window isn't too narrow
- Keywords aren't too restrictive

### Issue: Images Not Generating

**Check**:
- ModelScope API key is valid
- `generate_enhanced_top10.py` exists
- Prompts aren't too long (>500 chars)
- Network can reach ModelScope servers

### Issue: Obsidian Not Updating

**Check**:
- Obsidian vault path is correct
- Permissions allow writing
- Obsidian is set to auto-refresh
- Files are in correct directory

---

## Next Steps

- ✅ [Customize your configuration](INSTALLATION.md#step-3-configure-api-keys)
- ✅ Set up automation with cron
- ✅ Explore advanced features
- ✅ Share your reports (with attribution)

---

**Happy reporting! 🎉**

For questions or issues, see [GitHub Issues](https://github.com/yourusername/ai-hotspot-dailyreport-skill/issues).
