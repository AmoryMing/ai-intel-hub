#!/usr/bin/env python3
"""
AI Intel Hub -- 知识编织器
Phase 1 核心：把精选情报编织进 vault 知识架构。

流程：
  1. 从 intel.db 读今日精选情报（signal_score >= 6）
  2. GLM 分类到知识域（ai-frontier / competitor / opportunity / ...）
  3. grep vault/ 找相关文件，生成 wikilink
  4. DeepSeek 生成原子笔记（带关联 + 解读）
  5. 写入 vault 对应目录
  6. 生成每日索引 vault/05_Inbox/daily-intel-{date}.md

用法：
  python weave.py                # 编织今日情报
  python weave.py --date 2026-03-21  # 编织指定日期
  python weave.py --dry-run      # 只打印，不写文件
"""

import argparse
import json
import logging
import os
import re
import sqlite3
import subprocess
import time
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Optional

import httpx

# ---------- 配置 ----------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "intel.db"
VAULT_ROOT = PROJECT_ROOT.parent.parent.parent  # vault/

# 知识域映射
DOMAINS = {
    "ai-frontier": "AI 前沿技术（模型发布、能力突破、架构演进、Agent、MCP）",
    "competitor": "竞品动态（OpenClaw、Coze、各大厂 AI 产品）",
    "opportunity": "商机信号（市场变化、新需求、可落地机会）",
    "product-lab": "产品形态（新产品、交互模式、用户体验）",
    "methodology": "方法论（工程实践、PM方法、AI工作流）",
    "writing": "内容与传播（SEOGEO、自媒体、内容策略）",
}

# API 配置
GLM_API_KEY = os.environ.get("GLM_API_KEY", "")
GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("weaver")

# ---------- AI 调用 ----------

def call_llm(prompt: str, system: str = "", provider: str = "deepseek") -> str:
    """调用 LLM，返回文本。provider: glm / deepseek"""
    if provider == "glm":
        url = f"{GLM_BASE_URL}/chat/completions"
        headers = {"Authorization": f"Bearer {GLM_API_KEY}", "Content-Type": "application/json"}
        model = "glm-4-flash"
    else:
        url = f"{DEEPSEEK_BASE_URL}/chat/completions"
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        model = "deepseek-chat"

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = {"model": model, "messages": messages, "temperature": 0.3, "max_tokens": 1500}

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log.error(f"LLM 调用失败 ({provider}): {e}")
        return ""


# ---------- 分类 ----------

def classify_domain(title: str, snippet: str) -> str:
    """用 GLM 判断情报属于哪个知识域。"""
    domain_desc = "\n".join(f"- {k}: {v}" for k, v in DOMAINS.items())
    prompt = f"""请判断以下 AI 情报属于哪个知识域，只返回域名（如 ai-frontier），不要其他内容。

知识域：
{domain_desc}

标题：{title}
摘要：{snippet[:300]}

域名："""
    result = call_llm(prompt, provider="glm").strip().lower()
    # 清理可能的额外文本
    for domain in DOMAINS:
        if domain in result:
            return domain
    return "ai-frontier"  # 默认


# ---------- vault 关联搜索 ----------

