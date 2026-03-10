# TOOLS.md - 工具使用指南

## Git & Gerrit

### Gerrit 代码推送流程

**1. 首次提交**
```bash
git add .
git commit -m "your change message"
git push origin HEAD:refs/for/<target-branch>
```

**2. 安装 Change-Id hook（如果提示缺失）**
```bash
scp -p -P 29418 <user>@<gerrit-host>:hooks/commit-msg .git/hooks/
chmod +x .git/hooks/commit-msg
git commit --amend --no-edit
git push origin HEAD:refs/for/<target-branch>
```

**3. 更新同一个评审（patchset）**
```bash
git add .
git commit --amend
git push origin HEAD:refs/for/<target-branch>
```

> 保持同一个 Change-Id 会更新原 review，而不是创建新的

**常用分支：**
- `refs/for/master` - 推送到 master 分支
- `refs/for/main` - 推送到 main 分支
- `refs/for/develop` - 推送到 develop 分支

---

## Skills 管理

### 添加 Skill 到 Agent
```bash
cp -r <source-skill-path> ~/.openclaw/agents/<agent-id>/workspace/skills/
openclaw gateway restart
```

### 查看可用 Skills
```bash
ls ~/Desktop/github/openclaw/skills/
ls ~/.openclaw/skills/
ls ~/.openclaw/agents/main/workspace/skills/
```
