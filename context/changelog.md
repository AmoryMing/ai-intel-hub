# AI Intel Hub Changelog

## 2026-03-22 深夜大重建

### collect.py -- 信息源重建
- **从 14 源 → 21 源**，按用户真实阅读习惯校准
- 新增 Tier 0: Anthropic Blog、GitHub Trending AI、OpenClaw Releases
- 新增 Tier 1: 新智元/36kr、Cursor Blog、OpenClaw 动态、OPC 一人公司
- Simon Willison/Karpathy 从 T0 降到 T1，DeepMind/Google AI 从 T1 降到 T2
- 原因：用户反馈"这些东西对我帮助不大"，信息源和实际消费严重脱节
- Anthropic Blog RSS (`rss.xml`) 返回 404，需要找正确 URL

### analyze.py -- v3 大升级
- **噪音过滤**：新增 `is_noise` 字段，不相关内容标记为噪音
- **中文标题生成**：新增 `chinese_title` 字段，AI 生成 15-25 字中文标题（不再用英文原文第一句）
- **content_category**：7 种内容类型（product_launch/tech_update/policy/funding/opinion/security/tutorial）
- **content_tags**：JSON array 实体标签（3-8 个）
- **topic_domain**：ai_general/openclaw/opc 主题域
- **PM 视角权重**：高权重=OpenClaw+Claude+Coding Agent，低权重=纯学术/非AI
- **Anthropic/Claude 提权**：相关内容 signal_score 自动 +2
- **准确性规则**：不确定标注 [存疑]，不脑补原文没有的信息
- 原因：Kimi/Cursor 事件解读错误导致用户信任崩塌；卡片标题是英文第一句看不懂

### app.py -- Dashboard 单页面板（v2）
- **从 Tab 切换 → 单页 Dashboard**
- 左 60% AI 热点流 + 右 40% OpenClaw/OPC 专题
- 筛选栏：Category 下拉 + Tag 多选 + Domain + 搜索
- 信号标签：数字改为"重要"/"关注"
- Category 彩色标签
- 底部：商机发现 + 发布就绪（"复制到小红书"按钮）
- 相对时间戳（"3小时前"）
- 日间 Notion 主题
- 新增 /api/filters 端点
- 原因：用户说"5个Tab层级混乱"，面板思维 > 论坛思维

### claw_changelog.py -- 新建
- Claw 生态动态追踪器
- GitHub Releases（Claude Code 5 个 release）
- Brave Search（8 个方向 × 5 条 = 40 条新闻）
- 75 条事件写入 claw-ecosystem-data.json
- 原因：用户说"厂商卡片不是静态的，要 changelog"

### 根因修复
- **面板空了一周的原因**：app.py 读 vault markdown 文件（不存在），不读 intel.db（有 279 条数据）
- 修复：app.py 直接读 intel.db

### 参考项目
- 克隆 worldmonitor 到 tmp/worldmonitor/
- tech 变体可跑（localhost:3004），但 RSS 需要代理支持
- 用途：UI 参考 + 信息源列表参考，不做深度融合

### Memory 更新
- 新建 feedback_intel-hub-content-calibration.md（用户真实信息源 + 关注主题权重）
- 新建 feedback_changelog-required.md（每次改动必须记录 changelog）
- 更新 project_ai-intel-hub.md（全面重写，反映新架构）
