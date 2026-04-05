#!/bin/bash
# AI Intel Hub -- 每日自动采集 + 评分
# cron: 0 7 * * * /path/to/cron_collect.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON=/usr/bin/python3
LOG="${PROJECT_DIR}/data/collect.log"

echo "=== $(date '+%Y-%m-%d %H:%M:%S') 采集开始 ===" >> "$LOG"

# 采集
$PYTHON "${PROJECT_DIR}/src/collectors/collect.py" >> "$LOG" 2>&1
COLLECT_STATUS=$?

# 评分
# 评分（原 --score-only 参数不存在，已移除）
# TODO: 如需评分，添加独立 score.py 脚本

# 统计
TOTAL=$($PYTHON -c "
import sqlite3
conn = sqlite3.connect('${PROJECT_DIR}/data/intel.db')
today = __import__('datetime').date.today().isoformat()
total = conn.execute('SELECT COUNT(*) FROM intel_items').fetchone()[0]
today_n = conn.execute(\"SELECT COUNT(*) FROM intel_items WHERE collected_at LIKE ?\", (today+'%',)).fetchone()[0]
deep = conn.execute('SELECT COUNT(*) FROM intel_items WHERE signal_score >= 10 AND collected_at LIKE ?', (today+'%',)).fetchone()[0]
print(f'{today_n} 条新情报, {deep} 条深度级, 总量 {total}')
")

echo "结果: $TOTAL" >> "$LOG"

# 编织（采集完自动编织进 vault）
echo "=== $(date '+%Y-%m-%d %H:%M:%S') 编织开始 ===" >> "$LOG"
$PYTHON "${PROJECT_DIR}/src/weaver/weave.py" >> "$LOG" 2>&1
WEAVE_STATUS=$?
echo "=== $(date '+%Y-%m-%d %H:%M:%S') 编织完成 ===" >> "$LOG"

# 桌面通知
if [ "$COLLECT_STATUS" -eq 0 ]; then
    DISPLAY=:0 /usr/bin/notify-send -u normal -t 15000 \
        "AI Intel Hub 采集+编织完成" \
        "$TOTAL\n打开 Obsidian 查看 05_Inbox/daily-intel-$(date +%Y-%m-%d).md" 2>/dev/null || true
fi
