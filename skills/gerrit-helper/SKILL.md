---
name: gerrit-helper
description: Gerrit code review workflow helper. Use when user needs to push code to Gerrit, update patchsets, or manage code reviews.
---

# Gerrit Helper

Gerrit 代码评审工作流助手，帮助开发者快速完成代码推送和评审管理。

## 使用场景

- 首次提交代码到 Gerrit
- 更新已有的 patchset
- 安装 Change-Id hook
- 查看 Gerrit 推送状态

## 工作流程

### 1. 首次提交

```bash
cd <project-directory>
git add .
git commit -m "feat: your change message [JIRA-LINK]"
BRANCH=$(git branch --show-current)
git push origin HEAD:refs/for/$BRANCH
```

**说明：**
- 命令会自动使用当前分支名进行推送
- 常用分支参考：master、main、develop

### 2. 安装 Change-Id hook（如果提示缺失）

```bash
cd <project-directory>
scp -p -P 29418 <user>@<gerrit-host>:hooks/commit-msg .git/hooks/
chmod +x .git/hooks/commit-msg
git commit --amend --no-edit
BRANCH=$(git branch --show-current)
git push origin HEAD:refs/for/$BRANCH
```

**常见 Gerrit 主机：**
- `gerrit.casstime.net` - Casstime Gerrit
- 端口通常是 `29418`

### 3. 更新同一个评审（patchset）

```bash
cd <project-directory>
git add .
git commit --amend
BRANCH=$(git branch --show-current)
git push origin HEAD:refs/for/$BRANCH
```

> **重要**：保持同一个 Change-Id 会更新原 review，而不是创建新的

## 提交信息规范

### 格式要求

```
<type>: <subject> [<jira-link>]

<body>
```

### Type 类型

- `feat` - 新增功能
- `fix` - 修复 bug
- `docs` - 文档更新
- `style` - 代码格式调整
- `refactor` - 重构
- `test` - 测试相关
- `chore` - 构建/工具相关

### 示例

```bash
git commit -m "feat: 支持本地开发环境查看swagger文档 [https://jira.casstime.com/browse/TERMINAL-001]"
```

## 常见问题

### Q1: 提示 "missing Change-Id"

**解决方案**：安装 Change-Id hook（见上方步骤 2）

### Q2: 如何查看 Gerrit 链接

推送成功后，终端会显示类似：
```
remote: http://gerrit.casstime.net:8087/c/project-name/+/327282
```

### Q3: 如何放弃当前修改

```bash
git reset --hard HEAD
git clean -fd
```

### Q4: 如何切换到其他 patchset

```bash
git fetch origin refs/changes/82/327282/1
git checkout FETCH_HEAD
```

## 使用建议

1. **提交前检查**：确保代码已通过本地测试
2. **提交信息清晰**：包含 Jira 链接和清晰的描述
3. **及时响应评审**：收到评审意见后及时修改
4. **保持 Change-Id**：更新 patchset 时使用 `--amend`

## 相关链接

- Gerrit 文档：https://gerrit-review.googlesource.com/Documentation/
- Git 文档：https://git-scm.com/doc
