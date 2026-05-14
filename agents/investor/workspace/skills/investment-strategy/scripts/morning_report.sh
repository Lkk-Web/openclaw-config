#!/bin/bash
# 每日早盘分析脚本
# 生成持仓股分析报告

SKILLS_DIR="/Users/liukangkai/.openclaw/agents/investor/workspace/skills"
QUERY_SCRIPT="$SKILLS_DIR/mx_data/scripts/query.sh"

REPORT_FILE="/Users/liukangkai/.openclaw/agents/investor/workspace/memory/morning_report.md"

echo "# 📊 早盘分析 $(date '+%Y-%m-%d %H:%M')" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 国际医学
echo "## 📈 国际医学 (000516)" >> "$REPORT_FILE"
result=$($QUERY_SCRIPT "000516今日行情走势")
echo "```" >> "$REPORT_FILE"
echo "$result" >> "$REPORT_FILE"
echo "```" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 资金流向
echo "## 💰 资金流向" >> "$REPORT_FILE"
result2=$($QUERY_SCRIPT "000516资金流向")
echo "```" >> "$REPORT_FILE"
echo "$result2" >> "$REPORT_FILE"
echo "```" >> "$REPORT_FILE"

echo "✅ 早盘报告已生成: $REPORT_FILE"