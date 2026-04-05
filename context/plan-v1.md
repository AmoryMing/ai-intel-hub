# AI 情报中枢 (AI Intel Hub) -- 渐进式实施计划

> 一个面板看全貌，cron 自动跑，内容自动发小红书和B站。

## 愿景

把散落的 5 块情报能力（热点采集、深度分析、商机雷达、商业情报、信息过滤）合并为一个**统一的 AI 情报中枢**：

```
信息源（RSS/搜索/API）
    ↓ 采集层（定时自动）
原始素材池（SQLite）
    ↓ 分析层（Claude AI）
结构化情报（热点/深度/商机）
    ↓ 展示层
统一 Dashboard（浏览器）
    ↓ 分发层
小红书 + B站（自动/半自动发布）
```

## 已有资产清单

| 编号 | 资产 | 位置 | 能力 | 在中枢中的角色 |
|------|------|------|------|--------------|
| A1 | ai-hotspot-dailyreport | GitHub(外部) | RSS采集+Claude分析+ModelScope配图 | **采集层** -- 每日抓热点 |
| A2 | /ai-industry-intel-digest | skill | 搜索→筛选→叙事型深度分析 | **分析层** -- 深度解读 |
| A3 | /intel | skill | 市场动态→证据链→产品推荐 | **分析层** -- 商机挖掘 |
| A4 | BizRadar | vault/project/bizradar | 商机卡片+Dashboard+DB | **展示层参考** -- 面板设计 |
| A5 | info-filter | vault/project/info-filter | 信息过滤+Flask app | **过滤层参考** |

## GitHub 零件清单（不重复造轮子）

| 零件 | Stars | 层 | 用途 |
|------|-------|-----|------|
| **RSSHub** | 42.8K | 采集 | 万能 RSS 生成器，任何网站变 RSS |
| **DailyHotApi** | 3.7K | 采集 | 60+ 平台热榜聚合 API，可 Vercel 部署 |
| **DailyHot** | 878 | 面板 | DailyHotApi 配套前端，开箱即用热榜 Dashboard |
| **wewe-rss** | 9.0K | 采集 | 微信公众号 → RSS |
| **ai-news-aggregator** | 181 | 采集 | 80+ AI/科技 RSS 源，专注 AI 领域 |
| **Horizon** | 879 | 分析 | AI 新闻聚合+中英双语摘要生成 |
| **github-trending** | 831 | 采集 | Python 版 GitHub Trending 爬虫 |
| **github-trending-repos** | 2.9K | 采集 | Trending → GitHub Actions 定时推通知 |
| **star-history** | 8.7K | 可视化 | Star 增长曲线，可嵌入 |
| **biliup** | 5.0K | 发布 | B 站命令行投稿（Python） |
| **MediaCrawler** | 46.3K | 参考 | 国内主流平台爬虫（小红书/B站/微博） |
| **github-trending-scraper** | 1 | 参考 | 抓 Trending → 渲染卡片 → Gemini 生成小红书文案（完整链路） |

**推荐组合**: RSSHub(数据源) + DailyHotApi(聚合) + DailyHot(面板) + biliup(B站发布)，中间 AI 分析层用自有 Claude API。

## Phase 0 结论（2026-03-21 已完成）

跑了 ai-hotspot-dailyreport，结论：**不整体用，拆零件。**
- 232 条 Reddit 无差别采集，大部分是杂音
- AI 摘要质量可用（haiku），但信息源不对——用户有自己的精选源体系
- 详见 `voice/评估-hotspot-skill.md`

**关键转向**: 采集层不用别人的广撒网，而是**自动化用户已有的精选源体系**（/ai-industry-intel-digest 的 Tier 0/1/2 源）。

## 阶段划分（Phase 0 后修订）

---

### Phase 1: 自动化精选源采集 + 最小面板

**目标**: 把 /ai-industry-intel-digest 的 Tier 0/1/2 信息源自动化抓取，灌进 Dashboard。

| 步骤 | 动作 |
|------|------|
| 1.1 | 写采集脚本：自动抓 Tier 0/1 源（HN API、Reddit JSON、官方博客 RSS） |
| 1.2 | AI 筛选：用 GLM/DeepSeek 按信号强度评分框架打分，只留 6 分以上 |
| 1.3 | 统一数据模型（SQLite），存原文+摘要+评分 |
| 1.4 | 改 BizRadar 面板，加"今日情报"tab |
| 1.5 | 配 cron 每日自动跑 |

**信息源（直接复用 /ai-industry-intel-digest 的定义）**：
- **Tier 0**: OpenAI/Anthropic 博客、Karpathy、Simon Willison、HN 首页、r/LocalLLaMA
- **Tier 1**: DeepMind/Google AI/Meta AI 博客、Lilian Weng、r/MachineLearning、量子位、机器之心
- **Tier 2**: 36kr、HuggingFace、r/artificial（有事件时查）

