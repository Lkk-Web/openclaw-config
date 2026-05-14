#!/bin/bash
# 每日持仓股分析脚本
# 功能：查询持仓股最新行情，给出操作建议
# 用法：直接运行或设置cron

SKILLS_DIR="/Users/liukangkai/.openclaw/agents/investor/workspace/skills"
QUERY_SCRIPT="$SKILLS_DIR/mx_data/scripts/query.sh"

# 持仓股票列表
STOCKS=(
  "000516:国际医学"
)

echo "📊 每日持仓分析 $(date '+%Y-%m-%d %H:%M')"
echo "=============================="
echo ""

for stock in "${STOCKS[@]}"; do
  IFS=':' read -r code name <<< "$stock"
  echo "📈 $name ($code)"
  
  # 查询最新价和涨跌幅
  result=$($QUERY_SCRIPT "$code最新价")
  price=$(echo "$result" | grep -o '"f2":\s*\["[^"]*"\]' | grep -o '[0-9.]*')
  change=$(echo "$result" | grep -o '"f3":\s*\["[^"]*"\]' | grep -o '[0-9.]*%')
  
  echo "  最新价: ${price:-未知}元"
  echo "  涨跌幅: ${change:-未知}"
  echo ""
done

echo "💡 操作建议："
echo "  - 持有不动，等待6元目标位"
echo "  - 若高开低走破5元，考虑减仓"
echo "  - 接近6元可分批卖出"
echo ""
echo "=============================="