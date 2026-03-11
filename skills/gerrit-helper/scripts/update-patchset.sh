#!/bin/bash
# Gerrit patchset 更新助手

set -e

# 检查参数
if [ $# -lt 2 ]; then
    echo "用法: $0 <project-dir> <target-branch>"
    echo "示例: $0 /path/to/project master"
    exit 1
fi

PROJECT_DIR="$1"
TARGET_BRANCH="$2"

cd "$PROJECT_DIR"

echo "📁 工作目录: $PROJECT_DIR"
echo "🌿 目标分支: $TARGET_BRANCH"
echo ""

# 检查是否有未提交的更改
if ! git diff-index --quiet HEAD --; then
    echo "✅ 发现未提交的更改，准备更新 patchset..."
    git add .
    git commit --amend --no-edit
else
    echo "ℹ️  没有未提交的更改，直接推送现有 commit"
fi

# 推送到 Gerrit
echo ""
echo "🚀 更新 patchset..."
git push origin HEAD:refs/for/"$TARGET_BRANCH"

echo ""
echo "✅ Patchset 已更新！"
