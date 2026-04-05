#!/usr/bin/env python3
"""
AI Intel Hub -- Dashboard 单页面板
信息密度高、卡片式、一眼扫完。不分 Tab，全在一个页面。

用法:
  python app.py                  # 启动面板 (自动找端口)
  python app.py --port 37000     # 指定端口
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone, date
from pathlib import Path

from flask import Flask, jsonify, request, Response

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "intel.db"
CLAW_DATA_PATH = PROJECT_ROOT / "data" / "claw-ecosystem-data.json"
VAULT_ROOT = PROJECT_ROOT.parent.parent.parent  # vault/

sys.path.insert(0, str(PROJECT_ROOT / "src"))
from find_port import find_free_port

app = Flask(__name__)


# ---------- DB Helpers ----------

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def ensure_columns():
    """确保 AI 分析列存在"""
    conn = get_db()
    for col, typ in [("category", "TEXT"), ("ai_summary", "TEXT"),
                     ("ai_analysis", "TEXT"), ("analyzed_at", "TEXT"),
                     ("content_category", "TEXT"), ("content_tags", "TEXT")]:
        try:
            conn.execute(f"SELECT {col} FROM intel_items LIMIT 1")
        except Exception:
            conn.execute(f"ALTER TABLE intel_items ADD COLUMN {col} {typ}")
    conn.commit()
    conn.close()


# ---------- API: 热点 ----------

@app.route("/api/hotspots")
def api_hotspots():
    """热点情报，支持 category/tag/domain/source 筛选"""
    d = request.args.get("date", "")
    source = request.args.get("source", "")
    category = request.args.get("category", "")
    tag = request.args.get("tag", "")
    domain = request.args.get("domain", "")
    q = request.args.get("q", "")
    limit = int(request.args.get("limit", "60"))

    conn = get_db()
    sql = "SELECT * FROM intel_items WHERE signal_score >= 4 "
    params = []
    if d:
        sql += "AND collected_at LIKE ? "
        params.append(f"{d}%")
    if source:
        sql += "AND source = ? "
        params.append(source)
    if category:
        sql += "AND (category = ? OR content_category = ?) "
        params.extend([category, category])
    if tag:
        sql += "AND (content_tags LIKE ? OR tags LIKE ?) "
        params.extend([f"%{tag}%", f"%{tag}%"])
    if domain == "opc":
        sql += "AND (title LIKE '%一人公司%' OR title LIKE '%OPC%' OR title LIKE '%solopreneur%' OR ai_summary LIKE '%一人公司%') "
    elif domain == "openclaw":
        sql += "AND (title LIKE '%claw%' OR title LIKE '%Claw%' OR title LIKE '%OpenClaw%' OR ai_summary LIKE '%claw%') "
    if q:
        sql += "AND (title LIKE ? OR ai_summary LIKE ? OR content_snippet LIKE ?) "
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
    sql += "ORDER BY signal_score DESC, collected_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    items = [dict(r) for r in rows]
    conn.close()
    return jsonify(items)


@app.route("/api/sources")
def api_sources():
    """可用源列表"""
    conn = get_db()
    rows = conn.execute(
        "SELECT source, source_label, source_tier, COUNT(*) as cnt "
        "FROM intel_items GROUP BY source ORDER BY source_tier, cnt DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/stats")
def api_stats():
    """面板统计"""
    conn = get_db()
    today = date.today().isoformat()
    stats = {}
    r = conn.execute("SELECT COUNT(*) as total FROM intel_items").fetchone()
    stats["total"] = r["total"]
    r = conn.execute("SELECT COUNT(*) as today FROM intel_items WHERE collected_at LIKE ?",
                     (f"{today}%",)).fetchone()
    stats["today"] = r["today"]
    r = conn.execute("SELECT COUNT(*) as high FROM intel_items WHERE signal_score >= 10").fetchone()
    stats["high_signal"] = r["high"]
    r = conn.execute("SELECT COUNT(*) as analyzed FROM intel_items WHERE analyzed_at IS NOT NULL").fetchone()
    stats["analyzed"] = r["analyzed"]
    r = conn.execute("SELECT COUNT(*) as opps FROM intel_items WHERE category = 'opportunity'").fetchone()
    stats["opportunities"] = r["opps"]
    r = conn.execute("SELECT COUNT(*) as deep FROM intel_items WHERE category = 'deep'").fetchone()
    stats["deep_analysis"] = r["deep"]
    r = conn.execute("SELECT MAX(collected_at) as last FROM intel_items").fetchone()
    stats["last_collected"] = r["last"] or ""
    conn.close()
    return jsonify(stats)


# ---------- API: 筛选器 ----------

@app.route("/api/filters")
def api_filters():
    """返回所有可用的 category 和 tag 值"""
    conn = get_db()
    # categories
    rows = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM intel_items "
        "WHERE category IS NOT NULL AND category != '' "
        "GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    categories = [{"value": r["category"], "count": r["cnt"]} for r in rows]

    # content_categories (if populated)
    rows2 = conn.execute(
        "SELECT content_category, COUNT(*) as cnt FROM intel_items "
        "WHERE content_category IS NOT NULL AND content_category != '' "
        "GROUP BY content_category ORDER BY cnt DESC"
    ).fetchall()
    content_categories = [{"value": r["content_category"], "count": r["cnt"]} for r in rows2]

    # tags from content_tags (JSON arrays) and tags column
    tag_counts = {}
    for col in ["content_tags", "tags"]:
        rows_t = conn.execute(f"SELECT {col} FROM intel_items WHERE {col} IS NOT NULL AND {col} != '[]'").fetchall()
        for row in rows_t:
            try:
                tlist = json.loads(row[0])
                for t in tlist:
                    if t and not t.startswith("author_") and not t.startswith("story_"):
                        tag_counts[t] = tag_counts.get(t, 0) + 1
            except (json.JSONDecodeError, TypeError):
                pass

    # Sort by count, top 30
    tags = sorted([{"value": k, "count": v} for k, v in tag_counts.items()],
                  key=lambda x: -x["count"])[:30]

    # sources
    rows_s = conn.execute(
        "SELECT source, source_label, COUNT(*) as cnt "
        "FROM intel_items GROUP BY source ORDER BY cnt DESC"
    ).fetchall()
    sources = [{"value": r["source"], "label": r["source_label"], "count": r["cnt"]} for r in rows_s]

    conn.close()
    return jsonify({
        "categories": categories,
        "content_categories": content_categories,
        "tags": tags,
        "sources": sources,
    })


# ---------- API: 商机 ----------

@app.route("/api/opportunities")
def api_opportunities():
    """商机情报：category=opportunity 的条目"""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM intel_items WHERE category = 'opportunity' "
        "ORDER BY signal_score DESC, collected_at DESC LIMIT 30"
    ).fetchall()
    items = [dict(r) for r in rows]
    conn.close()

    # 也扫描 vault opportunity 目录
    opp_dir = VAULT_ROOT / "1-knowledge" / "opportunity" / "intel"
    vault_opps = []
    if opp_dir.exists():
        for f in sorted(opp_dir.glob("*.md"), reverse=True)[:10]:
            vault_opps.append({
                "filename": f.name,
                "content": f.read_text(encoding="utf-8", errors="ignore")[:2000],
            })

    return jsonify({"db_items": items, "vault_items": vault_opps})


# ---------- API: 深度 ----------

@app.route("/api/deep")
def api_deep():
    """深度解读：category=deep 或 signal_score >= 10"""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM intel_items WHERE category = 'deep' OR signal_score >= 10 "
        "ORDER BY signal_score DESC, collected_at DESC LIMIT 20"
    ).fetchall()
    items = [dict(r) for r in rows]
    conn.close()

    # 扫描 /ai-industry-intel-digest 产出
    digest_dir = PROJECT_ROOT / "output" / "AI-Hotspots" / "Daily"
    vault_digests = []
    if digest_dir.exists():
        for f in sorted(digest_dir.glob("*.md"), reverse=True)[:10]:
            vault_digests.append({
                "filename": f.name,
                "content": f.read_text(encoding="utf-8", errors="ignore")[:3000],
            })

    return jsonify({"db_items": items, "vault_items": vault_digests})


# ---------- API: Claw 生态 ----------

@app.route("/api/claw")
def api_claw():
    """Claw 生态数据"""
    if CLAW_DATA_PATH.exists():
        data = json.loads(CLAW_DATA_PATH.read_text(encoding="utf-8"))
        return jsonify(data)
    return jsonify({"error": "no claw data", "vendors": [], "timeline": []})


# ---------- API: 采集+分析 ----------

@app.route("/api/collect", methods=["POST"])
def api_collect():
    """触发采集"""
    import subprocess
    collector = PROJECT_ROOT / "src" / "collectors" / "collect.py"
    result = subprocess.run(["python3", str(collector)], capture_output=True,
                           text=True, timeout=120)
    return jsonify({"status": "ok", "output": result.stdout[-500:] if result.stdout else ""})


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """触发 AI 分析"""
    import subprocess
    analyzer = PROJECT_ROOT / "src" / "analyzers" / "analyze.py"
    if not analyzer.exists():
        return jsonify({"status": "error", "message": "analyze.py not found"})
    result = subprocess.run(["python3", str(analyzer)], capture_output=True,
                           text=True, timeout=600)
    return jsonify({"status": "ok", "output": result.stdout[-500:] if result.stdout else ""})


# ---------- Dashboard HTML ----------

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Intel Hub</title>
<style>
:root {
  --bg: #F7F7F5; --surface: #FFFFFF; --text: #37352F;
  --text2: #787774; --text3: #9B9A97; --border: #E9E9E7;
  --blue: #007AFF; --green: #27AE60; --orange: #D9730D;
  --red: #EB5757; --purple: #7B61FF;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }

/* Header */
.header { background: var(--surface); padding: 16px 28px; border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; position: sticky; top: 0; z-index: 100; }
.header h1 { font-size: 20px; font-weight: 700; white-space: nowrap; }
.header-stats { display: flex; gap: 10px; flex-wrap: wrap; }
.stat-pill { background: var(--bg); padding: 3px 12px; border-radius: 4px; font-size: 12px; border: 1px solid var(--border); white-space: nowrap; }
.stat-pill .n { font-weight: 700; color: var(--text); }
.header-actions { display: flex; gap: 8px; }
.btn { padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border); background: var(--surface); color: var(--text2); cursor: pointer; font-size: 13px; font-weight: 500; transition: all .15s; }
.btn:hover { border-color: var(--text3); color: var(--text); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background: var(--text); color: #fff; border-color: var(--text); }
.btn-primary:hover { background: #2d2d2a; }

/* Filter bar */
.filter-bar { background: var(--surface); padding: 12px 28px; border-bottom: 1px solid var(--border); display: flex; gap: 12px; flex-wrap: wrap; align-items: center; position: sticky; top: 57px; z-index: 99; }
.filter-group { display: flex; align-items: center; gap: 6px; }
.filter-label { font-size: 12px; color: var(--text3); font-weight: 600; white-space: nowrap; }
.filter-select { padding: 4px 10px; border: 1px solid var(--border); border-radius: 4px; font-size: 13px; color: var(--text); background: var(--bg); cursor: pointer; outline: none; }
.filter-select:focus { border-color: var(--blue); }
.tag-btn { padding: 3px 10px; border: 1px solid var(--border); background: var(--surface); border-radius: 12px; cursor: pointer; font-size: 12px; color: var(--text2); transition: all .15s; white-space: nowrap; }
.tag-btn:hover { background: var(--bg); color: var(--text); }
.tag-btn.active { background: var(--text); color: #fff; border-color: var(--text); }
.search-input { padding: 5px 12px; border: 1px solid var(--border); border-radius: 4px; font-size: 13px; width: 200px; outline: none; background: var(--bg); }
.search-input:focus { border-color: var(--blue); background: var(--surface); }
.tag-scroll { display: flex; gap: 4px; overflow-x: auto; max-width: 500px; scrollbar-width: none; }
.tag-scroll::-webkit-scrollbar { display: none; }

/* Main layout */
.main-layout { max-width: 1440px; margin: 0 auto; padding: 20px 28px; }
.two-col { display: grid; grid-template-columns: 1fr 380px; gap: 24px; }

/* Section */
.section { margin-bottom: 24px; }
.section-title { font-size: 14px; font-weight: 700; color: var(--text); margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
.section-title .count { font-size: 12px; color: var(--text3); font-weight: 400; }

/* Cards -- main feed */
.card-feed { display: flex; flex-direction: column; gap: 8px; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; transition: box-shadow .15s; }
.card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.card-top { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; flex-wrap: wrap; }
.signal-badge { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; white-space: nowrap; }
.signal-important { background: #FEF3E8; color: var(--orange); }
.signal-watch { background: #EDF5FF; color: var(--blue); }
.cat-tag { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; white-space: nowrap; }
.cat-product { background: #EDF5FF; color: var(--blue); }
.cat-tech { background: #F3EEFF; color: var(--purple); }
.cat-policy { background: #FDECEA; color: var(--red); }
.cat-funding { background: #EEFAF3; color: var(--green); }
.cat-opinion { background: #FEF3E8; color: var(--orange); }
.cat-security { background: #FDECEA; color: #C0392B; }
.cat-tutorial { background: #EDF5FF; color: #2980B9; }
.cat-hotspot { background: #FEF3E8; color: var(--orange); }
.cat-opportunity { background: #EEFAF3; color: var(--green); }
.cat-deep { background: #F3EEFF; color: var(--purple); }
.card-source { font-size: 11px; color: var(--text3); }
.card-title { font-size: 14px; font-weight: 600; line-height: 1.4; margin-bottom: 4px; }
.card-title a { color: var(--text); text-decoration: none; }
.card-title a:hover { color: var(--blue); }
.card-tags-row { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 4px; }
.card-tags-row .mini-tag { font-size: 10px; color: var(--text3); background: var(--bg); padding: 1px 6px; border-radius: 3px; }
.card-summary { font-size: 13px; color: var(--text2); line-height: 1.5; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.card-expand { font-size: 12px; color: var(--blue); cursor: pointer; margin-top: 4px; font-weight: 500; }
.card-analysis { font-size: 13px; color: var(--text); line-height: 1.6; border-left: 3px solid var(--blue); padding: 10px 12px; margin-top: 6px; background: #FAFAF9; border-radius: 0 6px 6px 0; display: none; white-space: pre-wrap; }
.card-time { font-size: 11px; color: var(--text3); margin-top: 4px; }

/* Right sidebar */
.sidebar { display: flex; flex-direction: column; gap: 20px; }
.sidebar-panel { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }
.sidebar-panel h3 { font-size: 13px; font-weight: 700; color: var(--text); margin-bottom: 10px; }

/* Timeline */
.tl-item { display: flex; gap: 10px; padding: 6px 0; border-bottom: 1px solid var(--bg); font-size: 12px; }
.tl-date { color: var(--text3); flex-shrink: 0; width: 80px; }
.tl-vendor { display: inline-block; padding: 1px 5px; border-radius: 3px; font-size: 10px; font-weight: 600; background: #EDF5FF; color: var(--blue); margin-right: 4px; }
.tl-event { color: var(--text); flex: 1; min-width: 0; }
.tl-event a { color: var(--text); text-decoration: none; }
.tl-event a:hover { color: var(--blue); }

/* Vendor compact */
.vendor-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.vendor-mini { padding: 8px 10px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg); }
.vendor-mini .v-name { font-size: 12px; font-weight: 700; }
.vendor-mini .v-status { display: inline-block; padding: 1px 5px; border-radius: 3px; font-size: 10px; font-weight: 600; }
.v-online { background: #EEFAF3; color: #27AE60; }
.v-beta { background: #FEF3E8; color: #D9730D; }
.v-test { background: #FDECEA; color: #EB5757; }
.vendor-mini .v-latest { font-size: 11px; color: var(--text3); margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Horizontal scroll sections */
.h-scroll-container { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 8px; scrollbar-width: thin; }
.h-scroll-container::-webkit-scrollbar { height: 4px; }
.h-scroll-container::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
.h-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; min-width: 320px; max-width: 380px; flex-shrink: 0; }
.h-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.h-card .card-title { font-size: 14px; }

/* Deep card */
.deep-row { display: flex; flex-direction: column; gap: 10px; }
.deep-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px 18px; }
.deep-card .card-analysis { display: block; max-height: 200px; overflow-y: auto; }
.copy-btn { padding: 4px 10px; border: 1px solid var(--border); border-radius: 4px; background: var(--surface); color: var(--text2); cursor: pointer; font-size: 11px; transition: all .15s; }
.copy-btn:hover { background: var(--bg); color: var(--text); }
.copy-btn.copied { background: var(--green); color: #fff; border-color: var(--green); }

/* Bottom sections */
.bottom-sections { margin-top: 24px; display: flex; flex-direction: column; gap: 24px; }

/* Empty / Loading */
.empty { text-align: center; padding: 40px 20px; color: var(--text3); }
.empty p { font-size: 13px; }
.loading { text-align: center; padding: 30px; color: var(--text3); font-size: 13px; }

/* Responsive */
@media (max-width: 960px) {
  .two-col { grid-template-columns: 1fr; }
  .sidebar { order: -1; }
  .filter-bar { padding: 10px 16px; }
  .main-layout { padding: 16px; }
  .header { padding: 12px 16px; }
  .tag-scroll { max-width: 280px; }
  .vendor-grid { grid-template-columns: 1fr; }
}
@media (max-width: 600px) {
  .h-card { min-width: 260px; }
  .search-input { width: 140px; }
}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
    <h1>AI Intel Hub</h1>
    <div class="header-stats" id="header-stats"></div>
  </div>
  <div class="header-actions">
    <button class="btn" onclick="doCollect()" id="btn-collect">采集</button>
    <button class="btn btn-primary" onclick="doAnalyze()" id="btn-analyze">AI 分析</button>
  </div>
</div>

<!-- Filter bar -->
<div class="filter-bar">
  <div class="filter-group">
    <span class="filter-label">分类</span>
    <select class="filter-select" id="f-category" onchange="applyFilters()">
      <option value="">全部</option>
    </select>
  </div>
  <div class="filter-group">
    <span class="filter-label">标签</span>
    <div class="tag-scroll" id="f-tags"></div>
  </div>
  <div class="filter-group">
    <span class="filter-label">主题域</span>
    <select class="filter-select" id="f-domain" onchange="applyFilters()">
      <option value="">全部</option>
      <option value="openclaw">OpenClaw</option>
      <option value="opc">OPC 一人公司</option>
    </select>
  </div>
  <div class="filter-group" style="margin-left:auto">
    <input type="text" class="search-input" id="f-search" placeholder="搜索标题/摘要..." oninput="debounceSearch()">
  </div>
</div>

<!-- Main content -->
<div class="main-layout">
  <div class="two-col">
    <!-- Left: main feed -->
    <div>
      <div class="section">
        <div class="section-title">AI 热点 <span class="count" id="hotspot-count"></span></div>
        <div class="card-feed" id="hotspot-cards">
          <div class="loading">加载中...</div>
        </div>
      </div>
    </div>

    <!-- Right: sidebar -->
    <div class="sidebar">
      <!-- Claw timeline -->
      <div class="sidebar-panel" id="claw-timeline-panel">
        <h3>OpenClaw 事件流</h3>
        <div id="claw-timeline"><div class="loading">加载中...</div></div>
      </div>
      <!-- Vendor overview -->
      <div class="sidebar-panel" id="claw-vendor-panel">
        <h3>厂商概览</h3>
        <div id="claw-vendors"></div>
      </div>
      <!-- OPC dynamics -->
      <div class="sidebar-panel" id="opc-panel">
        <h3>OPC 一人公司动态</h3>
        <div id="opc-feed"><div class="loading">加载中...</div></div>
      </div>
    </div>
  </div>

  <!-- Bottom sections -->
  <div class="bottom-sections">
    <!-- Opportunities -->
    <div class="section">
      <div class="section-title">商机发现 <span class="count" id="opp-count"></span></div>
      <div class="h-scroll-container" id="opp-cards">
        <div class="loading">加载中...</div>
      </div>
    </div>
    <!-- Deep analysis -->
    <div class="section">
      <div class="section-title">发布就绪 <span class="count" id="deep-count"></span></div>
      <div class="deep-row" id="deep-cards">
        <div class="loading">加载中...</div>
      </div>
    </div>
  </div>
</div>

<script>
// ---------- State ----------
let allHotspots = [];
let activeTagFilters = new Set();
let searchTimer = null;

// ---------- Helpers ----------
function esc(s) { const d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }

function timeAgo(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    const now = new Date();
    const diff = Math.floor((now - d) / 1000);
    if (diff < 60) return '刚刚';
    if (diff < 3600) return Math.floor(diff / 60) + '分钟前';
    if (diff < 86400) return Math.floor(diff / 3600) + '小时前';
    if (diff < 604800) return Math.floor(diff / 86400) + '天前';
    return iso.slice(0, 10);
  } catch(e) { return iso ? iso.slice(0, 10) : ''; }
}

function signalBadge(score) {
  if (score >= 10) return '<span class="signal-badge signal-important">重要</span>';
  if (score >= 6) return '<span class="signal-badge signal-watch">关注</span>';
  return '';
}

function catTag(cat) {
  if (!cat) return '';
  const map = {
    'hotspot': ['热点', 'cat-hotspot'],
    'opportunity': ['商机', 'cat-opportunity'],
    'deep': ['深度', 'cat-deep'],
    '产品发布': ['产品发布', 'cat-product'],
    '技术更新': ['技术更新', 'cat-tech'],
    '政策法规': ['政策法规', 'cat-policy'],
    '融资并购': ['融资', 'cat-funding'],
    '观点评论': ['观点', 'cat-opinion'],
    '安全事件': ['安全', 'cat-security'],
    '教程': ['教程', 'cat-tutorial'],
  };
  const m = map[cat] || [cat, 'cat-hotspot'];
  return '<span class="cat-tag ' + m[1] + '">' + esc(m[0]) + '</span>';
}

function getDisplayTitle(item) {
  // 如果 ai_summary 存在且原文标题是英文，用 ai_summary 第一句做标题
  const title = item.title || '';
  if (item.ai_summary && /^[A-Za-z0-9\s\[\]\(\)\-:'",.!?#@&]+$/.test(title.trim())) {
    const firstSentence = item.ai_summary.split(/[。！？\.\!\?]/)[0];
    if (firstSentence && firstSentence.length > 5 && firstSentence.length < 100) {
      return firstSentence;
    }
  }
  return title;
}

function parseTags(tagsStr) {
  if (!tagsStr) return [];
  try {
    const arr = JSON.parse(tagsStr);
    return arr.filter(t => t && !t.startsWith('author_') && !t.startsWith('story_'));
  } catch(e) { return []; }
}

// ---------- Load all ----------
async function loadAll() {
  await Promise.all([loadStats(), loadHotspots(), loadClaw(), loadOPC(), loadOpportunities(), loadDeep(), loadFilters()]);
}

// ---------- Stats ----------
async function loadStats() {
  try {
    const r = await fetch('/api/stats');
    const s = await r.json();
    document.getElementById('header-stats').innerHTML =
      '<div class="stat-pill">总计 <span class="n">' + s.total + '</span></div>' +
      '<div class="stat-pill">今日 <span class="n">' + s.today + '</span></div>' +
      '<div class="stat-pill">重要 <span class="n">' + s.high_signal + '</span></div>' +
      '<div class="stat-pill">已分析 <span class="n">' + s.analyzed + '</span></div>' +
      '<div class="stat-pill">商机 <span class="n">' + s.opportunities + '</span></div>' +
      '<div class="stat-pill">深度 <span class="n">' + s.deep_analysis + '</span></div>';
  } catch(e) {}
}

// ---------- Filters ----------
async function loadFilters() {
  try {
    const r = await fetch('/api/filters');
    const data = await r.json();

    // Category dropdown
    const sel = document.getElementById('f-category');
    const current = sel.value;
    sel.innerHTML = '<option value="">全部</option>';
    (data.categories || []).forEach(c => {
      sel.innerHTML += '<option value="' + esc(c.value) + '">' + esc(c.value) + ' (' + c.count + ')</option>';
    });
    (data.content_categories || []).forEach(c => {
      sel.innerHTML += '<option value="' + esc(c.value) + '">' + esc(c.value) + ' (' + c.count + ')</option>';
    });
    sel.value = current;

    // Tags
    const tagContainer = document.getElementById('f-tags');
    tagContainer.innerHTML = '';
    (data.tags || []).slice(0, 15).forEach(t => {
      const btn = document.createElement('button');
      btn.className = 'tag-btn' + (activeTagFilters.has(t.value) ? ' active' : '');
      btn.textContent = t.value;
      btn.onclick = function() {
        if (activeTagFilters.has(t.value)) {
          activeTagFilters.delete(t.value);
          this.classList.remove('active');
        } else {
          activeTagFilters.add(t.value);
          this.classList.add('active');
        }
        applyFilters();
      };
      tagContainer.appendChild(btn);
    });
  } catch(e) {}
}

// ---------- Hotspots ----------
async function loadHotspots() {
  try {
    const r = await fetch('/api/hotspots?limit=60');
    allHotspots = await r.json();
    renderHotspots(allHotspots);
  } catch(e) {
    document.getElementById('hotspot-cards').innerHTML = '<div class="empty"><p>加载失败</p></div>';
  }
}

function renderHotspots(items) {
  const container = document.getElementById('hotspot-cards');
  const countEl = document.getElementById('hotspot-count');
  countEl.textContent = items.length + ' 条';

  if (!items.length) {
    container.innerHTML = '<div class="empty"><p>暂无热点，点击"采集"获取最新数据</p></div>';
    return;
  }

  let html = '';
  items.forEach((it, i) => {
    const displayTitle = getDisplayTitle(it);
    const tags = parseTags(it.content_tags || it.tags);
    const cat = it.content_category || it.category || '';
    html += '<div class="card">' +
      '<div class="card-top">' +
        signalBadge(it.signal_score) +
        catTag(cat) +
        '<span class="card-source">' + esc(it.source_label || it.source) + '</span>' +
      '</div>' +
      '<div class="card-title">' +
        (it.url ? '<a href="' + esc(it.url) + '" target="_blank">' + esc(displayTitle) + '</a>' : esc(displayTitle)) +
      '</div>' +
      (tags.length ? '<div class="card-tags-row">' + tags.map(t => '<span class="mini-tag">#' + esc(t) + '</span>').join('') + '</div>' : '') +
      (it.ai_summary ? '<div class="card-summary">' + esc(it.ai_summary) + '</div>' : (it.content_snippet ? '<div class="card-summary">' + esc(it.content_snippet) + '</div>' : '')) +
      (it.ai_analysis ? '<div class="card-expand" onclick="toggleAnalysis(this)">展开分析</div><div class="card-analysis">' + esc(it.ai_analysis) + '</div>' : '') +
      '<div class="card-time">' + timeAgo(it.published_at || it.collected_at) + '</div>' +
    '</div>';
  });
  container.innerHTML = html;
}

function toggleAnalysis(el) {
  const d = el.nextElementSibling;
  if (d.style.display === 'block') { d.style.display = 'none'; el.textContent = '展开分析'; }
  else { d.style.display = 'block'; el.textContent = '收起分析'; }
}

// ---------- Filtering ----------
function applyFilters() {
  const cat = document.getElementById('f-category').value;
  const domain = document.getElementById('f-domain').value;
  const q = document.getElementById('f-search').value.trim().toLowerCase();

  let filtered = allHotspots;

  if (cat) {
    filtered = filtered.filter(it => (it.category === cat) || (it.content_category === cat));
  }
  if (domain === 'openclaw') {
    filtered = filtered.filter(it =>
      (it.title && /claw|openclaw/i.test(it.title)) ||
      (it.ai_summary && /claw/i.test(it.ai_summary))
    );
  } else if (domain === 'opc') {
    filtered = filtered.filter(it =>
      (it.title && /一人公司|OPC|solopreneur/i.test(it.title)) ||
      (it.ai_summary && /一人公司|OPC|solopreneur/i.test(it.ai_summary))
    );
  }
  if (activeTagFilters.size > 0) {
    filtered = filtered.filter(it => {
      const tags = parseTags(it.content_tags || it.tags);
      return [...activeTagFilters].some(f => tags.includes(f));
    });
  }
  if (q) {
    filtered = filtered.filter(it =>
      (it.title && it.title.toLowerCase().includes(q)) ||
      (it.ai_summary && it.ai_summary.toLowerCase().includes(q)) ||
      (it.content_snippet && it.content_snippet.toLowerCase().includes(q))
    );
  }

  renderHotspots(filtered);
}

function debounceSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(applyFilters, 300);
}

// ---------- Claw ----------
async function loadClaw() {
  try {
    const r = await fetch('/api/claw');
    const data = await r.json();

    if (data.error || !data.vendors) {
      document.getElementById('claw-timeline').innerHTML = '<div class="empty"><p>Claw 数据未加载</p></div>';
      document.getElementById('claw-vendors').innerHTML = '';
      return;
    }

    // Timeline
    if (data.timeline && data.timeline.length) {
      let html = '';
      data.timeline.slice(0, 12).forEach(e => {
        const hasUrl = e.url && e.url.startsWith('http');
        const vendor = e.vendor ? '<span class="tl-vendor">' + esc(e.vendor) + '</span>' : '';
        const eventText = (e.event || '').replace(/^\[.*?\]\s*/, '');
        html += '<div class="tl-item">' +
          '<div class="tl-date">' + esc(e.date || '') + '</div>' +
          '<div class="tl-event">' +
            vendor +
            (hasUrl ? '<a href="' + esc(e.url) + '" target="_blank">' + esc(eventText) + '</a>' : esc(eventText)) +
          '</div>' +
        '</div>';
      });
      document.getElementById('claw-timeline').innerHTML = html;
    } else {
      document.getElementById('claw-timeline').innerHTML = '<div class="empty"><p>暂无事件</p></div>';
    }

    // Vendors compact
    if (data.vendors && data.vendors.length) {
      let html = '<div class="vendor-grid">';
      data.vendors.forEach(v => {
        const statusCls = v.status === '已上线' ? 'v-online' : v.status === 'Beta' ? 'v-beta' : 'v-test';
        // Find latest timeline event for this vendor
        let latest = '';
        if (data.timeline) {
          const evt = data.timeline.find(e => e.vendor === v.vendor || e.vendor === v.product);
          if (evt) latest = (evt.event || '').replace(/^\[.*?\]\s*/, '').substring(0, 50);
        }
        html += '<div class="vendor-mini">' +
          '<div style="display:flex;justify-content:space-between;align-items:center">' +
            '<span class="v-name">' + esc(v.product || v.vendor) + '</span>' +
            '<span class="v-status ' + statusCls + '">' + esc(v.status) + '</span>' +
          '</div>' +
          (latest ? '<div class="v-latest">' + esc(latest) + '</div>' : '') +
        '</div>';
      });
      html += '</div>';
      document.getElementById('claw-vendors').innerHTML = html;
    }
  } catch(e) {
    document.getElementById('claw-timeline').innerHTML = '<div class="empty"><p>加载失败</p></div>';
  }
}

// ---------- OPC ----------
async function loadOPC() {
  try {
    const r = await fetch('/api/hotspots?domain=opc&limit=10');
    const items = await r.json();
    const container = document.getElementById('opc-feed');

    if (!items.length) {
      container.innerHTML = '<div class="empty"><p>暂无 OPC 动态</p></div>';
      return;
    }

    let html = '';
    items.forEach(it => {
      html += '<div style="padding:6px 0;border-bottom:1px solid var(--bg);font-size:12px">' +
        '<div style="font-weight:600;margin-bottom:2px">' +
          (it.url ? '<a href="' + esc(it.url) + '" target="_blank" style="color:var(--text);text-decoration:none">' + esc(getDisplayTitle(it)) + '</a>' : esc(getDisplayTitle(it))) +
        '</div>' +
        '<div style="color:var(--text3)">' + timeAgo(it.published_at || it.collected_at) + ' · ' + esc(it.source_label || '') + '</div>' +
      '</div>';
    });
    container.innerHTML = html;
  } catch(e) {
    document.getElementById('opc-feed').innerHTML = '<div class="empty"><p>加载失败</p></div>';
  }
}

// ---------- Opportunities ----------
async function loadOpportunities() {
  try {
    const r = await fetch('/api/opportunities');
    const data = await r.json();
    const items = data.db_items || [];
    const vault = data.vault_items || [];
    const container = document.getElementById('opp-cards');
    const countEl = document.getElementById('opp-count');
    const total = items.length + vault.length;
    countEl.textContent = total + ' 条';

    if (!total) {
      container.innerHTML = '<div class="empty"><p>暂无商机，运行"AI 分析"后自动识别</p></div>';
      return;
    }

    let html = '';
    items.forEach(it => {
      html += '<div class="h-card">' +
        '<div class="card-top">' +
          signalBadge(it.signal_score) +
          '<span class="cat-tag cat-opportunity">商机</span>' +
          '<span class="card-source">' + esc(it.source_label) + '</span>' +
        '</div>' +
        '<div class="card-title">' +
          (it.url ? '<a href="' + esc(it.url) + '" target="_blank">' + esc(getDisplayTitle(it)) + '</a>' : esc(getDisplayTitle(it))) +
        '</div>' +
        (it.ai_summary ? '<div class="card-summary">' + esc(it.ai_summary) + '</div>' : '') +
        (it.ai_analysis ? '<div class="card-summary" style="-webkit-line-clamp:3;margin-top:4px;font-size:12px;border-left:2px solid var(--green);padding-left:8px">' + esc(it.ai_analysis.substring(0, 200)) + '</div>' : '') +
        '<div class="card-time">' + timeAgo(it.collected_at) + '</div>' +
      '</div>';
    });
    vault.forEach(v => {
      const preview = v.content.substring(0, 150).replace(/\n/g, ' ');
      html += '<div class="h-card">' +
        '<div class="card-top"><span class="cat-tag cat-opportunity">Vault</span></div>' +
        '<div class="card-title">' + esc(v.filename.replace('.md','')) + '</div>' +
        '<div class="card-summary">' + esc(preview) + '</div>' +
      '</div>';
    });
    container.innerHTML = html;
  } catch(e) {
    document.getElementById('opp-cards').innerHTML = '<div class="empty"><p>加载失败</p></div>';
  }
}

// ---------- Deep / Publish-ready ----------
async function loadDeep() {
  try {
    const r = await fetch('/api/deep');
    const data = await r.json();
    const items = data.db_items || [];
    const vault = data.vault_items || [];
    const container = document.getElementById('deep-cards');
    const countEl = document.getElementById('deep-count');
    const total = items.length + vault.length;
    countEl.textContent = total + ' 条';

    if (!total) {
      container.innerHTML = '<div class="empty"><p>暂无深度解读，10分+ 情报自动进入</p></div>';
      return;
    }

    let html = '';
    items.forEach((it, i) => {
      const analysisText = it.ai_analysis || it.ai_summary || '';
      html += '<div class="deep-card">' +
        '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px">' +
          '<div style="flex:1">' +
            '<div class="card-top">' +
              signalBadge(it.signal_score) +
              '<span class="cat-tag cat-deep">深度</span>' +
              '<span class="card-source">' + esc(it.source_label) + '</span>' +
            '</div>' +
            '<div class="card-title">' +
              (it.url ? '<a href="' + esc(it.url) + '" target="_blank">' + esc(getDisplayTitle(it)) + '</a>' : esc(getDisplayTitle(it))) +
            '</div>' +
          '</div>' +
          (analysisText ? '<button class="copy-btn" onclick="copyForXHS(this, ' + i + ')">复制到小红书</button>' : '') +
        '</div>' +
        (it.ai_summary ? '<div class="card-summary" style="-webkit-line-clamp:unset">' + esc(it.ai_summary) + '</div>' : '') +
        (it.ai_analysis ? '<div class="card-analysis" style="display:block">' + esc(it.ai_analysis) + '</div>' : '') +
        '<div class="card-time">' + timeAgo(it.collected_at) + '</div>' +
      '</div>';
    });
    vault.forEach(v => {
      const preview = v.content.substring(0, 300).replace(/\n/g, ' ');
      html += '<div class="deep-card">' +
        '<div class="card-top"><span class="cat-tag cat-deep">文件</span></div>' +
        '<div class="card-title">' + esc(v.filename.replace('.md','')) + '</div>' +
        '<div class="card-summary" style="-webkit-line-clamp:4">' + esc(preview) + '</div>' +
      '</div>';
    });
    container.innerHTML = html;
  } catch(e) {
    document.getElementById('deep-cards').innerHTML = '<div class="empty"><p>加载失败</p></div>';
  }
}

// Deep items cache for copy
let deepItemsCache = [];
async function cacheDeepItems() {
  try {
    const r = await fetch('/api/deep');
    const data = await r.json();
    deepItemsCache = data.db_items || [];
  } catch(e) {}
}

function copyForXHS(btn, idx) {
  if (idx >= deepItemsCache.length) {
    // Fallback: copy from card analysis text
    const card = btn.closest('.deep-card');
    const analysis = card.querySelector('.card-analysis');
    const title = card.querySelector('.card-title');
    const text = (title ? title.textContent : '') + '\n\n' + (analysis ? analysis.textContent : '');
    doCopy(btn, formatXHS(title ? title.textContent : '', text));
    return;
  }
  const it = deepItemsCache[idx];
  const title = getDisplayTitle(it);
  const body = it.ai_analysis || it.ai_summary || '';
  doCopy(btn, formatXHS(title, body));
}

function formatXHS(title, body) {
  // 小红书格式：标题 + 分隔 + 正文 + 标签
  let text = title + '\n\n---\n\n' + body;
  text += '\n\n#AI情报 #科技前沿 #AI行业分析';
  return text;
}

function doCopy(btn, text) {
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = '已复制';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = '复制到小红书'; btn.classList.remove('copied'); }, 2000);
  }).catch(() => {
    btn.textContent = '复制失败';
    setTimeout(() => { btn.textContent = '复制到小红书'; }, 2000);
  });
}

// ---------- Actions ----------
async function doCollect() {
  const btn = document.getElementById('btn-collect');
  btn.textContent = '采集中...'; btn.disabled = true;
  try {
    await fetch('/api/collect', {method:'POST'});
    btn.textContent = '完成';
    setTimeout(() => { btn.textContent = '采集'; btn.disabled = false; loadAll(); }, 1500);
  } catch(e) {
    btn.textContent = '失败';
    setTimeout(() => { btn.textContent = '采集'; btn.disabled = false; }, 2000);
  }
}

async function doAnalyze() {
  const btn = document.getElementById('btn-analyze');
  btn.textContent = '分析中...'; btn.disabled = true;
  try {
    await fetch('/api/analyze', {method:'POST'});
    btn.textContent = '完成';
    setTimeout(() => { btn.textContent = 'AI 分析'; btn.disabled = false; loadAll(); }, 1500);
  } catch(e) {
    btn.textContent = '失败';
    setTimeout(() => { btn.textContent = 'AI 分析'; btn.disabled = false; }, 2000);
  }
}

// ---------- Init ----------
loadAll();
cacheDeepItems();
setInterval(loadAll, 300000);
</script>
</body>
</html>"""


# ---------- Routes ----------

@app.route("/")
def index():
    return Response(DASHBOARD_HTML, content_type="text/html; charset=utf-8")


# ---------- Main ----------

def main():
    parser = argparse.ArgumentParser(description="AI Intel Hub Dashboard")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"数据库不存在: {DB_PATH}，请先运行 collect.py")
        return

    ensure_columns()

    port = args.port if args.port > 0 else find_free_port(37000)
    print(f"\n{'='*50}")
    print(f"  AI Intel Hub: http://localhost:{port}")
    print(f"  数据库: {DB_PATH}")
    print(f"  Claw数据: {CLAW_DATA_PATH}")
    print(f"{'='*50}\n")
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