**Phase 1 产出**: localhost 打开能看到今天精选的 5-10 条高质量 AI 情报。

---

### Phase 2: 三流合一 -- 热点+情报+商机

**目标**: 把 /ai-industry-intel-digest 和 /intel 的产出也灌进同一个面板。

| 步骤 | 动作 |
|------|------|
| 2.1 | 统一情报数据模型：type=hotspot/deep-analysis/opportunity |
| 2.2 | /ai-industry-intel-digest 产出写入 DB（分析层适配器） |
| 2.3 | /intel 产出写入 DB（商机层适配器） |
| 2.4 | Dashboard 增加三栏视图：热点 / 深度 / 商机 |
| 2.5 | 增加时间轴视图：按日期看全部情报 |

**Phase 2 产出**: 一个面板看三类情报，每类有独立入口和时间线。

---

### Phase 3: 内容工厂 -- 自动生成发布素材

**目标**: 从情报自动生成小红书/B站可发布的内容。

| 步骤 | 动作 |
|------|------|
| 3.1 | 定义内容模板：小红书图文（封面+正文+标签）、B站文章/视频脚本 |
| 3.2 | 写内容生成器：情报 → Claude → 平台适配格式 |
| 3.3 | 小红书：生成封面图（标题+配图叠加）+ 正文（800字以内）+ 话题标签 |
| 3.4 | B站：生成专栏文章 或 视频脚本（配合 TTS） |
| 3.5 | Dashboard 增加「内容预览」tab，一键复制/导出 |

**Phase 3 产出**: 每条情报自动生成 2 套发布素材（小红书+B站），人工审核后发布。

---

### Phase 4: 半自动发布 -- 审核后一键发

**目标**: 在面板上审核内容，点击发布。

| 步骤 | 动作 |
|------|------|
| 4.1 | 调研小红书/B站发布 API 或自动化方案（Playwright/官方API） |
| 4.2 | 实现发布接口（优先小红书，B站次之） |
| 4.3 | Dashboard 增加「审核→发布」工作流 |
| 4.4 | 发布记录入库，防重发 |

**Phase 4 产出**: 面板上看内容→改→发，发布状态可追踪。

---

### Phase 5: 全自动飞轮 -- cron 端到端

**目标**: 全链路自动化，人只需要偶尔审核。

| 步骤 | 动作 |
|------|------|
| 5.1 | cron: 每日 7:00 采集 → 8:00 分析 → 9:00 生成内容 |
| 5.2 | 桌面通知：「今日 X 条情报已就绪，Y 条内容待审核」 |
| 5.3 | 自动发布低风险内容（纯热点转述），高风险内容（观点型）人工审核 |
| 5.4 | 数据反馈：小红书/B站阅读量回流，优化选题策略 |

**Phase 5 产出**: 每天早上收到通知，打开面板扫一眼，点几下发布，10分钟搞定。

---

## 目录规划

项目自治，代码+知识+产出放一起。

```
vault/1-knowledge/project/ai-intel-hub/
├── context/                    ← 计划、评估、决策
│   └── plan-v1.md
├── output/                     ← 各阶段产出物
├── voice/                      ← 用户判断、评估笔记
├── src/                        ← 所有代码
│   ├── hotspot/                ← Phase 0: clone 的外部项目
│   ├── collectors/             ← Phase 1: 采集适配器
│   ├── analyzers/              ← Phase 2: 分析适配器
│   ├── generators/             ← Phase 3: 内容生成器
│   ├── publishers/             ← Phase 4: 发布接口
│   └── dashboard/              ← Phase 1+: 统一面板
└── data/                       ← SQLite 数据库
```

## 风险与决策点

| 风险 | 影响 | 缓解 |
|------|------|------|
| hotspot-skill 产出质量差 | Phase 0 就能发现，不影响后续 | 自己写采集器替代 |
| 小红书/B站反爬严格 | Phase 4 发布受阻 | 降级为导出素材手动发布 |
| Claude API 成本 | 每日跑全链路 ~$0.5-1 | 缓存+增量分析+按需触发 |
| ModelScope 图片质量不稳定 | 封面图不可用 | 换 FLUX/Midjourney API |
| 信息源偏英文（Reddit/YouTube） | 中文受众水土不服 | Phase 2 加中文源（微博/知乎/即刻） |

## 成功标准

- **Phase 0**: 能产出一份可读的 AI 日报
- **Phase 1**: 每天打开面板就能看到今日热点
- **Phase 2**: 一个面板覆盖热点+深度+商机三条线
- **Phase 3**: 每条情报自动生成可发布素材
- **Phase 4**: 面板上点击即发布
- **Phase 5**: 每天 10 分钟完成全部情报工作

## 和 BizRadar 的关系

BizRadar 专注「商机」赛道，是 AI Intel Hub 的一个子集。Phase 2 时 BizRadar 的商机数据灌入统一面板，BizRadar 本身可以继续独立运行，也可以逐步合并。不急着合，先跑通再说。
