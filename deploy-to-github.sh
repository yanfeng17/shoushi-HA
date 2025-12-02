#!/bin/bash
# MediaPipe Gesture Control - GitHub 部署脚本
# 此脚本将项目上传到 GitHub

set -e

echo "========================================"
echo "MediaPipe Gesture Control"
echo "GitHub 部署脚本"
echo "========================================"
echo ""

# 检查是否已初始化 Git
if [ ! -d ".git" ]; then
    echo "初始化 Git 仓库..."
    git init
    echo "✓ Git 仓库已初始化"
else
    echo "✓ Git 仓库已存在"
fi

# 检查 gh CLI 登录状态
echo ""
echo "检查 GitHub CLI 登录状态..."
if gh auth status > /dev/null 2>&1; then
    echo "✓ 已登录到 GitHub"
else
    echo "✗ 未登录 GitHub CLI"
    echo "请运行: gh auth login"
    exit 1
fi

# 添加所有文件
echo ""
echo "添加文件到 Git..."
git add .
echo "✓ 文件已添加"

# 提交
echo ""
echo "创建 Git 提交..."
git commit -m "Initial commit: MediaPipe Gesture Control Home Assistant Addon

- Real-time hand gesture recognition using MediaPipe
- MQTT Auto Discovery integration
- Multi-architecture support (amd64, aarch64, armv7, armhf, i386)
- Complete documentation in Chinese and English
- Supports 5 gestures: Open Palm, Closed Fist, Pointing Up, OK Sign, None
- State machine with debouncing and cooldown mechanisms
- Automatic RTSP reconnection
- Performance optimized for low-resource devices"

echo "✓ 提交成功"

# 创建 GitHub 仓库
echo ""
echo "创建 GitHub 仓库..."
if gh repo view yanfeng17/shoushi-HA > /dev/null 2>&1; then
    echo "✓ 仓库已存在"
else
    echo "创建新仓库 shoushi-HA..."
    gh repo create shoushi-HA --public --source=. --description="Home Assistant Addon for real-time hand gesture recognition using MediaPipe"
    echo "✓ 仓库创建成功"
fi

# 设置远程仓库（如果尚未设置）
echo ""
echo "配置远程仓库..."
if git remote get-url origin > /dev/null 2>&1; then
    REMOTE_URL=$(git remote get-url origin)
    echo "✓ 远程仓库已存在: $REMOTE_URL"
else
    git remote add origin https://github.com/yanfeng17/shoushi-HA.git
    echo "✓ 远程仓库已添加"
fi

# 推送到 GitHub
echo ""
echo "推送代码到 GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "========================================"
echo "✓ 部署成功！"
echo "========================================"
echo ""
echo "仓库地址: https://github.com/yanfeng17/shoushi-HA"
echo ""
echo "下一步操作："
echo "1. 在 Home Assistant 中添加此仓库"
echo "   设置 → 加载项 → ⋮ → 仓库"
echo "   添加: https://github.com/yanfeng17/shoushi-HA"
echo ""
echo "2. 安装 MediaPipe Gesture Control addon"
echo ""
echo "3. 配置 RTSP 摄像头和 MQTT 设置"
echo ""
echo "详细说明请查看:"
echo "- QUICKSTART.md (快速入门)"
echo "- INSTALL.md (详细安装指南)"
echo "- DOCS.md (使用文档)"
