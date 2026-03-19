---
name: upstream-sync
description: 自动同步 upstream/main 到 remote/dev 分支，排除测试文件并生成变更报告。用于保持 remote/dev 分支与上游同步，包含新增功能、bug 修复、重构和 breaking changes 分析。触发条件：当需要同步 upstream/main 到 remote/dev 时使用。
---

# Upstream Sync Skill

## 快速开始

运行同步脚本：

```bash
~/.openclaw/skills/upstream-sync/scripts/sync-upstream.sh
```

脚本会：
1. 获取 upstream/main 最新代码
2. 合并到 remote/dev 分支（排除测试文件）
3. 生成变更报告

## 报告内容

生成的报告包含：
- **新增内容**：文件级别的新增统计
- **新特性 (feat)**：feature 类型的 commit
- **Bug 修复 (fix)**：fix 类型的 commit
- **重构 (refactor)**：refactor 类型的 commit
- **Breaking Changes**：可能导致破坏性变更的 commit
- **冲突解决**：合并冲突及解决方式

## 配置

如需修改排除模式，编辑脚本中的 `EXCLUDE_PATTERNS` 变量。