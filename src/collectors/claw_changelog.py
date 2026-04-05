#!/usr/bin/env python3
"""
Claw 生态 Changelog 追踪器
抓取 OpenClaw + 各厂商的最新动态/release/changelog，写入 claw-ecosystem-data.json

信息源：
  - OpenClaw GitHub Releases (API)
  - 各厂商官网/changelog 页面 (Brave Search)
  - OPC (One Person Company) 相关新闻 (Brave Search)

用法:
  python claw_changelog.py              # 更新全部
  python claw_changelog.py --stats      # 查看当前数据
"""

import argparse
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CLAW_DATA_PATH = PROJECT_ROOT / "data" / "claw-ecosystem-data.json"
PROXY = "http://127.0.0.1:7890"
BRAVE_API_KEY = "BSAxiCxnkEt6VA8O11gVKQgXJ6oHRnu"
REQUEST_TIMEOUT = 20

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("claw-changelog")


# ---------- GitHub Releases ----------

GITHUB_REPOS = [
    {"repo": "anthropics/claude-code", "label": "Claude Code"},
    {"repo": "openclawai/openclaw", "label": "OpenClaw"},
    {"repo": "openclawai/claw-servers", "label": "Claw Servers (MCP)"},
]


def fetch_github_releases(repo: str, label: str, client: httpx.Client) -> list:
    """获取 GitHub 仓库最近 5 个 release"""
    url = f"https://api.github.com/repos/{repo}/releases?per_page=5"
    try:
        resp = client.get(url)
        resp.raise_for_status()
        releases = resp.json()
        events = []
        for r in releases:
            events.append({
                "date": r["published_at"][:10] if r.get("published_at") else "",
                "event": f"[{label}] {r['name'] or r['tag_name']} 发布",
                "detail": (r.get("body") or "")[:300],
                "url": r.get("html_url", ""),
                "source": "github",
                "vendor": label,
            })
        log.info("  %s: %d releases", label, len(events))
        return events
    except Exception as e:
        log.warning("  %s: 获取失败 %s", label, e)
        return []


def fetch_github_stars(repo: str, client: httpx.Client) -> int:
    """获取 star 数"""
    try:
        resp = client.get(f"https://api.github.com/repos/{repo}")
        resp.raise_for_status()
        return resp.json().get("stargazers_count", 0)
    except:
        return 0


# ---------- Brave Search for Vendor News ----------

VENDOR_QUERIES = [
    {"query": "OpenClaw update OR release OR changelog", "label": "OpenClaw"},
    {"query": "Claude Code update OR changelog 2026", "label": "Claude Code"},
    {"query": "OPC 一人公司 OR \"one person company\" AI", "label": "OPC/一人公司"},
    {"query": "MiniMax MaxClaw update OR 发布", "label": "MaxClaw"},
    {"query": "Kimi Claw OR moonshot update 发布", "label": "Kimi Claw"},
    {"query": "字节 ArkClaw OR 扣子 Coze Claw update", "label": "ArkClaw/Coze"},
    {"query": "阿里云 JVS Claw OR 通义 agent update", "label": "JVS Claw"},
    {"query": "百度 DuClaw OR 文心 agent update", "label": "DuClaw"},
]


def brave_search(query: str, label: str, client: httpx.Client) -> list:
    """用 Brave Search 搜索厂商最新动态"""
    url = "https://api.search.brave.com/res/v1/web/search"
    params = {"q": query, "count": 5, "freshness": "pw"}  # past week
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY,
    }
    try:
        resp = client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        results = resp.json().get("web", {}).get("results", [])
        events = []
        for r in results:
            events.append({
                "date": r.get("page_fetched", "")[:10] or datetime.now().strftime("%Y-%m-%d"),
                "event": f"[{label}] {r['title'][:80]}",
                "detail": r.get("description", "")[:200],
                "url": r.get("url", ""),
                "source": "brave_search",
                "vendor": label,
            })
        log.info("  %s: %d results", label, len(events))
        return events
    except Exception as e:
        log.warning("  %s: 搜索失败 %s", label, e)
        return []


# ---------- 主逻辑 ----------

def update_changelog():
    """更新 claw-ecosystem-data.json 中的 timeline"""
    # 读取现有数据
    if CLAW_DATA_PATH.exists():
        data = json.loads(CLAW_DATA_PATH.read_text(encoding="utf-8"))
    else:
        data = {"meta": {}, "vendors": [], "timeline": []}

    new_events = []
    now = datetime.now(timezone.utc)

    with httpx.Client(timeout=REQUEST_TIMEOUT, proxy=PROXY,
                      headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True) as client:

        # 1. GitHub Releases
        log.info("抓取 GitHub Releases...")
        for repo_info in GITHUB_REPOS:
            events = fetch_github_releases(repo_info["repo"], repo_info["label"], client)
            new_events.extend(events)
            time.sleep(0.3)

        # 2. GitHub Stars update
        log.info("更新 Stars...")
        for repo_info in GITHUB_REPOS:
            stars = fetch_github_stars(repo_info["repo"], client)
            if stars > 0:
                log.info("  %s: %s stars", repo_info["label"], f"{stars:,}")
            time.sleep(0.3)

        # 3. Brave Search for vendor news
        log.info("搜索厂商动态...")
        for vq in VENDOR_QUERIES:
            events = brave_search(vq["query"], vq["label"], client)
            new_events.extend(events)
            time.sleep(0.5)

    # 去重：基于 url 或 event 文本
    existing_events = set()
    for e in data.get("timeline", []):
        existing_events.add(e.get("event", ""))

    added = 0
    for e in new_events:
        if e["event"] not in existing_events:
            data.setdefault("timeline", []).insert(0, e)
            existing_events.add(e["event"])
            added += 1

    # 按日期排序 timeline
    data["timeline"] = sorted(
        data.get("timeline", []),
        key=lambda x: x.get("date", ""),
        reverse=True,
    )[:100]  # 保留最近 100 条

    # 更新 meta
    data.setdefault("meta", {})["updated"] = now.strftime("%Y-%m-%d")
    data["meta"]["changelog_updated"] = now.isoformat()
    data["meta"]["stats"] = data["meta"].get("stats", {})
    data["meta"]["stats"]["timeline_events"] = len(data["timeline"])

    # 写回
    CLAW_DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    log.info("完成: 新增 %d 条事件, 总计 %d 条", added, len(data["timeline"]))
    return added


def show_stats():
    if not CLAW_DATA_PATH.exists():
        print("数据文件不存在")
        return
    data = json.loads(CLAW_DATA_PATH.read_text(encoding="utf-8"))
    print(f"\n{'='*50}")
    print(f"  Claw 生态数据统计")
    print(f"{'='*50}")
    print(f"  厂商: {len(data.get('vendors', []))}")
    print(f"  开源: {len(data.get('oss_projects', []))}")
    print(f"  时间线: {len(data.get('timeline', []))}")
    print(f"  最后更新: {data.get('meta', {}).get('updated', '?')}")
    print(f"\n  最近 5 条事件:")
    for e in data.get("timeline", [])[:5]:
        print(f"    {e.get('date', '?'):12s} | {e.get('event', '')[:60]}")
    print(f"{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(description="Claw 生态 Changelog 追踪")
    parser.add_argument("--stats", action="store_true", help="查看当前数据")
    args = parser.parse_args()

    if args.stats:
        show_stats()
        return

    update_changelog()
    show_stats()


if __name__ == "__main__":
    main()
