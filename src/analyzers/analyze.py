#!/usr/bin/env python3
"""
AI Intel Hub -- 情报分析器
读取 intel.db 中高信号条目，用 DeepSeek API 做分类、摘要、分析，结果写回 DB。

用法:
  python analyze.py              # 分析所有未处理的 signal_score >= 6 条目
  python analyze.py --dry-run    # 预览不写入
  python analyze.py --stats      # 查看分析统计
  python analyze.py --force      # 强制重新分析已分析的
  python analyze.py --limit 10   # 只处理前 N 条
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent          # ai-intel-hub/
DB_PATH = PROJECT_ROOT / "data" / "intel.db"
OPPORTUNITY_CTX = Path(os.environ.get("OPPORTUNITY_CTX_PATH", "")) or PROJECT_ROOT / "context" / "business-context.md"

# ---------------------------------------------------------------------------
# DeepSeek API
# ---------------------------------------------------------------------------
DEEPSEEK_BASE = "https://api.deepseek.com/v1"
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = "deepseek-chat"
REQUEST_TIMEOUT = 60.0
SLEEP_BETWEEN = 0.5

# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("analyze")

# ---------------------------------------------------------------------------
# DB schema migration
# ---------------------------------------------------------------------------
NEW_COLUMNS = [
    ("category", "TEXT"),
    ("ai_summary", "TEXT"),
    ("ai_analysis", "TEXT"),
    ("analyzed_at", "TEXT"),
    ("content_category", "TEXT"),
    ("content_tags", "TEXT"),
    ("topic_domain", "TEXT"),
    ("is_noise", "INTEGER DEFAULT 0"),
    ("chinese_title", "TEXT"),
]


def migrate_schema(conn: sqlite3.Connection):
    """安全地添加缺失列，SQLite 没有 IF NOT EXISTS 语法所以先查再加。"""
    cursor = conn.execute("PRAGMA table_info(intel_items)")
    existing = {row[1] for row in cursor.fetchall()}
    for col_name, col_type in NEW_COLUMNS:
        if col_name not in existing:
            conn.execute(f"ALTER TABLE intel_items ADD COLUMN {col_name} {col_type}")
            log.info("已添加列: %s %s", col_name, col_type)
    conn.commit()


# ---------------------------------------------------------------------------
# 公司上下文（opportunity 分析用）
# ---------------------------------------------------------------------------
def load_company_context() -> str:
    """读取公司业务上下文，给 opportunity 分析做背景。"""
    if OPPORTUNITY_CTX.exists():
        text = OPPORTUNITY_CTX.read_text(encoding="utf-8")
        # 截取前 2000 字，避免 prompt 过长
        if len(text) > 2000:
            text = text[:2000] + "\n...(截断)"
        return text
    return ""


COMPANY_CTX = ""  # 延迟加载


# ---------------------------------------------------------------------------
# Prompt 模板
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
你是 AI 情报分析师，负责对科技行业信号做分类、摘要和深度分析。
所有输出必须用中文撰写。英文专有名词保留原文放括号里，如"大模型（LLM）"、"OpenClaw"。
你的分析要有观点、有判断，不是复述原文。

严格遵守以下规则：
- 只基于提供的标题和摘要分析，不要脑补原文没有的信息。
- 如果你不确定事件的具体细节，必须标注"[存疑]"。不要猜测因果关系。
- 如果标题是英文，先翻译成中文，再分析。翻译时保留关键术语英文原文在括号内。"""

