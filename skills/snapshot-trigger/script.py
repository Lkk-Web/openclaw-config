#!/usr/bin/env python3
"""
Snapshot Trigger Skill 执行器
"""

import sys
import os
import subprocess
import json

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

def handle_snapshot(args):
    """处理快照请求"""
    if not args:
        # 默认执行完整快照
        cmd = f"bash {SCRIPT_DIR}/main.sh full"
    elif args[0] == "full":
        cmd = f"bash {SCRIPT_DIR}/main.sh full"
    elif args[0] == "init":
        cmd = f"bash {SCRIPT_DIR}/main.sh init"
    elif args[0] == "import":
        limit = args[1] if len(args) > 1 else "10"
        cmd = f"bash {SCRIPT_DIR}/main.sh import {limit}"
    elif args[0] == "threshold":
        threshold = args[1] if len(args) > 1 else "40000"
        cmd = f"bash {SCRIPT_DIR}/main.sh threshold {threshold}"
    elif args[0] == "graph":
        cmd = f"bash {SCRIPT_DIR}/main.sh graph"
    elif args[0] == "tokens":
        cmd = f"bash {SCRIPT_DIR}/main.sh tokens"
    else:
        return f"未知命令: {args[0]}\n可用命令: full, init, import, threshold, graph, tokens"
    
    output, code = run_command(cmd)
    
    if code == 0:
        return output
    else:
        return f"错误: {output}"

def check_skill_trigger(user_input):
    """检查是否触发快照技能"""
    triggers = ["snapshot", "快照", "触发器", "阈值", "token", "每日快照"]
    return any(t in user_input.lower() for t in triggers)

if __name__ == "__main__":
    # 从参数获取输入
    user_input = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    
    # 如果没有直接输入，尝试从 stdin 读取
    if not user_input:
        try:
            user_input = input("请输入快照命令: ")
        except:
            user_input = "full"
    
    # 解析命令
    args = user_input.split()
    
    # 执行
    if check_skill_trigger(user_input):
        result = handle_snapshot(args)
        print(result)
    else:
        print("未识别为快照命令")