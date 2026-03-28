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

def get_text_content(content_list, role=None):
    """从消息内容中提取纯文本
    
    Args:
        content_list: 消息内容列表
        role: 消息角色 (user/assistant/system)
    """
    if not content_list:
        return ""
    
    text_parts = []
    for item in content_list:
        if isinstance(item, dict):
            if item.get("type") == "text":
                text = item.get("text", "")
                text_parts.append(text)
            elif item.get("type") == "toolCall":
                tool_name = item.get("name", "unknown")
                text_parts.append(f"[Tool: {tool_name}]")
        elif isinstance(item, str):
            text_parts.append(item)
    
    result = "\n".join(text_parts)
    
    # 对于 user 角色，处理特殊格式
    if role == "user" and result:
        # 匹配时间戳前缀模式: [Day Mon DD HH:MM GMT+8]
        result = re.sub(r'^\[[A-Za-z]{3}\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+GMT[+-]?\d+\]\s*', '', result)
        
        # 处理格式: "Conversation info...Sender (untrusted metadata)...实际文本"
        # 找到最后的 "```\n```" 之后的内容
        if '```' in result:
            parts = result.split('```')
            if len(parts) > 2:
                last_part = parts[-1].strip()
                if last_part:
                    result = last_part
    
    return result

def parse_session_file(filepath):
    """解析单个 session 文件"""
    sessions = []
    messages = []
    tools = []
    current_session_id = None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                data = json.loads(line)
                record_type = data.get("type")
                
                if record_type == "session":
                    current_session_id = data.get("id")
                    sessions.append({
                        "session_id": current_session_id,
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
                        "session_id": current_session_id if current_session_id else "",
                        "parent_id": data.get("parentId"),
                        "role": role,
                        "content": get_text_content(content, role=role),
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
                                "session_id": current_session_id if current_session_id else "",
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
                            # 补充 session_id
                            if not tool.get("session_id") and current_session_id:
                                tool["session_id"] = current_session_id
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
    
    # 创建 snapshot 记录（用于增量同步）
    if total_messages > 0:
        cursor.execute("""
            INSERT INTO snapshots (snapshot_id, agent_id, session_id, created_at, trigger_type, status)
            VALUES (?, ?, ?, datetime('now'), 'scheduled', 'completed')
        """, (
            f"snap_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            agent_id,
            session.get("session_id", "unknown") if sessions else "unknown"
        ))
    
    conn.commit()
    
    # 获取导入的会话详情（只显示用户核心问答）
    if total_sessions > 0:
        # 只获取 role='user' 的首条消息
        cursor.execute("""
            SELECT s.session_id, s.started_at, 
                   (SELECT COUNT(*) FROM messages WHERE session_id = s.session_id) as msg_count,
                   (SELECT content FROM messages 
                    WHERE session_id = s.session_id 
                    AND role = 'user' 
                    AND content IS NOT NULL
                    AND content != ''
                    ORDER BY timestamp LIMIT 1) as first_user_msg
            FROM sessions s
            WHERE s.session_id IN (
                SELECT session_id FROM sessions ORDER BY started_at DESC LIMIT ?
            )
        """, (total_sessions,))
        
        session_details = cursor.fetchall()
        
        import re
        print(f"\n📋 核心用户会话:")
        for sid, started_at, msg_count, first_user_msg in session_details:
            if first_user_msg and first_user_msg.strip():
                # 尝试提取纯文本内容
                text_match = re.search(r'(?:text|text\":\")([^\"]+)', first_user_msg)
                if text_match:
                    summary = text_match.group(1)[:60].replace('\n', ' ').strip()
                else:
                    # 清理内容获取前60字符
                    summary = first_user_msg[:60].replace('\n', ' ').strip()
                if len(first_user_msg) > 60:
                    summary += "..."
                # 过滤掉元数据前缀和时间戳
                summary = re.sub(r'^\[Internal.*?\]\s*', '', summary)
                summary = re.sub(r'^\[[A-Za-z]{3}\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+GMT[+-]?\d+\]\s*', '', summary)
            else:
                summary = "(无用户消息)"
            print(f"   • {sid[:12]}... | {msg_count}条消息 | 用户请求：{summary}")
    
    conn.close()
    
    print(f"\n✅ 导入完成")

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