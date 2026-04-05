#!/usr/bin/env python3
"""
AI Intel Hub -- Phase 1.1 采集脚本
自动抓取 Tier 0/1/2 信息源，存入 SQLite。

信息源按用户实际关注主题排序:
  OpenClaw 生态 (~40%) | Claude/Anthropic (~25%) | Coding Agent 工具链 (~15%)
  AI 产品/商业 (~10%) | AI 技术前沿 (~10%)

  Tier 0 (必采): Anthropic 博客/新闻, GitHub Trending AI, HN, OpenClaw Releases,
                  r/LocalLLaMA, OpenAI 博客
  Tier 1 (每日): 量子位, 机器之心, 新智元/36kr, Cursor, Simon Willison, Karpathy,
                  OpenClaw 动态, OPC 一人公司, r/MachineLearning
  Tier 2 (按需): Ethan Mollick, Lilian Weng, DeepMind, Google AI, Meta AI

用法:
  python collect.py              # 采集全部
  python collect.py --tier 0     # 只采 Tier 0
  python collect.py --source hn  # 只采 HN
  python collect.py --stats      # 查看统计
"""

import argparse
import hashlib
import json
import logging
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from html.parser import HTMLParser

import feedparser
import httpx

# ---------- 配置 ----------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "intel.db"
PROXY = "http://127.0.0.1:7890"
REQUEST_TIMEOUT = 20  # 秒
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
BRAVE_API_KEY = "BSAxiCxnkEt6VA8O11gVKQgXJ6oHRnu"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("collector")

# ---------- 信息源注册表 ----------

