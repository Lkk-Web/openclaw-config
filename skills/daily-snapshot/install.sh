#!/bin/bash
# Daily Snapshot 一键安装脚本

set -e

SKILL_DIR="$HOME/.openclaw/skills/daily-snapshot"
REPO_URL="https://github.com/Lkk-Web/openclaw-config"
RAW_URL="https://raw.githubusercontent.com/Lkk-Web/openclaw-config/main"

echo "📦 正在安装 Daily Snapshot..."

# 1. 创建目录
mkdir -p "$SKILL_DIR"

# 2. 下载 skill 文件
echo "📥 下载 skill 文件..."
curl -sSL "$RAW_URL/skills/daily-snapshot/script.py" -o "$SKILL_DIR/script.py"
curl -sSL "$RAW_URL/skills/daily-snapshot/SKILL.md" -o "$SKILL_DIR/SKILL.md"
curl -sSL "$RAW_URL/skills/daily-snapshot/config.env.example" -o "$SKILL_DIR/config.env.example"
curl -sSL "$RAW_URL/skills/daily-snapshot/cron-setup.sh" -o "$SKILL_DIR/cron-setup.sh"
curl -sSL "$RAW_URL/skills/daily-snapshot/requirements.txt" -o "$SKILL_DIR/requirements.txt"

chmod +x "$SKILL_DIR/script.py" "$SKILL_DIR/cron-setup.sh"

# 3. 配置环境变量
if [ ! -f "$SKILL_DIR/config.env" ]; then
    echo "⚙️ 配置环境变量..."
    cp "$SKILL_DIR/config.env.example" "$SKILL_DIR/config.env"
    echo "请编辑 $SKILL_DIR/config.env 填入 API Key"
fi

# 4. 加载环境变量
source "$SKILL_DIR/config.env" 2>/dev/null || true

# 5. 初始化数据库
echo "🗄️ 初始化数据库..."
cd "$SKILL_DIR"
python3 script.py init 2>/dev/null || echo "数据库已存在"

# 6. 设置定时任务
echo "⏰ 设置定时任务（每日4点）..."
bash "$SKILL_DIR/cron-setup.sh"

echo ""
echo "✅ 安装完成！"
echo ""
echo "📝 下一步："
echo "   1. 编辑 $SKILL_DIR/config.env 填入 API Key"
echo "   2. 重启 OpenClaw: cd ~/Desktop/github/openclaw && pnpm gateway:watch"
echo "   3. 测试: /snapshot"