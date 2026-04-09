# AI Intel Hub — Multi-Source AI Industry Intelligence Engine

**AI 情报引擎 — 多源 AI 行业情报自动化采集与深度分析系统**

Dual-engine architecture for automated AI industry intelligence gathering and deep analysis. Running continuously for 38+ days, producing 60+ intelligence documents.

双引擎架构，自动化采集 AI 行业情报并进行深度分析。已连续运行 38 天以上，产出 60+ 篇情报文档。

---

## Architecture / 架构

```
┌─────────────────────────────────────────────────────┐
│                   AI Intel Hub                       │
├──────────────────────┬──────────────────────────────┤
│   Engine 1           │   Engine 2                    │
│   Reddit Deep Digest │   AI Industry Daily           │
│                      │                               │
│   50+ posts/day      │   HackerNews, WeChat,         │
│   → 5+ deep themes   │   36Kr, and more              │
│   → 10,000+ word     │   → Structured daily report   │
│     long-form digest │                               │
└──────────┬───────────┴──────────────┬───────────────┘
           │                          │
           ▼                          ▼
┌─────────────────────────────────────────────────────┐
│                    Collectors                         │
│  Reddit · Twitter/X · YouTube · Jike · Xiaohongshu   │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│                    Processors                        │
│            AI Filter  ·  AI Analyzer                 │
│     (Signal scoring, categorization, summarization)  │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│                    Exporters                          │
│    Obsidian  ·  Image Generator  ·  NotebookLM       │
└─────────────────────────────────────────────────────┘
```

## Engine 1: Reddit Deep Digest / Reddit 深度摘要

Collects 50+ posts daily from 15+ AI-focused subreddits (r/MachineLearning, r/LocalLLaMA, r/OpenAI, etc.), then uses AI to extract 5+ deep themes and produce a comprehensive long-form digest (10,000+ words).

每天从 15+ 个 AI 相关 subreddit 采集 50+ 帖子，通过 AI 提取 5+ 个深度主题，产出万字长文深度解读。

## Engine 2: AI Industry Daily / AI 行业日报

Multi-source aggregation from HackerNews, WeChat public accounts, 36Kr, and other Chinese/English sources. Produces structured daily intelligence reports with categorization, scoring, and trend analysis.

多源聚合 HackerNews、微信公众号、36氪等中英文信息源，产出结构化日报，含分类、评分和趋势分析。

## Collectors / 采集器

| Collector | Source | Method |
|-----------|--------|--------|
| Reddit | r/MachineLearning, r/LocalLLaMA, etc. | RSS |
| Twitter/X | @sama, @karpathy, @AnthropicAI, etc. | RSSHub |
| YouTube | Two Minute Papers, AI Explained, etc. | RSS |
| Jike (即刻) | AI/Tech topics | RSSHub |
| Xiaohongshu (小红书) | AI keywords | RSSHub |

## Processors / 处理器

- **AI Filter**: Signal scoring (1-10) based on relevance, novelty, and impact. Only high-signal items (score >= 6) proceed to analysis.
- **AI Analyzer**: Deep categorization, summarization, key point extraction, and opportunity identification using DeepSeek/GLM models.

## Exporters / 导出器

- **Obsidian**: Atomic notes with wikilinks woven into knowledge graph
- **Image Generator**: Visual cards for top daily stories
- **NotebookLM**: Weekly podcast generation from curated intelligence

## MR Watcher / 代码审查守望者

MR Watcher is an AI-powered code review agent that monitors Pull Requests in real time and provides automated assistance throughout the review lifecycle.

MR Watcher 是一个 AI 驱动的代码审查智能体，实时监控 Pull Request 并在整个审查周期中提供自动化协助。

**Key Features / 核心功能：**

- **Auto Review / 自动审查**：PR 创建或更新时，自动分析 diff 并发现潜在问题（格式、逻辑、安全风险）
- **CI Monitor / CI 监控**：监听 CI 状态，失败时自动分析错误日志并建议修复方案
- **Comment Response / 评论响应**：响应 reviewer 评论，按要求自动修复代码并推送
- **Smart Notification / 智能通知**：重要事件（CI 失败、被 approve、需要修改）自动邮件通知作者
- **Code Fix / 代码修复**：对于明确的修改请求，直接在分支上修复代码并提交

**Workflow / 工作流：**

```
PR Event (comment / CI / push)
        │
        ▼
  MR Watcher Agent
        │
        ├─→ Analyze & Summarize (分析摘要)
        ├─→ Post Comment (回复评论)
        ├─→ Fix Code (修复代码)
        └─→ Notify Author (通知作者)
```

## Quick Start / 快速开始

### 1. Clone and setup

```bash
git clone https://github.com/AmoryMing/ai-intel-hub.git
cd ai-intel-hub
python -m venv venv
source venv/bin/activate
pip install -r src/hotspot/requirements.txt
```

### 2. Configure environment

```bash
cp src/hotspot/config/.env.example .env
# Edit .env with your API keys:
#   DEEPSEEK_API_KEY=your-key
#   GLM_API_KEY=your-key
#   ANTHROPIC_API_KEY=your-key  (optional, for Claude-based analysis)
```

### 3. Configure sources

Edit `src/hotspot/config/config.yaml` to customize:
- Subreddits, YouTube channels, Twitter accounts
- AI keyword filters
- Scoring thresholds
- Output paths

### 4. Run

```bash
# Collect intelligence
python src/collectors/collect.py

# Analyze collected data
python src/analyzers/analyze.py

# Weave into knowledge base
python src/weaver/weave.py
```

### 5. Automate (optional)

```bash
# Add to crontab for daily collection at 9:00 AM
crontab -e
0 9 * * * cd /path/to/ai-intel-hub && bash src/cron_collect.sh
```

## Tech Stack / 技术栈

- **Language**: Python 3.10+
- **Collectors**: RSS/RSSHub-based multi-source crawlers
- **AI Models**: DeepSeek, GLM (ZhipuAI), Claude (optional)
- **Storage**: SQLite (intel.db)
- **Knowledge Base**: Obsidian-compatible Markdown with wikilinks
- **Hot API**: [DailyHot API](https://github.com/imsyy/DailyHotApi) (bundled, for Chinese sources)

## Project Structure / 项目结构

```
ai-intel-hub/
├── src/
│   ├── collectors/       # Multi-source data collectors
│   ├── analyzers/        # AI-powered analysis pipeline
│   ├── weaver/           # Knowledge base integration
│   ├── hotspot/          # Reddit Deep Digest engine
│   ├── dailyhot-api/     # Chinese hot topics API
│   ├── dashboard/        # Monitoring dashboard
│   └── cron_collect.sh   # Automation script
├── context/              # Design docs and changelogs
├── config.yaml           # Source configuration
└── README.md
```

## License / 许可证

[Apache License 2.0](LICENSE)

Copyright 2026 Ming Mu (AmoryMing)
