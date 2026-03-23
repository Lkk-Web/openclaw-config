#!/usr/bin/env python3
"""
Knowledge Graph Skill 执行器
"""

import sys
import os
import subprocess

SCRIPT_DIR = os.path.expanduser("~/.openclaw/scripts/snapshot")

def run_command(cmd):
    """运行 shell 命令"""
    result = subprocess.run(
        cmd, 
        shell=True, 
        capture_output=True, 
        text=True
    )
    return result.stdout, result.returncode

def handle_graph(args):
    """处理图谱请求"""
    if not args or args[0] == "daily" or args[0] == "today":
        cmd = f"python3 {SCRIPT_DIR}/export-graph.py daily"
    elif args[0] == "session" and len(args) > 1:
        session_id = args[1]
        cmd = f"python3 {SCRIPT_DIR}/export-graph.py session {session_id}"
    elif args[0] == "stats" or args[0] == "info":
        cmd = f"ls -la {os.path.expanduser('~/.openclaw/memory/graphs/')}"
    else:
        return f"未知命令: {args[0]}\n可用命令: daily, session <id>, stats"
    
    output, code = run_command(cmd)
    
    if code == 0:
        return output
    else:
        return f"错误: {output}"

def check_skill_trigger(user_input):
    """检查是否触发图谱技能"""
    triggers = ["knowledge graph", "知识图谱", "图谱", "entity", "关系", "导出图谱", "graph"]
    return any(t in user_input.lower() for t in triggers)

if __name__ == "__main__":
    # 从参数获取输入
    user_input = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    
    # 如果没有直接输入，尝试从 stdin 读取
    if not user_input:
        try:
            user_input = input("请输入图谱命令: ")
        except:
            user_input = "daily"
    
    # 解析命令
    args = user_input.split()
    
    # 执行
    if check_skill_trigger(user_input):
        result = handle_graph(args)
        print(result)
    else:
        print("未识别为图谱命令")