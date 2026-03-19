#!/usr/bin/env python3
"""
Daily Snapshot Skill - 每日快照主入口
功能：自动将 OpenClaw 会话数据快照到本地 SQLite 数据库
"""

import os
import sys
import subprocess

# 脚本目录
SCRIPT_DIR = os.path.expanduser("~/.openclaw/scripts/snapshot")

def run_command(cmd):
    """运行 shell 命令"""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    return result.stdout, result.returncode, result.stderr

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
    elif args[0] == "summary":
        session_id = args[1] if len(args) > 1 else None
        if session_id:
            cmd = f"bash {SCRIPT_DIR}/main.sh summary {session_id}"
        else:
            cmd = f"bash {SCRIPT_DIR}/main.sh summary"
    else:
        return f"未知命令: {args[0]}\n可用命令: full, init, import, threshold, graph, tokens, summary"

    stdout, code, stderr = run_command(cmd)

    if code == 0:
        return stdout
    else:
        return f"错误: {stderr}\n{stdout}"

def check_skill_trigger(user_input):
    """检查是否触发快照技能"""
    triggers = ["snapshot", "快照", "每日快照", "daily-snapshot"]
    return any(t in user_input.lower() for t in triggers)

def show_help():
    """显示帮助信息"""
    return """Daily Snapshot Skill - 每日快照

用法: python3 script.py <command> [options]

命令:
  full              执行完整快照流程（默认）
  init              初始化数据库
  import [limit]    导入会话数据 (默认 10)
  summary [session] 生成摘要 (可选指定会话)
  graph [snapshot]  导出图谱 (可选指定快照)
  tokens            检查 token 使用情况
  threshold [n]     检查 token 阈值 (默认 40K)

示例:
  python3 script.py full              # 执行完整快照
  python3 script.py import 20         # 导入最近 20 个会话
  python3 script.py tokens            # 检查 token
  python3 script.py threshold 50000   # 检查 50K 阈值

环境变量:
  CASS_BASE_URL    CASS API 基础地址
  CASS_API_KEY     CASS API 密钥
"""

if __name__ == "__main__":
    # 从参数获取输入
    user_input = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""

    # 如果没有参数，显示帮助
    if not user_input or user_input in ["help", "-h", "--help"]:
        print(show_help())
        sys.exit(0)

    # 解析命令
    args = user_input.split()

    # 执行
    if check_skill_trigger(user_input) or True:  # 始终执行
        result = handle_snapshot(args)
        print(result)
    else:
        print("未识别为快照命令")
        sys.exit(1)