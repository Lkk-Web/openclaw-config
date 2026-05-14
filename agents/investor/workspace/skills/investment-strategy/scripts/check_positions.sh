#!/bin/bash
# 持仓检查脚本
# 用途：检查持仓股票的最新行情和异动

STOCKS=(
  "国际医学:SZ000516"
  "广发证券:SZ000776"
)

echo "📊 持仓检查 $(date '+%Y-%m-%d %H:%M')"
echo "=============================="

for stock in "${STOCKS[@]}"; do
  IFS=':' read -r name code <<< "$stock"
  echo "检查 $name ($code)..."
  # 这里可以调用股票API获取实时数据
  # 示例使用tavily搜索
  echo "  → 建议使用 skill: tavily-search 获取行情"
done

echo ""
echo "📋 持仓检查清单："
echo "1. 是否有股票涨幅 >3% 或跌幅 >3%？"
echo "2. 是否有股票触及涨停/跌停？"
echo "3. 是否有股票需要止损？"
echo "4. 是否有股票达到卖点？"
echo "5. 现金储备是否充足？"
echo ""
echo "🕒 下次检查：建议每日收盘前或开盘后"