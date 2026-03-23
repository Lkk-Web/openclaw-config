#!/usr/bin/env python3
"""
LLM 摘要提取脚本
使用现有 LLM API 对会话进行摘要
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime

# 配置 LLM API
CASS_BASE_URL = os.environ.get("CASS_BASE_URL", "")
CASS_API_KEY = os.environ.get("CASS_API_KEY", "")

if CASS_BASE_URL and CASS_API_KEY:
    USE_CASS = True
    print(f"✅ 使用 CASS API: {CASS_BASE_URL}")
else:
    USE_CASS = False
    print("⚠️ 未配置 CASS_API_KEY，使用模拟模式")

DB_PATH = os.path.expanduser("~/.openclaw/memory/snapshot.db")

def call_llm(prompt, system_prompt=None, max_retries=3):
    """调用 LLM 进行摘要"""
    if USE_CASS:
        import urllib.request
        import json
        import time
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        for attempt in range(max_retries):
            try:
                data = json.dumps({
                    "model": "MiniMax-M2.5",
                    "messages": messages,
                    "max_tokens": 2000
                }).encode('utf-8')
                
                req = urllib.request.Request(
                    f"{CASS_BASE_URL}/v1/chat/completions",
                    data=data,
                    headers={
                        "Authorization": f"Bearer {CASS_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    method="POST"
                )
                
                with urllib.request.urlopen(req, timeout=60) as response:
                    result = json.loads(response.read().decode('utf-8'))
                
                return result["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"  ⚠️ 第 {attempt+1} 次尝试失败: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                continue
        
        print(f"❌ CASS API 调用失败 (已重试 {max_retries} 次)")
        return None
    else:
        # 模拟模式 - 简单返回摘要
        return f"[模拟摘要] 对话内容涉及: {prompt[:100]}..."

def generate_summary(session_id, messages):
    """为会话生成摘要"""
    if not messages:
        return None
    
    # 构建摘要提示 - 限制总长度以避免 API 超载
    conversation_text = "\n".join([
        f"{msg['role']}: {msg['content'][:300]}"
        for msg in messages[:5]  # 限制消息数量
    ])
    
    # 如果太长，进一步截断
    if len(conversation_text) > 1500:
        conversation_text = conversation_text[:1500]
    
    system_prompt = """你是一个对话摘要助手。请分析下面的对话内容，生成一个简洁的摘要，包括：
1. 对话的主要话题和目的
2. 用户请求的关键内容
3. AI 采取的主要行动
4. 结果或结论

请用中文回复，摘要长度控制在 200-500 字之间。"""
    
    prompt = f"""请为以下对话生成摘要：

{conversation_text}

摘要："""
    
    summary_content = call_llm(prompt, system_prompt)
    
    if summary_content:
        # 提取关键词
        keywords = extract_keywords(conversation_text)
        
        return {
            "summary_id": str(uuid.uuid4()),
            "content": summary_content,
            "keywords": ",".join(keywords)
        }
    
    return None

def extract_keywords(text):
    """简单的关键词提取"""
    # 常见关键词模式
    patterns = [
        "浏览器", "搜索", "打开", "创建", "开发", "代码", "测试",
        "API", "数据库", "文件", "下载", "上传", "登录", "查询",
        "修改", "删除", "添加", "执行", "运行", "编译"
    ]
    
    found = [p for p in patterns if p in text]
    return found[:5] if found else ["通用对话"]

def summarize_session(session_id, agent_id="main"):
    """对指定会话进行摘要"""
    if not os.path.exists(DB_PATH):
        print("❌ 数据库不存在")
        return None
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取会话消息
    cursor.execute("""
        SELECT message_id, role, content, timestamp, token_count
        FROM messages 
        WHERE session_id = ?
        ORDER BY timestamp
    """, (session_id,))
    
    rows = cursor.fetchall()
    
    if not rows:
        print(f"⚠️ 会话 {session_id} 没有消息")
        conn.close()
        return None
    
    messages = []
    total_tokens = 0
    for row in rows:
        messages.append({
            "message_id": row[0],
            "role": row[1],
            "content": row[2] or "",
            "timestamp": row[3],
            "token_count": row[4] or 0
        })
        total_tokens += row[4] or 0
    
    # 生成摘要
    print(f"📝 正在为会话 {session_id[:16]}... 生成摘要 (共 {len(messages)} 条消息, {total_tokens} tokens)")
    
    summary = generate_summary(session_id, messages)
    
    if summary:
        # 保存摘要到数据库
        cursor.execute("""
            INSERT INTO summaries (summary_id, snapshot_id, session_id, content, keywords, created_at, model_used)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            summary["summary_id"],
            f"snap_{session_id[:8]}",
            session_id,
            summary["content"],
            summary["keywords"],
            datetime.now().isoformat(),
            "cass-gpt/MiniMax-M2.5" if USE_CASS else "mock"
        ))
        
        conn.commit()
        
        print(f"✅ 摘要生成完成:")
        print(f"   ID: {summary['summary_id']}")
        print(f"   关键词: {summary['keywords']}")
        print(f"   内容: {summary['content'][:200]}...")
    
    conn.close()
    return summary

def summarize_all_sessions(agent_id="main", min_tokens=1000):
    """对所有会话进行摘要"""
    if not os.path.exists(DB_PATH):
        print("❌ 数据库不存在")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取需要摘要的会话
    cursor.execute("""
        SELECT session_id, SUM(token_count) as total_tokens
        FROM messages
        GROUP BY session_id
        HAVING total_tokens >= ?
        ORDER BY total_tokens DESC
    """, (min_tokens,))
    
    sessions = cursor.fetchall()
    conn.close()
    
    print(f"📊 找到 {len(sessions)} 个会话需要摘要 (最少 {min_tokens} tokens)")
    
    for session_id, tokens in sessions:
        print(f"\n处理会话: {session_id[:16]}... ({tokens} tokens)")
        summarize_session(session_id, agent_id)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "session" and len(sys.argv) > 2:
            summarize_session(sys.argv[2])
        elif sys.argv[1] == "all":
            min_tokens = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
            summarize_all_sessions(min_tokens=min_tokens)
        else:
            print("Usage:")
            print("  python summarizer.py session <session_id>  - 摘要单个会话")
            print("  python summarizer.py all [min_tokens]      - 摘要所有会话")
    else:
        print("Usage:")
        print("  python summarizer.py session <session_id>  - 摘要单个会话")
        print("  python summarizer.py all [min_tokens]      - 摘要所有会话")