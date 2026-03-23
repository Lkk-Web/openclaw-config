#!/usr/bin/env python3
"""
对话读取脚本
从 JSONL 文件中读取对话数据并解析
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
import re

SESSIONS_DIR = os.path.expanduser("~/.openclaw/agents/main/sessions")
DB_PATH = os.path.expanduser("~/.openclaw/memory/snapshot.db")

def get_text_content(content_list):
    """从消息内容中提取纯文本"""
    if not content_list:
        return ""
    
    text_parts = []
    for item in content_list:
        if isinstance(item, dict):
            if item.get("type") == "text":
                text_parts.append(item.get("text", ""))
            elif item.get("type") == "toolCall":
                # 提取工具调用信息
                tool_name = item.get("name", "unknown")
                args = item.get("arguments", {})
                text_parts.append(f"[Tool: {tool_name}]")
        elif isinstance(item, str):
            text_parts.append(item)
    
    return "\n".join(text_parts)

def parse_session_file(filepath):
    """解析单个 session 文件"""
    sessions = []
    messages = []
    tools = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                data = json.loads(line)
                record_type = data.get("type")
                
                if record_type == "session":
                    sessions.append({
                        "session_id": data.get("id"),
                        "agent_id": "main",
                        "timestamp": data.get("timestamp"),
                        "cwd": data.get("cwd")
                    })
                
                elif record_type == "message":
                    msg_data = data.get("message", {})
                    role = msg_data.get("role")
                    content = msg_data.get("content", [])
                    
                    # 提取 token 使用量
                    usage = msg_data.get("usage", {})
                    token_count = usage.get("totalTokens", 0) if usage else 0
                    
                    messages.append({
                        "message_id": data.get("id"),
                        "session_id": data.get("parentId", "").split("-")[0] if data.get("parentId") else "",
                        "parent_id": data.get("parentId"),
                        "role": role,
                        "content": get_text_content(content),
                        "timestamp": data.get("timestamp"),
                        "token_count": token_count
                    })
                    
                    # 处理工具调用
                    for content_item in content:
                        if isinstance(content_item, dict) and content_item.get("type") == "toolCall":
                            tool_call_id = content_item.get("id")
                            tool_name = content_item.get("name")
                            tool_args = json.dumps(content_item.get("arguments", {}))
                            
                            tools.append({
                                "tool_id": tool_call_id,
                                "message_id": data.get("id"),
                                "tool_name": tool_name,
                                "arguments": tool_args,
                                "is_error": 0
                            })
                
                elif record_type == "toolResult":
                    tool_call_id = data.get("toolCallId")
                    tool_result_content = data.get("content", [])
                    result_text = get_text_content(tool_result_content)
                    is_error = 1 if data.get("isError", False) else 0
                    
                    # 更新工具结果
                    for tool in tools:
                        if tool["tool_id"] == tool_call_id:
                            tool["result"] = result_text[:5000]  # 限制长度
                            tool["is_error"] = is_error
                            break
                            
            except json.JSONDecodeError:
                continue
    
    return sessions, messages, tools

def import_sessions(agent_id="main", limit=None):
    """导入 session 数据到数据库"""
    if not os.path.exists(DB_PATH):
        print("❌ 数据库不存在，请先运行 init-db.py")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取所有 session 文件
    session_files = sorted(
        Path(SESSIONS_DIR).glob("*.jsonl*"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    if limit:
        session_files = session_files[:limit]
    
    total_sessions = 0
    total_messages = 0
    total_tools = 0
    
    for session_file in session_files:
        sessions, messages, tools = parse_session_file(session_file)
        
        for session in sessions:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO sessions 
                    (session_id, agent_id, started_at, cwd, message_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    session["session_id"],
                    session["agent_id"],
                    session["timestamp"],
                    session["cwd"],
                    len([m for m in messages if m["session_id"] == session["session_id"]])
                ))
                total_sessions += 1
            except sqlite3.IntegrityError:
                pass
        
        # 导入消息
        for msg in messages:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO messages
                    (message_id, session_id, parent_id, role, content, timestamp, token_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    msg["message_id"],
                    msg["session_id"],
                    msg["parent_id"],
                    msg["role"],
                    msg["content"][:10000],  # 限制内容长度
                    msg["timestamp"],
                    msg["token_count"]
                ))
                total_messages += 1
            except sqlite3.IntegrityError:
                pass
        
        # 导入工具调用
        for tool in tools:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO tools
                    (tool_id, session_id, message_id, tool_name, arguments, result, is_error, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    tool["tool_id"],
                    tool["message_id"].split("-")[0] if tool["message_id"] else "",
                    tool["message_id"],
                    tool["tool_name"],
                    tool["arguments"],
                    tool.get("result", ""),
                    tool["is_error"]
                ))
                total_tools += 1
            except sqlite3.IntegrityError:
                pass
    
    conn.commit()
    conn.close()
    
    print(f"✅ 导入完成:")
    print(f"   - 会话: {total_sessions}")
    print(f"   - 消息: {total_messages}")
    print(f"   - 工具: {total_tools}")

def get_session_tokens(session_id):
    """获取指定会话的 token 总数"""
    if not os.path.exists(DB_PATH):
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT SUM(token_count) FROM messages WHERE session_id = ?
    """, (session_id,))
    
    result = cursor.fetchone()[0]
    conn.close()
    
    return result or 0

def get_all_active_sessions():
    """获取所有活跃会话及其 token 数量"""
    if not os.path.exists(DB_PATH):
        return []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT session_id, SUM(token_count) as total_tokens 
        FROM messages 
        GROUP BY session_id 
        ORDER BY total_tokens DESC
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    return [{"session_id": r[0], "tokens": r[1] or 0} for r in results]

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "import":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
            import_sessions(limit=limit)
        elif sys.argv[1] == "tokens":
            session_id = sys.argv[2] if len(sys.argv) > 2 else None
            if session_id:
                print(f"Session {session_id}: {get_session_tokens(session_id)} tokens")
            else:
                sessions = get_all_active_sessions()
                print("Active sessions:")
                for s in sessions[:10]:
                    print(f"  {s['session_id'][:20]}...: {s['tokens']} tokens")
    else:
        print("Usage:")
        print("  python read-jsonl.py import [limit]  - 导入会话数据")
        print("  python read-jsonl.py tokens [session_id]  - 查看 token 使用情况")