SOURCES = {
    # ========== Tier 0 -- 必采（每条都有价值） ==========

    # Claude/Anthropic 官方
    "anthropic_blog": {
        "tier": 0, "type": "rss", "label": "Anthropic Blog",
        "url": "https://www.anthropic.com/rss.xml",
        "needs_proxy": True,
    },
    "anthropic_news": {
        "tier": 0, "type": "html_anthropic", "label": "Anthropic News",
        "url": "https://www.anthropic.com/news",
        "needs_proxy": True,
    },

    # GitHub Trending AI
    "github_trending": {
        "tier": 0, "type": "brave_search", "label": "GitHub Trending AI",
        "url": "https://api.search.brave.com/res/v1/web/search",
        "brave_query": "github trending AI agent LLM",
        "needs_proxy": True,
    },

    # Hacker News
    "hn": {
        "tier": 0, "type": "api", "label": "Hacker News",
        "url": "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=30",
        "needs_proxy": False,
    },

    # OpenClaw -- 用户最关注的主题
    "openclaw_releases": {
        "tier": 0, "type": "rss", "label": "OpenClaw Releases",
        "url": "https://github.com/anthropics/claude-code/releases.atom",
        "needs_proxy": True,
    },

    # Reddit
    "r_locallama": {
        "tier": 0, "type": "reddit", "label": "r/LocalLLaMA",
        "url": "https://www.reddit.com/r/LocalLLaMA/hot.json?limit=25",
        "needs_proxy": True,
    },

    # OpenAI 官方
    "openai_blog": {
        "tier": 0, "type": "rss", "label": "OpenAI Blog",
        "url": "https://openai.com/blog/rss.xml",
        "needs_proxy": True,
    },

    # ========== Tier 1 -- 高价值（每日扫描） ==========

    # 中文源
    "qbitai": {
        "tier": 1, "type": "brave_search", "label": "量子位",
        "url": "https://api.search.brave.com/res/v1/web/search",
        "brave_query": "site:qbitai.com",
        "needs_proxy": True,
    },
    "jiqizhixin": {
        "tier": 1, "type": "brave_search", "label": "机器之心",
        "url": "https://api.search.brave.com/res/v1/web/search",
        "brave_query": "site:jiqizhixin.com/articles",
        "needs_proxy": True,
    },
    "xinzhiyuan": {
        "tier": 1, "type": "brave_search", "label": "新智元",
        "url": "https://api.search.brave.com/res/v1/web/search",
        "brave_query": "site:36kr.com AI agent OpenClaw Claude",
        "needs_proxy": True,
    },

    # Coding Agent 生态
    "cursor_blog": {
        "tier": 1, "type": "brave_search", "label": "Cursor Blog",
        "url": "https://api.search.brave.com/res/v1/web/search",
        "brave_query": "site:cursor.com blog OR changelog",
        "needs_proxy": True,
    },

    # 个人博客 -- 高质量
    "simon_willison": {
        "tier": 1, "type": "rss", "label": "Simon Willison",
        "url": "https://simonwillison.net/atom/everything/",
        "needs_proxy": True,
    },
    "karpathy": {
        "tier": 1, "type": "rss", "label": "Karpathy Blog",
        "url": "http://karpathy.github.io/feed.xml",
        "needs_proxy": True,
    },

    # OpenClaw 生态搜索
    "openclaw_news": {
        "tier": 1, "type": "brave_search", "label": "OpenClaw 动态",
        "url": "https://api.search.brave.com/res/v1/web/search",
        "brave_query": "OpenClaw OR \"claude code\" update release changelog 2026",
        "needs_proxy": True,
    },
    "opc_news": {
        "tier": 1, "type": "brave_search", "label": "OPC 一人公司",
        "url": "https://api.search.brave.com/res/v1/web/search",
        "brave_query": "一人公司 OR \"one person company\" AI agent solopreneur 2026",
        "needs_proxy": True,
    },

    # Reddit
    "r_ml": {
        "tier": 1, "type": "reddit", "label": "r/MachineLearning",
        "url": "https://www.reddit.com/r/MachineLearning/hot.json?limit=25",
        "needs_proxy": True,
    },

    # ========== Tier 2 -- 补充（按需） ==========

    # AI Practitioner blogs
    "ethan_mollick": {
        "tier": 2, "type": "rss", "label": "Ethan Mollick",
        "url": "https://www.oneusefulthing.org/feed",
        "needs_proxy": True,
    },
    "lilian_weng": {
        "tier": 2, "type": "rss", "label": "Lilian Weng",
        "url": "https://lilianweng.github.io/index.xml",
        "needs_proxy": True,
    },

    # 大厂博客
    "deepmind": {
        "tier": 2, "type": "rss", "label": "DeepMind Blog",
        "url": "https://deepmind.google/blog/rss.xml",
        "needs_proxy": True,
    },
    "google_ai": {
        "tier": 2, "type": "rss", "label": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "needs_proxy": True,
    },
    "meta_ai": {
        "tier": 2, "type": "brave_search", "label": "Meta AI Blog",
        "url": "https://api.search.brave.com/res/v1/web/search",
        "brave_query": "site:ai.meta.com/blog",
        "needs_proxy": True,
    },
}

# ---------- DB ----------

def init_db():
    """创建 SQLite 表。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS intel_items (
            id            TEXT PRIMARY KEY,   -- sha256(source + url)
            source        TEXT NOT NULL,      -- 源 key，如 hn / r_locallama
            source_label  TEXT NOT NULL,      -- 人读名，如 Hacker News
            source_tier   INTEGER NOT NULL,   -- 0 / 1 / 2
            title         TEXT NOT NULL,
            url           TEXT,
            author        TEXT,
            content_snippet TEXT,             -- 前 500 字摘要
            published_at  TEXT,               -- ISO8601
            collected_at  TEXT NOT NULL,       -- ISO8601
            score         INTEGER DEFAULT 0,  -- 源平台分数（upvotes 等）
            comments_count INTEGER DEFAULT 0,
            signal_score  REAL DEFAULT 0,      -- 信号强度评分（0-15）
            tags          TEXT DEFAULT '[]'    -- JSON array
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON intel_items(source)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tier ON intel_items(source_tier)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_collected ON intel_items(collected_at)")
    conn.commit()
    return conn


def item_id(source: str, url: str) -> str:
    return hashlib.sha256(f"{source}:{url}".encode()).hexdigest()[:16]


def upsert(conn: sqlite3.Connection, item: dict):
    """插入或跳过（已存在则不更新）。"""
    conn.execute("""
        INSERT OR IGNORE INTO intel_items
        (id, source, source_label, source_tier, title, url, author,
         content_snippet, published_at, collected_at, score, comments_count, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item["id"], item["source"], item["source_label"], item["source_tier"],
        item["title"], item.get("url"), item.get("author"),
        item.get("content_snippet", "")[:500],
        item.get("published_at"), item["collected_at"],
        item.get("score", 0), item.get("comments_count", 0),
        json.dumps(item.get("tags", []), ensure_ascii=False),
    ))


