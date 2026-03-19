#!/bin/bash
#=============================================================================
# 每日快照主入口脚本
# 功能：整合所有快照相关功能
#=============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENCLAW_DIR="$HOME/.openclaw"
MEMORY_DIR="$OPENCLAW_DIR/memory"
GRAPH_DIR="$MEMORY_DIR/graphs"
DB_PATH="$MEMORY_DIR/snapshot.db"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

#=============================================================================
# 初始化数据库
#=============================================================================
init_db() {
    log_info "初始化数据库..."
    python3 "$SCRIPT_DIR/init-db.py"
}

#=============================================================================
# 导入会话数据
#=============================================================================
import_sessions() {
    local limit=${1:-10}
    log_info "导入最近 $limit 个会话..."
    python3 "$SCRIPT_DIR/read-jsonl.py" import $limit
}

#=============================================================================
# 生成摘要
#=============================================================================
generate_summary() {
    local session_id=$1
    
    if [ -z "$session_id" ]; then
        log_info "为所有高 token 会话生成摘要..."
        python3 "$SCRIPT_DIR/summarizer.py" all 5000
    else
        log_info "为会话 $session_id 生成摘要..."
        python3 "$SCRIPT_DIR/summarizer.py" session "$session_id"
    fi
}

#=============================================================================
# 导出知识图谱
#=============================================================================
export_graph() {
    local snapshot_id=$1
    
    if [ -z "$snapshot_id" ]; then
        log_info "导出今日图谱..."
        python3 "$SCRIPT_DIR/export-graph.py" daily
    else
        log_info "导出图谱: $snapshot_id"
        python3 "$SCRIPT_DIR/export-graph.py" session "$snapshot_id"
    fi
}

#=============================================================================
# 检查 token 阈值
#=============================================================================
check_tokens() {
    python3 "$SCRIPT_DIR/read-jsonl.py" tokens
}

#=============================================================================
# 完整快照流程
#=============================================================================
full_snapshot() {
    log_info "========== 开始完整快照流程 =========="
    
    # 1. 初始化数据库
    init_db
    
    # 2. 导入会话数据
    import_sessions 20
    
    # 3. 生成摘要
    generate_summary
    
    # 4. 导出图谱
    export_graph
    
    log_info "========== 快照流程完成 =========="
}

#=============================================================================
# 40K Token 阈值检测
#=============================================================================
check_threshold() {
    local threshold=${1:-40000}
    
    log_info "检查 token 阈值 (>= $threshold)..."
    
    # 读取并计算总 token
    python3 "$SCRIPT_DIR/read-jsonl.py" tokens | while read line; do
        tokens=$(echo "$line" | grep -oE '[0-9]+ tokens' | grep -oE '[0-9]+')
        if [ ! -z "$tokens" ] && [ "$tokens" -ge "$threshold" ]; then
            log_warn "会话 token 达到阈值: $tokens >= $threshold"
            return 1  # 触发快照
        fi
    done
    
    if [ $? -eq 1 ]; then
        log_warn "Token 阈值触发快照!"
        full_snapshot
    else
        log_info "Token 未达到阈值"
    fi
}

#=============================================================================
# 帮助信息
#=============================================================================
show_help() {
    echo "用法: $0 <command> [options]"
    echo ""
    echo "命令:"
    echo "  init              初始化数据库"
    echo "  import [limit]    导入会话数据 (默认 10)"
    echo "  summary [session] 生成摘要 (可选指定会话)"
    echo "  graph [snapshot]  导出图谱 (可选指定快照)"
    echo "  tokens            检查 token 使用情况"
    echo "  full              执行完整快照流程"
    echo "  threshold [n]     检查 token 阈值 (默认 40K)"
    echo "  help              显示帮助"
    echo ""
    echo "示例:"
    echo "  $0 init                    # 初始化数据库"
    echo "  $0 import 20              # 导入最近 20 个会话"
    echo "  $0 full                   # 执行完整快照"
    echo "  $0 threshold 40000        # 检查 40K 阈值"
}

#=============================================================================
# 主程序
#=============================================================================
case "${1:-help}" in
    init)
        init_db
        ;;
    import)
        import_sessions ${2:-10}
        ;;
    summary)
        generate_summary $2
        ;;
    graph)
        export_graph $2
        ;;
    tokens)
        check_tokens
        ;;
    full)
        full_snapshot
        ;;
    threshold)
        check_threshold ${2:-40000}
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "未知命令: $1"
        show_help
        exit 1
        ;;
esac