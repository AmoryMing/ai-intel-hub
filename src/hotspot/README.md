# 🔥 AI Hotspot Daily Report

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![TDD](https://img.shields.io/badge/Methodology-TDD-green)](docs/TDD-COMPLETION-REPORT.md)

> **Automated AI news collection, analysis, and professional visualization in 15 minutes.**

Collect 200+ AI hotspots from Reddit & YouTube → Analyze with Claude AI → Generate professional images → Export to Obsidian.

**⚡ One-command setup. Two API keys. Zero manual work.**

[English](#english) | [中文](#chinese)

---

## English

### 🎯 What It Does

```
Input: None (fully automated)
  ↓
Collect 200+ AI news from Reddit & YouTube (RSS feeds)
  ↓
Analyze with Claude AI (summaries, key points, sentiment)
  ↓
Generate 10 professional images (ModelScope API)
  ↓
Output: Complete Obsidian markdown reports (~15 min)
```

### ✨ Features

- 🤖 **Automated Collection**: 241+ items from 15 AI subreddits + YouTube
- 🧠 **AI Analysis**: Claude generates Chinese summaries & key points
- 📊 **Structured Reports**: Obsidian-formatted markdown, categorized
- 🎨 **Professional Images**: 10 high-quality visuals with Intelligent Prompt Generator
- ⚡ **100% Automation**: 2 commands, ~15 minutes, done
- ✅ **TDD-Tested**: 100% behavioral improvement verified

### 🚀 Quick Start (5 Minutes)

#### Prerequisites

- Python 3.8+ installed ([Download](https://www.python.org/downloads/))
- 2 API Keys (5 minutes to get):
  - **Anthropic**: [console.anthropic.com](https://console.anthropic.com) → API Keys
  - **ModelScope**: [modelscope.cn](https://modelscope.cn) → Profile → API Tokens

#### Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/ai-hotspot-dailyreport-skill.git
cd ai-hotspot-dailyreport-skill

# 2. Run automatic setup
./setup.sh

# 3. Add your API keys
nano config/.env
# Set ANTHROPIC_API_KEY=sk-ant-api03-...
# Set MODELSCOPE_API_KEY=...

# 4. Generate your first report!
source venv/bin/activate
python3 main.py --hours 24
python3 generate_enhanced_top10.py
```

**Done!** Check `~/Documents/Obsidian Vault/AI-Hotspots/Daily/` for your report.

### 📦 What You Get

```
~/Documents/Obsidian Vault/AI-Hotspots/Daily/
├── 2026-01-16.md                       # 📄 Complete report (241 items)
├── 2026-01-16-Top10总结.md             # 🏆 Top 10 highlights
├── 🎨-增强版图片生成报告-2026-01-16.md # 📊 Image report
└── images/2026-01-16/
    ├── top01_2026-01-16_enhanced.jpg   # 🎨 10 professional
    ├── top02_2026-01-16_enhanced.jpg   #    images (8K quality,
    └── ... (10 images total)           #    16:9, Chinese titles)
```

**Example Output:**
- **241 AI hotspots** collected and analyzed
- **10 professional images** with Intelligent Prompt Generator
- **~4000 lines** of structured markdown
- **100% success rate** on image generation

### 📊 Performance

| Metric | Result |
|--------|--------|
| **Data collected** | 241 items from Reddit/YouTube |
| **AI analysis** | 100% automated (Claude API) |
| **Image generation** | 100% success (10/10) |
| **Total time** | ~15 minutes |
| **Cost per report** | ~$0.15-0.30 (APIs) |

### 🎨 Image Quality

All images generated using **Intelligent Prompt Generator v2.0**:

![Example Output 1](images/example-output-01.jpg)
*NVIDIA Test-Time Training visualization*

![Example Output 2](images/example-output-02.jpg)
*Zhipu AI domestic chip breakthrough*

**Features:**
- ✅ Complete structure (subject + color + lighting + mood + technical)
- ✅ Semantic consistency (unified style)
- ✅ Bilingual prompts (Chinese theme + English description)
- ✅ 8K quality, 16:9 aspect ratio

### 🛠️ Usage

#### Basic Usage

```bash
# Activate environment
source venv/bin/activate

# Collect last 24 hours
python3 main.py --hours 24

# Generate images for Top 10
python3 generate_enhanced_top10.py

# Check output in Obsidian
```

#### Advanced Options

```bash
# Collect last 48 hours
python3 main.py --hours 48

# Regenerate images for specific date
python3 generate_enhanced_top10.py --date 2026-01-15

# Test with 3 images only
python3 generate_enhanced_top10.py --limit 3

# Skip AI analysis (faster, cheaper)
python3 main.py --hours 24 --no-ai-analysis
```

#### With Claude Code (Optional)

If you have [Claude Code](https://claude.ai/claude-code) installed:

```
请使用 ai-hotspot-dailyreport skill 生成今天的日报
```

Claude will run all commands automatically.

### 📖 Documentation

- **[INSTALLATION.md](docs/INSTALLATION.md)** - Detailed setup guide
- **[USAGE.md](docs/USAGE.md)** - Complete usage instructions
- **[TDD-COMPLETION-REPORT.md](docs/TDD-COMPLETION-REPORT.md)** - Testing methodology
- **[Configuration Examples](examples/)** - Customize your setup

### 🔧 Customization

Edit `config/config.example.yaml` to customize:

- **Data sources**: Add more subreddits or YouTube channels
- **AI keywords**: Filter by custom keywords
- **Categories**: Define your own categorization
- **Image styles**: Add custom style templates
- **Output format**: Customize markdown structure

See [examples/README.md](examples/README.md) for configuration examples.

### 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

### 🐛 Issues & Support

- **Bug reports**: [GitHub Issues](https://github.com/yourusername/ai-hotspot-dailyreport-skill/issues)
- **Questions**: [GitHub Discussions](https://github.com/yourusername/ai-hotspot-dailyreport-skill/discussions)
- **Documentation**: [docs/](docs/)

### 📄 License

MIT License - see [LICENSE](LICENSE) file.

### 🙏 Acknowledgments

- Built with [Claude Code](https://claude.ai/claude-code)
- AI analysis by [Anthropic Claude](https://anthropic.com)
- Images by [ModelScope](https://modelscope.cn)
- Tested with TDD methodology

---

## Chinese

<a name="chinese"></a>

### 🎯 功能说明

```
输入：无（全自动）
  ↓
从 Reddit 和 YouTube 收集 200+ AI 新闻（RSS 订阅）
  ↓
使用 Claude AI 分析（摘要、关键点、情感）
  ↓
生成 10 张专业配图（ModelScope API）
  ↓
输出：完整的 Obsidian Markdown 报告（~15 分钟）
```

### ✨ 功能特性

- 🤖 **自动收集**: 从 15 个 AI 子版块 + YouTube 收集 241+ 条目
- 🧠 **AI 分析**: Claude 生成中文摘要和关键点
- 📊 **结构化报告**: Obsidian 格式的 Markdown，自动分类
- 🎨 **专业配图**: 10 张高质量图片（Intelligent Prompt Generator）
- ⚡ **100% 自动化**: 2 条命令，~15 分钟完成
- ✅ **TDD 测试**: 经过验证，100% 行为改进

### 🚀 快速开始（5 分钟）

#### 前置条件

- 已安装 Python 3.8+（[下载](https://www.python.org/downloads/)）
- 2 个 API 密钥（5 分钟获取）：
  - **Anthropic**: [console.anthropic.com](https://console.anthropic.com) → API Keys
  - **ModelScope**: [modelscope.cn](https://modelscope.cn) → 个人中心 → API令牌

#### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/ai-hotspot-dailyreport-skill.git
cd ai-hotspot-dailyreport-skill

# 2. 运行自动安装脚本
./setup.sh

# 3. 添加您的 API 密钥
nano config/.env
# 设置 ANTHROPIC_API_KEY=sk-ant-api03-...
# 设置 MODELSCOPE_API_KEY=...

# 4. 生成您的第一份报告！
source venv/bin/activate
python3 main.py --hours 24
python3 generate_enhanced_top10.py
```

**完成！** 在 `~/Documents/Obsidian Vault/AI-Hotspots/Daily/` 查看报告。

### 📦 生成内容

```
~/Documents/Obsidian Vault/AI-Hotspots/Daily/
├── 2026-01-16.md                       # 📄 完整报告（241 条）
├── 2026-01-16-Top10总结.md             # 🏆 Top 10 亮点
├── 🎨-增强版图片生成报告-2026-01-16.md # 📊 图片报告
└── images/2026-01-16/
    ├── top01_2026-01-16_enhanced.jpg   # 🎨 10 张专业图片
    ├── top02_2026-01-16_enhanced.jpg   #    （8K 质量，
    └── ...（共 10 张图片）              #     16:9，中文标题）
```

**示例输出：**
- **241 条 AI 热点** 已收集和分析
- **10 张专业图片** 使用 Intelligent Prompt Generator
- **~4000 行** 结构化 Markdown
- **100% 成功率** 图片生成

### 📊 性能指标

| 指标 | 结果 |
|------|------|
| **数据收集** | 241 条（Reddit/YouTube）|
| **AI 分析** | 100% 自动化（Claude API）|
| **图片生成** | 100% 成功（10/10）|
| **总耗时** | ~15 分钟 |
| **每份报告成本** | ~¥1-2（API）|

### 🎨 图片质量

所有图片使用 **Intelligent Prompt Generator v2.0** 生成：

![示例输出 1](images/example-output-01.jpg)
*NVIDIA 测试时训练可视化*

![示例输出 2](images/example-output-02.jpg)
*智谱 AI 国产芯片突破*

**特点：**
- ✅ 结构完整（主体 + 配色 + 光影 + 氛围 + 技术）
- ✅ 语义一致（风格统一）
- ✅ 双语提示词（中文主题 + 英文描述）
- ✅ 8K 质量，16:9 横版

### 🛠️ 使用方法

#### 基础用法

```bash
# 激活环境
source venv/bin/activate

# 收集最近 24 小时
python3 main.py --hours 24

# 为 Top 10 生成图片
python3 generate_enhanced_top10.py

# 在 Obsidian 中查看输出
```

#### 高级选项

```bash
# 收集最近 48 小时
python3 main.py --hours 48

# 重新生成特定日期的图片
python3 generate_enhanced_top10.py --date 2026-01-15

# 仅测试生成 3 张图片
python3 generate_enhanced_top10.py --limit 3

# 跳过 AI 分析（更快、更便宜）
python3 main.py --hours 24 --no-ai-analysis
```

#### 使用 Claude Code（可选）

如果已安装 [Claude Code](https://claude.ai/claude-code)：

```
请使用 ai-hotspot-dailyreport skill 生成今天的日报
```

Claude 会自动运行所有命令。

### 📖 文档

- **[INSTALLATION.md](docs/INSTALLATION.md)** - 详细安装指南
- **[USAGE.md](docs/USAGE.md)** - 完整使用说明
- **[TDD-COMPLETION-REPORT.md](docs/TDD-COMPLETION-REPORT.md)** - 测试方法论
- **[配置示例](examples/)** - 自定义配置

### 🔧 自定义

编辑 `config/config.example.yaml` 以自定义：

- **数据源**: 添加更多子版块或 YouTube 频道
- **AI 关键词**: 按自定义关键词过滤
- **分类**: 定义您自己的分类
- **图片风格**: 添加自定义风格模板
- **输出格式**: 自定义 Markdown 结构

详见 [examples/README.md](examples/README.md)。

### 🤝 贡献

欢迎贡献！请：

1. Fork 仓库
2. 创建功能分支（`git checkout -b feature/amazing`）
3. 提交更改（`git commit -m '添加很棒的功能'`）
4. 推送到分支（`git push origin feature/amazing`）
5. 打开 Pull Request

### 🐛 问题与支持

- **错误报告**: [GitHub Issues](https://github.com/yourusername/ai-hotspot-dailyreport-skill/issues)
- **问题讨论**: [GitHub Discussions](https://github.com/yourusername/ai-hotspot-dailyreport-skill/discussions)
- **文档**: [docs/](docs/)

### 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

### 🙏 致谢

- 使用 [Claude Code](https://claude.ai/claude-code) 构建
- AI 分析由 [Anthropic Claude](https://anthropic.com) 提供
- 图片生成由 [ModelScope](https://modelscope.cn) 提供
- 使用 TDD 方法论测试

---

**⭐ Star this repo if you find it helpful!**

**快速链接**: [安装](docs/INSTALLATION.md) | [使用](docs/USAGE.md) | [示例](examples/) | [Issues](https://github.com/yourusername/ai-hotspot-dailyreport-skill/issues)