# ---------- HTTP ----------

def get_client(needs_proxy: bool) -> httpx.Client:
    kwargs = {
        "timeout": REQUEST_TIMEOUT,
        "headers": {"User-Agent": USER_AGENT},
        "follow_redirects": True,
    }
    if needs_proxy:
        kwargs["proxy"] = PROXY
    return httpx.Client(**kwargs)


def fetch(url: str, needs_proxy: bool) -> Optional[httpx.Response]:
    """GET with error handling, returns None on failure."""
    try:
        with get_client(needs_proxy) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp
    except Exception as e:
        log.warning(f"采集失败 {url}: {e}")
        return None


# ---------- HTML 文本提取 ----------

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._text = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            t = data.strip()
            if t:
                self._text.append(t)

    def get_text(self) -> str:
        return " ".join(self._text)


def html_to_text(html: str) -> str:
    p = TextExtractor()
    p.feed(html)
    return p.get_text()


# ---------- 采集器 ----------

def collect_hn(conn: sqlite3.Connection) -> int:
    """Hacker News 首页 Top 30。"""
    src = SOURCES["hn"]
    resp = fetch(src["url"], src["needs_proxy"])
    if not resp:
        return 0
    data = resp.json()
    now = datetime.now(timezone.utc).isoformat()
    count = 0
    for hit in data.get("hits", []):
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
        item = {
            "id": item_id("hn", url),
            "source": "hn",
            "source_label": src["label"],
            "source_tier": 0,
            "title": hit.get("title", ""),
            "url": url,
            "author": hit.get("author", ""),
            "content_snippet": hit.get("story_text", "") or "",
            "published_at": hit.get("created_at", ""),
            "collected_at": now,
            "score": hit.get("points", 0),
            "comments_count": hit.get("num_comments", 0),
            "tags": hit.get("_tags", []),
        }
        upsert(conn, item)
        count += 1
    conn.commit()
    return count


def collect_reddit(conn: sqlite3.Connection, source_key: str) -> int:
    """Reddit subreddit hot posts。"""
    src = SOURCES[source_key]
    resp = fetch(src["url"], src["needs_proxy"])
    if not resp:
        return 0
    data = resp.json()
    now = datetime.now(timezone.utc).isoformat()
    count = 0
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        if post.get("stickied"):
            continue
        url = post.get("url", "")
        item = {
            "id": item_id(source_key, url),
            "source": source_key,
            "source_label": src["label"],
            "source_tier": src["tier"],
            "title": post.get("title", ""),
            "url": url,
            "author": post.get("author", ""),
            "content_snippet": (post.get("selftext", "") or "")[:500],
            "published_at": datetime.fromtimestamp(
                post.get("created_utc", 0), tz=timezone.utc
            ).isoformat() if post.get("created_utc") else "",
            "collected_at": now,
            "score": post.get("score", 0),
            "comments_count": post.get("num_comments", 0),
            "tags": [post.get("link_flair_text", "")] if post.get("link_flair_text") else [],
        }
        upsert(conn, item)
        count += 1
    conn.commit()
    return count