CLASSIFY_AND_ANALYZE_PROMPT = """\
请分析以下情报条目，完成分析任务：

## 分析规则（必须遵守）
1. 只基于下方提供的标题和摘要分析，不要脑补原文没有的信息。
2. 如果你不确定事件的具体细节，必须标注"[存疑]"。不要猜测因果关系。
3. 如果标题是英文，先翻译成中文再分析。翻译时保留关键术语英文原文在括号内。
4. 所有 summary 和 analysis 必须用中文撰写。英文专有名词保留原文放括号里，如"OpenClaw"、"Cursor"。
5. 如果原标题是英文，summary 的第一句必须用中文概述标题含义。

## 条目信息
- 标题: {title}
- 来源: {source_label}（可信度层级: T{source_tier}）
- 作者: {author}
- 平台热度: {score} 分, {comments_count} 条评论
- 信号分: {signal_score}
- 标签: {tags}
- 内容摘要:
{content_snippet}

## 任务

### 重要：用户视角
用户是 **AI PM**（产品经理），在中国数据智能公司工作，做企业信息服务产品。
用户最关注（高权重）：
1. AI 产品发布/能力变化（Claude、GPT、Gemini 等模型的产品更新）
2. AI 开发工具链（Claude Code、Cursor、Windsurf、coding agent 工具）
3. OpenClaw/OPC(One Person Company) 生态动态
4. 中国 AI 厂商产品动态（大厂发布、政策变化）
5. AI 在企业服务/B端的应用案例

用户较少关注（低权重）：
- 纯学术论文（除非有工程实践价值）
- 非 AI 领域的技术帖（Rust、Linux 内核等，除非与 AI 工具链相关）
- 个人项目/小众工具（除非是 OPC/一人公司案例）

分类时，高权重话题更倾向于 deep 或 opportunity，低权重话题倾向于 hotspot。

### 1. 分类（category）
判断属于哪一类：
- **hotspot**: AI 行业热点，大家都在聊的事
- **opportunity**: 有商业机会的方向，有人在痛、有市场
- **deep**: 值得深度解读的内容，有独特视角或重大影响
注意：signal_score >= 10 的条目自动归为 deep

### 2. 内容类型（content_category，互斥选一）
- **product_launch**: 产品发布（新产品、新版本、新功能上线）
- **tech_update**: 技术更新（框架升级、API变更、技术方案）
- **policy**: 政策法规（监管、合规、行业标准）
- **funding**: 融资并购（投资、收购、上市）
- **opinion**: 观点评论（分析文章、行业评论、预测）
- **security**: 安全事件（漏洞、攻击、数据泄露）
- **tutorial**: 教程/实践（使用指南、最佳实践、案例分享）

### 3. 内容标签（content_tags）
从标题和内容中提取关键实体作为标签，返回 JSON array。
示例: ["Claude", "OpenAI", "Cursor", "Kimi", "开源", "MCP", "Agent"]
要求: 3-8 个标签，优先提取产品名/公司名/技术概念。

### 4. 主题域（topic_domain，互斥选一）
- **ai_general**: AI 通用热点（大多数条目属于此类）
- **openclaw**: OpenClaw 生态相关（OpenClaw、Claw Hub、Skill 市场等）
- **opc**: OPC/一人公司相关（One Person Company、个人开发者创业、solo founder）

### 5. 噪音判断（is_noise）
判断这条信息对上述用户是否是噪音：
- 与5个关注主题完全无关 → true
- 过时信息（已被更新版本/事件取代，如讨论 GPT-4 而非 GPT-5.4）→ true
- 纯学术无工程实践价值 → true
- 非 AI 领域的纯技术讨论 → true
- 其他情况 → false

### 6. 中文标题（chinese_title）
为这条信息生成一个简洁有力的中文标题（15-25字）。要求：
- 不是翻译原标题，是重新提炼核心信息
- 像公众号文章标题一样吸引人但不标题党
- 关键术语保留英文，如 Claude Code、OpenClaw、Cursor
- 示例："Cursor 被发现偷用 Kimi 模型，紧急补声明"、"OpenClaw 3.12 发布：UI 大改 + 模型提速"

### 7. 中文摘要（2-3句话）
不是复述标题，而是：这件事的本质是什么、为什么重要。要有观点。
如果原标题是英文，第一句必须用中文概述。

### 8. 分析
根据分类写不同风格的分析：

如果是 **hotspot**（300-500字）：
- 这件事的背景和上下文
- "这意味着什么" -- 对行业/开发者/企业的影响
- "值得关注的点" -- 后续可能的发展方向

如果是 **opportunity**（按五步证据链格式）：
- 谁在痛？（明确用户群体和痛点场景）
- 痛多大？（量化或定性评估痛点严重程度）
- 没人解决？（现有方案的缺陷或空白）
- 我们能接住？（结合公司能力评估可行性）
- 产品化方向？（具体的产品形态建议）
{company_context_section}

如果是 **deep**（800-1500字，叙事型）：
- 钩子开头：一句话抓住读者注意力
- 核心叙事：事件全貌、关键细节、多方视角
- 独立判断：你的分析和预判，不随大流

## 输出格式
严格输出 JSON，不要其他文字：
{{"category": "hotspot|opportunity|deep", "is_noise": true/false, "chinese_title": "中文标题", "summary": "中文摘要", "analysis": "中文分析", "content_category": "product_launch|tech_update|policy|funding|opinion|security|tutorial", "content_tags": ["标签1", "标签2"], "topic_domain": "ai_general|openclaw|opc"}}

如果 is_noise 为 true，summary 写一句话说明为什么是噪音，analysis 留空字符串。"""