def find_related_files(title: str, snippet: str, domain: str, top_n: int = 3) -> list[dict]:
    """在 vault 中搜索相关文件，返回 [{path, name, relevance}]"""
    # 提取关键词
    text = f"{title} {snippet}"
    # 去掉常见停用词，保留有意义的词
    keywords = set()
    for word in re.findall(r'[A-Za-z]{3,}|[\u4e00-\u9fff]{2,}', text):
        if word.lower() not in {"the", "and", "for", "with", "this", "that", "from", "are", "was", "has", "have", "not", "but", "can", "will"}:
            keywords.add(word)

    if not keywords:
        return []

    # 用 grep 在 vault 的知识库目录中搜索
    search_dirs = [
        str(VAULT_ROOT / "1-knowledge"),
        str(VAULT_ROOT / "2-memory"),
    ]

    found_files = {}  # path -> match_count

    for kw in list(keywords)[:8]:  # 限制关键词数量
        for search_dir in search_dirs:
            if not Path(search_dir).exists():
                continue
            try:
                result = subprocess.run(
                    ["grep", "-ril", "--include=*.md", kw, search_dir],
                    capture_output=True, text=True, timeout=5
                )
                for path in result.stdout.strip().split("\n"):
                    if path and path.endswith(".md"):
                        # 排除自身产出的 intel 文件
                        if "/intel-2" in path or "/daily-intel-" in path:
                            continue
                        found_files[path] = found_files.get(path, 0) + 1
            except (subprocess.TimeoutExpired, Exception):
                continue

    # 按匹配次数排序，取 top N
    sorted_files = sorted(found_files.items(), key=lambda x: -x[1])[:top_n]

    results = []
    for filepath, count in sorted_files:
        p = Path(filepath)
        # 读首行作为摘要
        try:
            first_lines = p.read_text(encoding="utf-8", errors="ignore").strip().split("\n")
            # 跳过 frontmatter
            summary = ""
            in_frontmatter = False
            for line in first_lines[:20]:
                if line.strip() == "---":
                    in_frontmatter = not in_frontmatter
                    continue
                if not in_frontmatter and line.strip() and not line.startswith("#"):
                    summary = line.strip()[:100]
                    break
                if not in_frontmatter and line.startswith("# "):
                    summary = line.replace("# ", "").strip()[:100]
                    break
        except Exception:
            summary = ""

        # 转为 vault 相对路径（用于 wikilink）
        rel = p.relative_to(VAULT_ROOT)
        name = p.stem  # 不带扩展名的文件名

        results.append({
            "path": str(rel),
            "name": name,
            "summary": summary,
            "match_count": count,
        })

    return results


# ---------- 原子笔记生成 ----------

def generate_note(item: dict, domain: str, related: list[dict]) -> str:
    """用 DeepSeek 生成原子笔记。"""
    related_context = ""
    if related:
        related_context = "已有相关知识：\n"
        for r in related:
            related_context += f"- [[{r['name']}]]: {r['summary']}\n"

    prompt = f"""你是 AI PM 的知识助手。请根据以下情报生成一篇原子笔记。

要求：
1. 首行必须是你的判断/观点（不是复述事实）
2. 用中文写，关键术语保留英文
3. wikilink 用 [[文件名]] 格式
4. 总长度 200-500 字
5. "我的看法"部分要结合已有知识给出对 AI PM 的实操建议

情报：
标题：{item['title']}
来源：{item['source_label']}（Tier {item['source_tier']}）
URL：{item.get('url', '')}
摘要：{item.get('content_snippet', '')[:400]}
信号强度：{item.get('signal_score', 0)}

{related_context}

请按以下格式输出（不要输出 frontmatter，我会自动加）：

{{一句话判断}}

## 事件

{{2-3 句描述发生了什么}}

## 关联

{{列出 wikilink 和关联理由，每条一行}}

## 我的看法

{{基于已有知识的解读，这对 AI PM 意味着什么，该怎么反应}}"""

    return call_llm(prompt, system="你是一个 AI 行业资深分析师，擅长从碎片信息中提炼结构化洞察。", provider="deepseek")


def make_frontmatter(item: dict, domain: str) -> str:
    """生成 frontmatter"""
    tags = ["ai-intel", domain]
    return f"""---
source: {item.get('source_label', '')}
url: {item.get('url', '')}
signal_score: {item.get('signal_score', 0)}
date: {date.today().isoformat()}
tags: {json.dumps(tags, ensure_ascii=False)}
---

"""


def make_slug(title: str) -> str:
    """从标题生成文件名 slug"""
    # 取英文单词或中文
    words = re.findall(r'[a-zA-Z0-9]+|[\u4e00-\u9fff]+', title)
    slug = "-".join(words[:6]).lower()
    return slug[:60] if slug else "untitled"


# ---------- 每日索引 ----------

def generate_index(today: str, notes: list[dict]) -> str:
    """生成每日索引文件内容"""
    deep = [n for n in notes if n["score"] >= 10]
    standard = [n for n in notes if 6 <= n["score"] < 10]

    # 按域统计
    domain_counts = {}
    for n in notes:
        d = n["domain"]
        domain_counts[d] = domain_counts.get(d, 0) + 1

    lines = [
        f"# AI 情报 | {today}",
        "",
        f"今日编织 {len(notes)} 条情报，深度级 {len(deep)} 条。",
        "",
    ]

    if deep:
        lines.append("## 深度级（10 分+）")
        for n in deep:
            lines.append(f"- [[{n['filename']}]] -- {n['title'][:60]}")
        lines.append("")

    if standard:
        lines.append("## 标准级（6-9 分）")
        for n in standard:
            lines.append(f"- [[{n['filename']}]] -- {n['title'][:60]}")
        lines.append("")

    if domain_counts:
        lines.append("## 知识架构更新")
        for d, cnt in sorted(domain_counts.items(), key=lambda x: -x[1]):
            lines.append(f"- {d}/: +{cnt} 篇")
        lines.append("")

    return "\n".join(lines)