def collect_rss(conn: sqlite3.Connection, source_key: str) -> int:
    """RSS/Atom feed 采集。"""
    src = SOURCES[source_key]
    resp = fetch(src["url"], src["needs_proxy"])
    if not resp:
        return 0
    feed = feedparser.parse(resp.text)
    now = datetime.now(timezone.utc).isoformat()
    count = 0
    for entry in feed.entries[:20]:
        url = entry.get("link", "")
        # 提取发布时间
        pub = ""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            pub = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc).isoformat()
        # 提取摘要
        snippet = ""
        if hasattr(entry, "summary"):
            snippet = html_to_text(entry.summary)
        elif hasattr(entry, "content") and entry.content:
            snippet = html_to_text(entry.content[0].get("value", ""))

        item = {
            "id": item_id(source_key, url),
            "source": source_key,
            "source_label": src["label"],
            "source_tier": src["tier"],
            "title": entry.get("title", ""),
            "url": url,
            "author": entry.get("author", ""),
            "content_snippet": snippet[:500],
            "published_at": pub,
            "collected_at": now,
            "score": 0,
            "comments_count": 0,
            "tags": [t.get("term", "") for t in getattr(entry, "tags", [])],
        }
        upsert(conn, item)
        count += 1
    conn.commit()
    return count


def collect_html_anthropic(conn: sqlite3.Connection, source_key: str) -> int:
    """Anthropic /news 页 HTML 抓取。"""
    src = SOURCES[source_key]
    resp = fetch(src["url"], src["needs_proxy"])
    if not resp:
        return 0

    html = resp.text
    now = datetime.now(timezone.utc).isoformat()
    count = 0

    # 提取 /news/slug 链接
    links = re.findall(r'href="(/news/[a-z0-9-]+)"', html)
    unique = list(dict.fromkeys(links))

    # 提取日期（格式如 "Mar 12, 2026"）
    date_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4})'
    dates_in_page = re.findall(date_pattern, html)

    for i, path in enumerate(unique[:20]):
        url = f"https://www.anthropic.com{path}"
        # slug 转标题: "claude-sonnet-4-6" → "Claude Sonnet 4 6"
        slug = path.replace("/news/", "")
        title = slug.replace("-", " ").title()
        # 尝试匹配日期
        pub = ""
        if i < len(dates_in_page):
            try:
                pub = datetime.strptime(dates_in_page[i], "%b %d, %Y").replace(
                    tzinfo=timezone.utc
                ).isoformat()
            except ValueError:
                pass

        item = {
            "id": item_id(source_key, url),
            "source": source_key,
            "source_label": src["label"],
            "source_tier": src["tier"],
            "title": title,
            "url": url,
            "author": "Anthropic",
            "content_snippet": "",
            "published_at": pub,
            "collected_at": now,
            "score": 0,
            "comments_count": 0,
            "tags": [],
        }
        upsert(conn, item)
        count += 1

    conn.commit()
    return count


def collect_brave_search(conn: sqlite3.Connection, source_key: str) -> int:
    """Brave Search API 采集（用于 SPA 站点兜底）。"""
    src = SOURCES[source_key]
    query = src["brave_query"]
    now = datetime.now(timezone.utc).isoformat()

    params = {
        "q": query,
        "count": 20,
    }
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY,
        "User-Agent": USER_AGENT,
    }

    try:
        with get_client(needs_proxy=True) as client:
            resp = client.get(src["url"], params=params, headers=headers)
            resp.raise_for_status()
    except Exception as e:
        log.warning(f"Brave Search 失败 [{source_key}]: {e}")
        return 0

    data = resp.json()
    results = data.get("web", {}).get("results", [])
    count = 0

    for r in results:
        url = r.get("url", "")
        title = r.get("title", "")
        snippet = r.get("description", "")

        item = {
            "id": item_id(source_key, url),
            "source": source_key,
            "source_label": src["label"],
            "source_tier": src["tier"],
            "title": html_to_text(title),
            "url": url,
            "author": "",
            "content_snippet": html_to_text(snippet)[:500],
            "published_at": r.get("page_age", ""),
            "collected_at": now,
            "score": 0,
            "comments_count": 0,
            "tags": [],
        }
        upsert(conn, item)
        count += 1

    conn.commit()
    return count


# ---------- 调度 ----------