def build_company_section() -> str:
    """构建 opportunity prompt 中的公司上下文段落。"""
    global COMPANY_CTX
    if not COMPANY_CTX:
        COMPANY_CTX = load_company_context()
    if COMPANY_CTX:
        return f'\n\n以下是公司业务上下文，评估"我们能接住"时参考：\n```\n{COMPANY_CTX}\n```'
    return '\n（无公司上下文，请基于通用分析回答"我们能接住"）'


# ---------------------------------------------------------------------------
# DeepSeek API 调用
# ---------------------------------------------------------------------------
def call_deepseek(prompt: str, client: httpx.Client) -> dict | None:
    """调用 DeepSeek API，返回解析后的 JSON dict，失败返回 None。"""
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 2048,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(3):
        try:
            resp = client.post(
                f"{DEEPSEEK_BASE}/chat/completions",
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            # 解析 JSON
            result = json.loads(content)
            # 校验必需字段
            if all(k in result for k in ("category", "summary", "analysis")):
                # 强制校验 category 值
                if result["category"] not in ("hotspot", "opportunity", "deep"):
                    result["category"] = "hotspot"
                # 强制校验 content_category 值
                valid_cc = ("product_launch", "tech_update", "policy", "funding", "opinion", "security", "tutorial")
                if result.get("content_category") not in valid_cc:
                    result["content_category"] = "opinion"
                # 强制校验 content_tags 为列表
                if not isinstance(result.get("content_tags"), list):
                    result["content_tags"] = []
                # 强制校验 topic_domain 值
                valid_td = ("ai_general", "openclaw", "opc")
                if result.get("topic_domain") not in valid_td:
                    result["topic_domain"] = "ai_general"
                # 校验 is_noise
                result["is_noise"] = bool(result.get("is_noise", False))
                # 校验 chinese_title
                if not result.get("chinese_title"):
                    result["chinese_title"] = ""
                return result
            log.warning("返回 JSON 缺少必需字段: %s", list(result.keys()))
            return None
        except httpx.HTTPStatusError as e:
            log.warning("API HTTP %d (attempt %d/3): %s", e.response.status_code, attempt + 1, e)
            if e.response.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            return None
        except (json.JSONDecodeError, KeyError) as e:
            log.warning("解析失败 (attempt %d/3): %s", attempt + 1, e)
            if attempt < 2:
                time.sleep(1)
                continue
            return None
        except httpx.TimeoutException:
            log.warning("请求超时 (attempt %d/3)", attempt + 1)
            if attempt < 2:
                time.sleep(1)
                continue
            return None
    return None


# ---------------------------------------------------------------------------
# 主分析逻辑
# ---------------------------------------------------------------------------
def analyze_items(
    conn: sqlite3.Connection,
    dry_run: bool = False,
    force: bool = False,
    limit: int | None = None,
):
    """批量分析 intel_items。"""
    # 构建查询
    where = "signal_score >= 6"
    if not force:
        where += " AND analyzed_at IS NULL"
    query = f"SELECT id, source, source_label, source_tier, title, url, author, content_snippet, score, comments_count, signal_score, tags FROM intel_items WHERE {where} ORDER BY signal_score DESC"
    if limit:
        query += f" LIMIT {limit}"

    rows = conn.execute(query).fetchall()
    total = len(rows)

    if total == 0:
        log.info("没有需要分析的条目")
        return

    log.info("待分析条目: %d 条 (dry_run=%s, force=%s)", total, dry_run, force)

    company_section = build_company_section()
    success = 0
    failed = 0

    with httpx.Client() as client:
        for i, row in enumerate(rows, 1):
            item_id, source, source_label, source_tier, title, url, author, content_snippet, score, comments_count, signal_score, tags = row

            log.info("[%d/%d] %s (signal=%.1f) %s", i, total, source_label, signal_score, title[:60])

            # Anthropic/Claude 源自动提权
            effective_score = signal_score
            if any(kw in (title + (content_snippet or "")).lower() for kw in ['anthropic', 'claude', 'claude code', 'sonnet', 'opus', 'haiku']):
                effective_score = min(signal_score + 2, 15)

            if dry_run:
                # 预览模式：effective_score >= 10 自动 deep
                predicted = "deep" if effective_score >= 10 else "?"
                log.info("  -> [DRY-RUN] 预测分类: %s (effective_score=%.1f)", predicted, effective_score)
                continue

            # 构建 prompt
            prompt = CLASSIFY_AND_ANALYZE_PROMPT.format(
                title=title or "(无标题)",
                source_label=source_label,
                source_tier=source_tier,
                author=author or "(未知)",
                score=score or 0,
                comments_count=comments_count or 0,
                signal_score=signal_score,
                tags=tags or "[]",
                content_snippet=content_snippet or "(无摘要内容)",
                company_context_section=company_section,
            )

            result = call_deepseek(prompt, client)

            if result is None:
                log.error("  -> 分析失败，跳过")
                failed += 1
                time.sleep(SLEEP_BETWEEN)
                continue

            # effective_score >= 10 强制归 deep（含 Anthropic/Claude 提权）
            category = result["category"]
            if effective_score >= 10:
                category = "deep"

            # 噪音跳过（仍写入标记，但不做深度分析）
            is_noise = 1 if result.get("is_noise") else 0
            chinese_title = result.get("chinese_title", "") or ""

            now = datetime.now(timezone.utc).isoformat()
            content_tags_json = json.dumps(result.get("content_tags", []), ensure_ascii=False)
            conn.execute(
                """UPDATE intel_items
                   SET category = ?, ai_summary = ?, ai_analysis = ?, analyzed_at = ?,
                       content_category = ?, content_tags = ?, topic_domain = ?,
                       is_noise = ?, chinese_title = ?
                   WHERE id = ?""",
                (category, result["summary"], result["analysis"], now,
                 result.get("content_category", "opinion"),
                 content_tags_json,
                 result.get("topic_domain", "ai_general"),
                 is_noise, chinese_title,
                 item_id),
            )
            conn.commit()

            success += 1
            noise_mark = " [噪音]" if is_noise else ""
            log.info("  -> %s%s | %s | %s", category, noise_mark, chinese_title[:30] or "(无标题)", result["summary"][:40])

            time.sleep(SLEEP_BETWEEN)

    log.info("完成: 成功 %d, 失败 %d, 总计 %d", success, failed, total)


# ---------------------------------------------------------------------------
# 统计
# ---------------------------------------------------------------------------
def show_stats(conn: sqlite3.Connection):
    """显示分析统计。"""
    total = conn.execute("SELECT count(*) FROM intel_items").fetchone()[0]
    high_signal = conn.execute("SELECT count(*) FROM intel_items WHERE signal_score >= 6").fetchone()[0]
    analyzed = conn.execute("SELECT count(*) FROM intel_items WHERE analyzed_at IS NOT NULL").fetchone()[0]
    pending = conn.execute("SELECT count(*) FROM intel_items WHERE signal_score >= 6 AND analyzed_at IS NULL").fetchone()[0]

    print(f"\n{'='*50}")
    print(f"  AI Intel Hub 分析统计")
    print(f"{'='*50}")
    print(f"  条目总数:        {total}")
    print(f"  高信号(>=6):     {high_signal}")
    print(f"  已分析:          {analyzed}")
    print(f"  待分析:          {pending}")

    if analyzed > 0:
        print(f"\n  分类分布:")
        for row in conn.execute(
            "SELECT category, count(*) FROM intel_items WHERE analyzed_at IS NOT NULL GROUP BY category ORDER BY count(*) DESC"
        ):
            cat, cnt = row
            print(f"    {cat or '(空)':15s} {cnt:4d}")

        avg_len = conn.execute(
            "SELECT avg(length(ai_analysis)) FROM intel_items WHERE ai_analysis IS NOT NULL"
        ).fetchone()[0]
        print(f"\n  平均分析长度:    {avg_len:.0f} 字" if avg_len else "")

    print(f"{'='*50}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="AI Intel Hub 情报分析器")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不写入数据库")
    parser.add_argument("--stats", action="store_true", help="显示分析统计")
    parser.add_argument("--force", action="store_true", help="强制重新分析已分析的条目")
    parser.add_argument("--limit", type=int, default=None, help="只处理前 N 条")
    args = parser.parse_args()

    if not DB_PATH.exists():
        log.error("数据库不存在: %s", DB_PATH)
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    # schema migration
    migrate_schema(conn)

    if args.stats:
        show_stats(conn)
        conn.close()
        return

    analyze_items(conn, dry_run=args.dry_run, force=args.force, limit=args.limit)
    show_stats(conn)
    conn.close()


if __name__ == "__main__":
    main()
