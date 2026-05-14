#!/bin/bash
# 妙想金融数据查询脚本
# 用法: bash scripts/query.sh "查询内容"

# 默认apikey（测试用）
DEFAULT_APIKEY="mkt_FlyBm_-6IkomvaVRPEbcqbcehxLia0tu7LUAE7vrlZU"

# 获取apikey
APIKEY=${MX_APIKEY:-$DEFAULT_APIKEY}

# 检查参数
if [ -z "$1" ]; then
    echo "用法: bash query.sh \"查询内容\""
    echo "示例: bash query.sh \"000516最新价\""
    exit 1
fi

QUERY="$1"

# 调用API
curl -s -X POST 'https://mkapi2.dfcfs.com/finskillshub/api/claw/query' \
  -H 'Content-Type: application/json' \
  -H "apikey: $APIKEY" \
  -d "{\"toolQuery\": \"$QUERY\"}" | python3 -m json.tool 2>/dev/null || cat

echo ""