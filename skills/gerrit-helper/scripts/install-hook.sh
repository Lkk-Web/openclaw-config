#!/bin/bash
# Gerrit Change-Id hook 安装助手

set -e

# 检查参数
if [ $# -lt 3 ]; then
    echo "用法: $0 <project-dir> <gerrit-user> <gerrit-host>"
    echo "示例: $0 /path/to/project a05608 gerrit.casstime.net"
    exit 1
fi

PROJECT_DIR="$1"
GERRIT_USER="$2"
GERRIT_HOST="$3"
GERRIT_PORT="${4:-29418}"

cd "$PROJECT_DIR"

echo "📁 工作目录: $PROJECT_DIR"
echo "👤 Gerrit 用户: $GERRIT_USER"
echo "🌐 Gerrit 主机: $GERRIT_HOST:$GERRIT_PORT"
echo ""

# 下载 hook
echo "📥 下载 Change-Id hook..."
scp -p -P "$GERRIT_PORT" "$GERRIT_USER@$GERRIT_HOST:hooks/commit-msg" .git/hooks/

# 设置执行权限
echo "🔧 设置执行权限..."
chmod +x .git/hooks/commit-msg

# 修改最后一次提交以添加 Change-Id
echo "✏️  修改最后一次提交..."
git commit --amend --no-edit

echo ""
echo "✅ Change-Id hook 安装完成！"
echo "💡 现在可以推送到 Gerrit 了"
