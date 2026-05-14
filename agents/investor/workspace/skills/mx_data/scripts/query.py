#!/usr/bin/env python3
"""
妙想金融数据查询工具
用法: python query.py "查询内容"
"""

import os
import sys
import json
import requests

DEFAULT_APIKEY = "mkt_FlyBm_-6IkomvaVRPEbcqbcehxLia0tu7LUAE7vrlZU"
API_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/query"

def query(query_text: str, apikey: str = None) -> dict:
    """查询金融数据"""
    key = apikey or os.environ.get("MX_APIKEY", DEFAULT_APIKEY)
    
    headers = {
        "Content-Type": "application/json",
        "apikey": key
    }
    
    data = {"toolQuery": query_text}
    
    try:
        response = requests.post(API_URL, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def parse_result(result: dict) -> str:
    """解析返回结果"""
    if "error" in result:
        return f"查询失败: {result['error']}"
    
    try:
        data = result.get("data", {})
        table_list = data.get("dataTableDTOList", [])
        
        if not table_list:
            return "未找到相关数据"
        
        outputs = []
        for item in table_list:
            code = item.get("code", "N/A")
            name = item.get("entityName", item.get("title", ""))
            table = item.get("table", {})
            name_map = item.get("nameMap", {})
            
            outputs.append(f"📊 {name} ({code})")
            
            # 简化显示
            for col, values in table.items():
                col_name = name_map.get(col, col)
                if isinstance(values, list) and values:
                    val = values[-1] if len(values) > 0 else "N/A"
                    outputs.append(f"  {col_name}: {val}")
        
        return "\n".join(outputs) if outputs else "无数据"
    
    except Exception as e:
        return f"解析结果失败: {e}\n原始数据: {json.dumps(result, ensure_ascii=False)[:500]}"

def main():
    if len(sys.argv) < 2:
        print("用法: python query.py \"查询内容\"")
        print("示例: python query.py \"000516最新价\"")
        sys.exit(1)
    
    query_text = " ".join(sys.argv[1:])
    print(f"🔍 查询: {query_text}\n")
    
    result = query(query_text)
    print(parse_result(result))

if __name__ == "__main__":
    main()