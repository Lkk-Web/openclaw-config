#!/bin/bash
#=============================================================================
# Daily Snapshot - 定时任务配置脚本
# 功能：自动创建每日 4 点的 cron job
#=============================================================================

SKILL_DIR="$HOME/.openclaw/skills/daily-snapshot"
SCRIPT_PATH="$SKILL_DIR/script.py"
CONFIG_FILE="$SKILL_DIR/config.env"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

#=============================================================================
# 检查依赖
#=============================================================================
check_dependencies() {
    log_step "检查依赖..."

    # 检查 Python3
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装，请先安装 Python3"
        exit 1
    fi

    # 检查脚本文件
    if [ ! -f "$SCRIPT_PATH" ]; then
        log_error "脚本文件不存在: $SCRIPT_PATH"
        exit 1
    fi

    log_info "依赖检查通过"
}

#=============================================================================
# 配置环境变量
#=============================================================================
setup_environment() {
    log_step "配置环境变量..."

    # 检查配置文件
    if [ ! -f "$CONFIG_FILE" ]; then
        log_warn "配置文件不存在，正在创建..."

        # 复制模板
        cp "$SKILL_DIR/config.env.example" "$CONFIG_FILE"

        log_error "请编辑配置文件并填入 API Key:"
        echo "  nano $CONFIG_FILE"
        echo ""
        echo "需要配置:"
        echo "  - CASS_BASE_URL"
        echo "  - CASS_API_KEY"
        echo ""
        echo "配置完成后，重新运行此脚本"

        exit 1
    fi

    # 加载环境变量
    source "$CONFIG_FILE"

    # 检查必需的环境变量
    if [ -z "$CASS_BASE_URL" ] || [ -z "$CASS_API_KEY" ]; then
        log_error "环境变量未配置完整，请编辑 $CONFIG_FILE"
        echo ""
        echo "需要配置:"
        [ -z "$CASS_BASE_URL" ] && echo "  - CASS_BASE_URL"
        [ -z "$CASS_API_KEY" ] && echo "  - CASS_API_KEY"

        exit 1
    fi

    log_info "环境变量已加载: CASS_BASE_URL=$CASS_BASE_URL"
}

#=============================================================================
# 初始化数据库
#=============================================================================
init_database() {
    log_step "初始化数据库..."

    # 确保 memory 目录存在
    mkdir -p "$HOME/.openclaw/memory"

    # 运行初始化
    python3 "$SCRIPT_PATH" init

    if [ $? -eq 0 ]; then
        log_info "数据库初始化完成"
    else
        log_warn "数据库初始化遇到问题，继续配置 cron..."
    fi
}

#=============================================================================
# 配置 Cron 任务
#=============================================================================
setup_cron() {
    log_step "配置定时任务..."

    # 构建 cron 命令
    CRON_CMD="0 4 * * * cd $SKILL_DIR && source $CONFIG_FILE > /dev/null 2>&1 && python3 $SCRIPT_PATH full >> $HOME/.openclaw/logs/daily-snapshot.log 2>&1"

    # 检查是否已存在相同的 cron 任务
    EXISTING_CRON=$(crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH" && echo "yes" || echo "no")

    if [ "$EXISTING_CRON" = "yes" ]; then
        log_warn "定时任务已存在，先移除旧任务..."
        # 移除旧的 cron 任务
        crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH" | crontab -
    fi

    # 添加新的 cron 任务
    echo "$CRON_CMD" | crontab -

    log_info "定时任务已配置完成"
}

#=============================================================================
# 验证配置
#=============================================================================
verify_setup() {
    log_step "验证配置..."

    # 显示当前的 crontab
    echo ""
    echo "当前定时任务:"
    echo "------------------------------------------------------------"
    crontab -l 2>/dev/null | grep "daily-snapshot" || echo "  (无)"
    echo "------------------------------------------------------------"
    echo ""

    # 测试运行
    log_info "测试运行快照脚本..."
    python3 "$SCRIPT_PATH" tokens

    if [ $? -eq 0 ]; then
        log_info "✅ 配置完成！"
    else
        log_warn "脚本测试遇到问题，但 cron 已配置"
    fi
}

#=============================================================================
# 显示使用说明
#=============================================================================
show_usage() {
    echo ""
    echo "========================================"
    echo "  Daily Snapshot 定时任务配置完成"
    echo "========================================"
    echo ""
    echo "📅 执行时间: 每日 04:00"
    echo ""
    echo "📝 管理命令:"
    echo "  查看定时任务:  crontab -l"
    echo "  编辑定时任务:  crontab -e"
    echo "  删除定时任务:  crontab -r"
    echo ""
    echo "📂 日志位置:"
    echo "  $HOME/.openclaw/logs/daily-snapshot.log"
    echo ""
    echo "🔧 手动执行:"
    echo "  python3 $SCRIPT_PATH full"
    echo ""
    echo "========================================"
}

#=============================================================================
# 主程序
#=============================================================================
main() {
    echo "========================================"
    echo "  Daily Snapshot - 定时任务配置"
    echo "========================================"
    echo ""

    check_dependencies
    setup_environment
    init_database
    setup_cron
    verify_setup
    show_usage
}

# 执行主程序
main "$@"