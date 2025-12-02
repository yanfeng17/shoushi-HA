# MediaPipe Gesture Control - GitHub 部署脚本
# 此脚本将项目上传到 GitHub

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MediaPipe Gesture Control" -ForegroundColor Cyan
Write-Host "GitHub 部署脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否已初始化 Git
if (-not (Test-Path ".git")) {
    Write-Host "初始化 Git 仓库..." -ForegroundColor Yellow
    git init
    Write-Host "✓ Git 仓库已初始化" -ForegroundColor Green
} else {
    Write-Host "✓ Git 仓库已存在" -ForegroundColor Green
}

# 检查 gh CLI 登录状态
Write-Host ""
Write-Host "检查 GitHub CLI 登录状态..." -ForegroundColor Yellow
$ghStatus = gh auth status 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 已登录到 GitHub" -ForegroundColor Green
} else {
    Write-Host "✗ 未登录 GitHub CLI" -ForegroundColor Red
    Write-Host "请运行: gh auth login" -ForegroundColor Yellow
    exit 1
}

# 添加所有文件
Write-Host ""
Write-Host "添加文件到 Git..." -ForegroundColor Yellow
git add .
Write-Host "✓ 文件已添加" -ForegroundColor Green

# 提交
Write-Host ""
Write-Host "创建 Git 提交..." -ForegroundColor Yellow
git commit -m "Initial commit: MediaPipe Gesture Control Home Assistant Addon

- Real-time hand gesture recognition using MediaPipe
- MQTT Auto Discovery integration
- Multi-architecture support (amd64, aarch64, armv7, armhf, i386)
- Complete documentation in Chinese and English
- Supports 5 gestures: Open Palm, Closed Fist, Pointing Up, OK Sign, None
- State machine with debouncing and cooldown mechanisms
- Automatic RTSP reconnection
- Performance optimized for low-resource devices"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 提交成功" -ForegroundColor Green
} else {
    Write-Host "✗ 提交失败" -ForegroundColor Red
    Write-Host "请检查错误信息并手动执行" -ForegroundColor Yellow
    exit 1
}

# 创建 GitHub 仓库
Write-Host ""
Write-Host "创建 GitHub 仓库..." -ForegroundColor Yellow
$repoExists = gh repo view yanfeng17/shoushi-HA 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 仓库已存在" -ForegroundColor Yellow
} else {
    Write-Host "创建新仓库 shoushi-HA..." -ForegroundColor Yellow
    gh repo create shoushi-HA --public --source=. --description="Home Assistant Addon for real-time hand gesture recognition using MediaPipe"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 仓库创建成功" -ForegroundColor Green
    } else {
        Write-Host "✗ 仓库创建失败" -ForegroundColor Red
        Write-Host "您可能需要手动创建仓库" -ForegroundColor Yellow
        exit 1
    }
}

# 设置远程仓库（如果尚未设置）
Write-Host ""
Write-Host "配置远程仓库..." -ForegroundColor Yellow
$remoteExists = git remote get-url origin 2>&1
if ($LASTEXITCODE -ne 0) {
    git remote add origin https://github.com/yanfeng17/shoushi-HA.git
    Write-Host "✓ 远程仓库已添加" -ForegroundColor Green
} else {
    Write-Host "✓ 远程仓库已存在: $remoteExists" -ForegroundColor Green
}

# 推送到 GitHub
Write-Host ""
Write-Host "推送代码到 GitHub..." -ForegroundColor Yellow
git branch -M main
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ 部署成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "仓库地址: https://github.com/yanfeng17/shoushi-HA" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "下一步操作：" -ForegroundColor Yellow
    Write-Host "1. 在 Home Assistant 中添加此仓库" -ForegroundColor White
    Write-Host "   设置 → 加载项 → ⋮ → 仓库" -ForegroundColor White
    Write-Host "   添加: https://github.com/yanfeng17/shoushi-HA" -ForegroundColor White
    Write-Host ""
    Write-Host "2. 安装 MediaPipe Gesture Control addon" -ForegroundColor White
    Write-Host ""
    Write-Host "3. 配置 RTSP 摄像头和 MQTT 设置" -ForegroundColor White
    Write-Host ""
    Write-Host "详细说明请查看:" -ForegroundColor Yellow
    Write-Host "- QUICKSTART.md (快速入门)" -ForegroundColor White
    Write-Host "- INSTALL.md (详细安装指南)" -ForegroundColor White
    Write-Host "- DOCS.md (使用文档)" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "✗ 推送失败" -ForegroundColor Red
    Write-Host "请检查网络连接和 GitHub 权限" -ForegroundColor Yellow
    exit 1
}
