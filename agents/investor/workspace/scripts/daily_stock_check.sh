#!/bin/bash

# 每日收盘前检查是否已记录操作，未记录则自动记录"无操作"

# 获取今天日期
TODAY=$(date +%Y-%m-%d)

# 检查今天是否已经记录（查看 asset-history.json 是否有今天的数据）
DATA_FILE="/Users/liukangkai/Desktop/github/interview/data/stock/asset-history.json"

# 检查是否为交易日下午3点前（周一到周五，排除节假日简单判断）
# 只在工作日且下午3点前执行
HOUR=$(date +%H)
WEEKDAY=$(date +%u)

if [ "$WEEKDAY" -ge 1 ] && [ "$WEEKDAY" -le 5 ] && [ "$HOUR" -lt 15 ]; then
    # 检查是否已有今天记录
    if grep -q "\"date\": \"$TODAY\"" "$DATA_FILE"; then
        echo "$(date): 今日已有记录，跳过"
        exit 0
    fi
    
    echo "$(date): 今日无操作记录，正在自动记录..."
    
    # 获取持仓价格并更新记录
    # 这里调用一个 Python 脚本来完成更新
    /usr/bin/python3 << 'EOF'
import json
import subprocess
import os

# 读取持仓
positions_file = "/Users/liukangkai/Desktop/github/interview/data/stock/positions.json"
asset_file = "/Users/liukangkai/Desktop/github/interview/data/stock/asset-history.json"

with open(positions_file, 'r') as f:
    positions = json.load(f)

# 获取实时价格
result = subprocess.run(
    ["curl", "-s", "--retry", "3", "https://push2.eastmoney.com/api/qt/ulist.np/get?secids=0.000516,1.600860&fields=f2,f3,f4,f12,f13"],
    capture_output=True, text=True, timeout=30
)

data = json.loads(result.stdout)
prices = {}
for item in data.get("data", {}).get("diff", []):
    code = item.get("f12", "")
    prices[code] = {
        "price": item.get("f2", 0) / 1000 if item.get("f2") else 0,
        "change": item.get("f3", 0) / 100 if item.get("f3") else 0
    }

# 计算股票市值
stock_value = 0
for pos in positions:
    code = pos["code"].replace("sz", "").replace("sh", "")
    price = prices.get(code, {}).get("price", 0)
    shares = pos["shares"]
    stock_value += price * shares

# 读取现有记录
with open(asset_file, 'r') as f:
    assets = json.load(f)

# 获取昨日资产
last_asset = assets[-1] if assets else {"cash": 0, "stockValue": 0, "loan": 0, "other": 0}
cash = last_asset.get("cash", 0)
loan = last_asset.get("loan", 0)
other = last_asset.get("other", 0)

# 计算总资产
total = cash + stock_value + loan + other

# 添加今日记录
from datetime import datetime
today = datetime.now().strftime("%Y-%m-%d")

new_record = {
    "date": today,
    "cash": cash,
    "stockValue": int(stock_value),
    "loan": loan,
    "other": other,
    "totalAsset": int(total),
    "remark": "自动记录：无操作"
}

# 检查是否已存在今日记录
existing = False
for i, record in enumerate(assets):
    if record.get("date") == today:
        assets[i] = new_record
        existing = True
        break

if not existing:
    assets.append(new_record)

with open(asset_file, 'w') as f:
    json.dump(assets, f, indent=2, ensure_ascii=False)

print(f"已自动记录：{today}, 总资产: {total}")
EOF
    
    echo "$(date): 自动记录完成"
else
    echo "$(date): 非交易日下午3点前，跳过"
fi
