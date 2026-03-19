#!/bin/bash
# upstream-sync: 自动同步 upstream/main 到 remote/dev 分支

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
REPORT_FILE="$SKILL_DIR/sync-report.md"

# 配置
UPSTREAM_REMOTE="upstream"
MAIN_BRANCH="main"
TARGET_BRANCH="remote/dev"
EXCLUDE_PATTERN="*.test.ts,*.spec.ts,*.test.js,*.spec.js,*.test.tsx,*.spec.tsx,*.test.scss,*.spec.scss"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查 git 仓库
if [ ! -d ".git" ]; then
    log_error "当前目录不是 git 仓库"
    exit 1
fi

# 检查 upstream remote 是否存在
if ! git remote get-url "$UPSTREAM_REMOTE" &>/dev/null; then
    log_info "添加 upstream remote: https://github.com/openclaw/openclaw.git"
    git remote add upstream https://github.com/openclaw/openclaw.git 2>/dev/null || true
fi

# 获取 upstream/main 最新代码
log_info "Fetching upstream/main..."
git fetch upstream

# 记录合并前的 commit 数
PREV_COMMITS=$(git rev-list --count "$TARGET_BRANCH"..upstream/main 2>/dev/null || echo "0")
log_info " upstream/main 领先 remote/dev: $PREV_COMMITS commits"

# 执行合并（排除测试文件）
log_info "Merging upstream/main to $TARGET_BRANCH..."

# 保存当前分支
CURRENT_BRANCH=$(git branch --show-current)

# 切换到目标分支
git checkout "$TARGET_BRANCH"

# 尝试合并
MERGE_RESULT=0
git merge upstream/main --no-edit || MERGE_RESULT=$?

# 处理合并冲突
if [ $MERGE_RESULT -ne 0 ]; then
    log_warn "检测到合并冲突，正在分析..."
    
    # 获取冲突文件列表
    CONFLICT_FILES=$(git diff --name-only --diff-filter=U)
    
    # 只保留非测试文件的冲突解决
    for file in $CONFLICT_FILES; do
        if echo "$file" | grep -qE "\.(test|spec)\.(ts|js|tsx|scss)$"; then
            log_info "放弃测试文件冲突: $file"
            git checkout --theirs "$file"
            git add "$file"
        else
            log_info "解决冲突: $file"
            # 使用 ours 策略（保留本地 remote/dev 的版本）
            git checkout --ours "$file"
            git add "$file"
        fi
    done
    
    # 完成合并
    git commit --no-edit || true
    log_success "冲突已解决并提交"
fi

# 生成变更报告
log_info "生成变更报告..."

# 获取变更的 commit 列表
COMMITS=$(git log --pretty=format:"%h|%s|%an" "$TARGET_BRANCH"..upstream/main 2>/dev/null || git log --pretty=format:"%h|%s|%an" -10)

# 分类统计
FEATURES=$(echo "$COMMITS" | grep -i "^[^|]*|.*feat:" || true)
FIXES=$(echo "$COMMITS" | grep -i "^[^|]*|.*fix:" || true)
REFACTORS=$(echo "$COMMITS" | grep -i "^[^|]*|.*refactor:" || true)
BREAKING=$(echo "$COMMITS" | grep -i -E "BREAKING|breaking\s+change" || true)

# 获取新增文件（排除测试）
NEW_FILES=$(git diff --name-only "$TARGET_BRANCH"..upstream/main 2>/dev/null | grep -vE "\.(test|spec)\.(ts|js|tsx|scss)$" || true)

# 统计
FEATURE_COUNT=$(echo "$FEATURES" | grep -c "^" || echo "0")
FIX_COUNT=$(echo "$FIXES" | grep -c "^" || echo "0")
REFACTOR_COUNT=$(echo "$REFACTORS" | grep -c "^" || echo "0")
BREAKING_COUNT=$(echo "$BREAKING" | grep -c "^" || echo "0")
NEW_FILE_COUNT=$(echo "$NEW_FILES" | grep -c "^" || echo "0")

# 写入报告
cat > "$REPORT_FILE" << EOF
# Upstream Sync 报告

**同步时间**: $(date '+%Y-%m-%d %H:%M:%S')
**上游分支**: upstream/main
**目标分支**: $TARGET_BRANCH
**同步 commit 数**: $PREV_COMMITS

## 变更摘要

| 类型 | 数量 |
|------|------|
| 新增文件 | $NEW_FILE_COUNT |
| 新特性 (feat) | $FEATURE_COUNT |
| Bug 修复 (fix) | $FIX_COUNT |
| 重构 (refactor) | $REFACTOR_COUNT |
| Breaking Changes | $BREAKING_COUNT |

## 新增文件（排除测试）

\`\`\`
$NEW_FILES
\`\`\`

## 新特性 (feat)

\`\`\`
$FEATURES
\`\`\`

## Bug 修复 (fix)

\`\`\`
$FIXES
\`\`\`

## 重构 (refactor)

\`\`\`
$REFACTORS
\`\`\`

## Breaking Changes

\`\`\`
$BREAKING
\`\`\`

## 冲突解决

EOF

# 添加冲突信息
if [ $MERGE_RESULT -ne 0 ]; then
    echo "**存在合并冲突，已自动解决**" >> "$REPORT_FILE"  
    echo "" >> "$REPORT_FILE"
    echo "解决的冲突文件:" >> "$REPORT_FILE"
    echo "\`\`\`" >> "$REPORT_FILE"
    echo "$CONFLICT_FILES" >> "$REPORT_FILE"
    echo "\`\`\`" >> "$REPORT_FILE"
else
    echo "无合并冲突" >> "$REPORT_FILE"
fi

# 切回原分支
if [ -n "$CURRENT_BRANCH" ] && [ "$CURRENT_BRANCH" != "$TARGET_BRANCH" ]; then
    git checkout "$CURRENT_BRANCH"
fi

log_success "同步完成！"
log_info "报告已生成: $REPORT_FILE"

# 显示报告摘要
echo ""
echo "=== 变更摘要 ==="
echo "新特性: $FEATURE_COUNT"
echo "Bug 修复: $FIX_COUNT"
echo "重构: $REFACTOR_COUNT"
echo "Breaking Changes: $BREAKING_COUNT"
echo "新增文件: $NEW_FILE_COUNT"