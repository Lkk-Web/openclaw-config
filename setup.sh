#!/bin/bash
# OpenClaw 快速部署脚本

set -e

echo "🚀 OpenClaw 配置部署"
echo ""

# 1. 检查是否已安装 OpenClaw
if ! command -v openclaw &> /dev/null; then
    echo "❌ 请先安装 OpenClaw"
    exit 1
fi

# 2. 克隆配置（如果还没有）
if [ ! -d ~/.openclaw/.git ]; then
    echo "📥 克隆配置仓库..."
    git clone https://github.com/Lkk-Web/openclaw-config.git ~/.openclaw-temp
    mv ~/.openclaw-temp/* ~/.openclaw-temp/.* ~/.openclaw/ 2>/dev/null || true
    rm -rf ~/.openclaw-temp
fi

# 3. 配置敏感信息
echo ""
echo "⚙️  配置敏感信息"
echo ""

if [ ! -f ~/.openclaw/.env ]; then
    echo "请输入 TAVILY_API_KEY:"
    read -r TAVILY_KEY
    echo "TAVILY_API_KEY=$TAVILY_KEY" > ~/.openclaw/.env
    echo "✅ .env 已创建"
fi

# 4. 配置 openclaw.json
if [ ! -f ~/.openclaw/openclaw.json ]; then
    echo ""
    echo "请输入你的用户名（用于路径配置）:"
    read -r USERNAME
    
    cp ~/.openclaw/openclaw.json.example ~/.openclaw/openclaw.json
    sed -i.bak "s/YOUR_USERNAME/$USERNAME/g" ~/.openclaw/openclaw.json
    rm ~/.openclaw/openclaw.json.bak
    
    echo "✅ openclaw.json 已创建"
    echo "⚠️  请编辑 ~/.openclaw/openclaw.json 配置 API keys"
fi

# 5. 重启 Gateway
echo ""
echo "🔄 重启 OpenClaw Gateway..."
openclaw gateway restart

echo ""
echo "✅ 部署完成！"
echo ""
echo "下一步："
echo "1. 编辑 ~/.openclaw/openclaw.json 配置 API keys"
echo "2. 运行: openclaw gateway restart"
