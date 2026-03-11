#!/bin/bash
# Gerrit 首次提交助手

set -e

# 检查参数
if [ $# -lt 3 ]; then
    echo "用法: $0 <project-dir> <commit-message> <target-branch>"
    echo "示例: $0 /path/to/project 'feat: 新功能 [JIRA-123]' master"
    exit 1
fi

PROJECT_DIR="$1"
COMMIT_MSG="$2"
TARGET_BRANCH="$3"

cd "$PROJECT_DIR"

echo "📁 工作目录: $PROJECT_DIR"
echo "📝 提交信息: $COMMIT_MSG"
echo "🌿 目标分支: $TARGET_BRANCH"
echo ""

# 检查是否有未提交的更改
if ! git diff-index --quiet HEAD --; then
    echo "✅ 发现未提交的更改，准备提交..."
    git add .
    git commit -m "$COMMIT_MSG"
else
    echo "ℹ️  没有未提交的更改"
fi

# 推送到 Gerrit
echo ""
echo "🚀 推送到 Gerrit..."
git push origin HEAD:refs/for/"$TARGET_BRANCH"

echo ""
echo "✅ 完成！请查看终端输出中的 Gerrit 链接"