COLLECTOR_MAP = {
    "api": lambda conn, key: collect_hn(conn),
    "reddit": collect_reddit,
    "rss": collect_rss,
    "html_anthropic": collect_html_anthropic,
    "brave_search": collect_brave_search,
}


def run_collection(tier: Optional[int] = None, source: Optional[str] = None):
    """主入口：按 tier 或 source 过滤采集。"""
    conn = init_db()
    results = {}

    for key, src in SOURCES.items():
        if source and key != source:
            continue
        if tier is not None and src["tier"] != tier:
            continue

        collector = COLLECTOR_MAP.get(src["type"])
        if not collector:
            log.warning(f"未知类型 {src['type']}，跳过 {key}")
            continue

        log.info(f"采集 [{src['label']}] (Tier {src['tier']})...")
        t0 = time.time()
        try:
            count = collector(conn, key)
        except Exception as e:
            log.error(f"采集 {key} 异常: {e}")
            count = 0
        elapsed = time.time() - t0
        results[key] = count
        log.info(f"  → {count} 条, {elapsed:.1f}s")

    conn.close()
    return results


def show_stats():
    """显示数据库统计。"""
    if not DB_PATH.exists():
        print("数据库不存在，请先运行采集。")
        return

    conn = sqlite3.connect(str(DB_PATH))
    print(f"\n{'='*60}")
    print(f"  AI Intel Hub -- 数据统计")
    print(f"  DB: {DB_PATH}")
    print(f"{'='*60}\n")

    # 总量
    total = conn.execute("SELECT COUNT(*) FROM intel_items").fetchone()[0]
    print(f"  总条目: {total}\n")

    # 按源统计
    rows = conn.execute("""
        SELECT source, source_label, source_tier, COUNT(*) as cnt
        FROM intel_items
        GROUP BY source
        ORDER BY source_tier, cnt DESC
    """).fetchall()

    print(f"  {'源':<20} {'Tier':>4} {'条数':>6}")
    print(f"  {'-'*36}")
    for source, label, tier, cnt in rows:
        print(f"  {label:<20} {tier:>4} {cnt:>6}")

    # 按日统计（最近 7 天）
    print(f"\n  最近采集日志:")
    print(f"  {'-'*36}")
    days = conn.execute("""
        SELECT DATE(collected_at) as day, COUNT(*) as cnt
        FROM intel_items
        GROUP BY day
        ORDER BY day DESC
        LIMIT 7
    """).fetchall()
    for day, cnt in days:
        print(f"  {day}  {cnt} 条")

    print()
    conn.close()


# ---------- CLI ----------

def main():
    parser = argparse.ArgumentParser(description="AI Intel Hub 采集器")
    parser.add_argument("--tier", type=int, choices=[0, 1, 2], help="只采指定 Tier")
    parser.add_argument("--source", type=str, help=f"只采指定源: {', '.join(SOURCES.keys())}")
    parser.add_argument("--stats", action="store_true", help="显示统计")
    parser.add_argument("--list-sources", action="store_true", help="列出所有源")
    args = parser.parse_args()

    if args.stats:
        show_stats()
        return

    if args.list_sources:
        print(f"\n{'源 Key':<20} {'Tier':>4} {'类型':<8} {'名称'}")
        print(f"{'-'*60}")
        for key, src in SOURCES.items():
            print(f"{key:<20} {src['tier']:>4} {src['type']:<8} {src['label']}")
        return

    log.info("=" * 50)
    log.info("AI Intel Hub 采集启动")
    log.info("=" * 50)

    t0 = time.time()
    results = run_collection(tier=args.tier, source=args.source)
    elapsed = time.time() - t0

    total = sum(results.values())
    success = sum(1 for v in results.values() if v > 0)
    failed = sum(1 for v in results.values() if v == 0)

    log.info(f"{'='*50}")
    log.info(f"采集完成: {total} 条, {success} 源成功, {failed} 源失败, 耗时 {elapsed:.1f}s")
    log.info(f"数据库: {DB_PATH}")
    log.info(f"{'='*50}")


if __name__ == "__main__":
    main()
