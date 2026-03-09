#!/bin/bash
# Tavily 搜索脚本

QUERY="$1"
MAX_RESULTS="${2:-5}"

if [ -z "$QUERY" ]; then
    echo "用法: $0 <搜索关键词> [结果数量]"
    exit 1
fi

if [ -z "$TAVILY_API_KEY" ]; then
    echo "错误: 未找到 TAVILY_API_KEY"
    exit 1
fi

curl -s -X POST "https://api.tavily.com/search" \
  -H "Content-Type: application/json" \
  -d "{
    \"api_key\": \"$TAVILY_API_KEY\",
    \"query\": \"$QUERY\",
    \"max_results\": $MAX_RESULTS
  }"