# ---------- 主流程 ----------

def run_weave(target_date: Optional[str] = None, dry_run: bool = False):
    """主流程：编织今日情报"""
    if not DB_PATH.exists():
        log.error(f"数据库不存在: {DB_PATH}")
        return

    today = target_date or date.today().isoformat()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # 读取精选情报
    rows = conn.execute("""
        SELECT * FROM intel_items
        WHERE signal_score >= 6
        AND collected_at LIKE ?
        ORDER BY signal_score DESC
        LIMIT 15
    """, (f"{today}%",)).fetchall()

    if not rows:
        # 如果按 collected_at 没找到，试试不带日期过滤（取最新的）
        rows = conn.execute("""
            SELECT * FROM intel_items
            WHERE signal_score >= 6
            ORDER BY signal_score DESC
            LIMIT 15
        """).fetchall()
        log.info(f"今日无数据，取最新 {len(rows)} 条精选情报")

    log.info(f"精选情报: {len(rows)} 条 (score >= 6)")

    woven_notes = []

    for i, row in enumerate(rows):
        item = dict(row)
        title = item.get("title", "")
        snippet = item.get("content_snippet", "")

        log.info(f"[{i+1}/{len(rows)}] [{item.get('signal_score', 0)}] {title[:50]}...")

        # 1. 分类
        domain = classify_domain(title, snippet)
        log.info(f"  域: {domain}")

        # 2. 关联搜索
        related = find_related_files(title, snippet, domain)
        if related:
            log.info(f"  关联: {', '.join(r['name'][:30] for r in related)}")

        # 3. 生成笔记
        note_body = generate_note(item, domain, related)
        if not note_body:
            log.warning(f"  笔记生成失败，跳过")
            continue

        frontmatter = make_frontmatter(item, domain)
        full_note = frontmatter + note_body

        # 4. 写入文件
        slug = make_slug(title)
        filename = f"intel-{today}-{slug}"
        domain_dir = VAULT_ROOT / "1-knowledge" / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        filepath = domain_dir / f"{filename}.md"

        if dry_run:
            log.info(f"  [DRY RUN] 会写入: {filepath.relative_to(VAULT_ROOT)}")
            log.info(f"  笔记前 100 字: {note_body[:100]}...")
        else:
            filepath.write_text(full_note, encoding="utf-8")
            log.info(f"  写入: {filepath.relative_to(VAULT_ROOT)}")

        woven_notes.append({
            "filename": filename,
            "title": title,
            "domain": domain,
            "score": item.get("signal_score", 0),
            "path": str(filepath.relative_to(VAULT_ROOT)),
        })

        # 控制速率
        time.sleep(0.5)

    conn.close()

    # 5. 生成每日索引
    if woven_notes:
        index_content = generate_index(today, woven_notes)
        inbox_dir = VAULT_ROOT / "05_Inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)
        index_path = inbox_dir / f"daily-intel-{today}.md"

        if dry_run:
            log.info(f"[DRY RUN] 索引会写入: {index_path.relative_to(VAULT_ROOT)}")
            print("\n" + index_content)
        else:
            index_path.write_text(index_content, encoding="utf-8")
            log.info(f"索引写入: {index_path.relative_to(VAULT_ROOT)}")

    log.info(f"编织完成: {len(woven_notes)} 条笔记, {len(set(n['domain'] for n in woven_notes))} 个域")
    return woven_notes


def main():
    parser = argparse.ArgumentParser(description="AI Intel Hub 知识编织器")
    parser.add_argument("--date", type=str, help="指定日期 (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="只打印不写文件")
    args = parser.parse_args()

    log.info("=" * 50)
    log.info("知识编织器启动")
    log.info("=" * 50)

    t0 = time.time()
    notes = run_weave(target_date=args.date, dry_run=args.dry_run)
    elapsed = time.time() - t0

    log.info(f"总耗时: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
