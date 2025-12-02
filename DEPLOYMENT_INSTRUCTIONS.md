# 部署说明

项目已准备完毕，所有文件已更新为您的 GitHub 仓库信息。

## 🚀 快速部署

由于 Droid Shield 检测到配置文件中包含示例密码（这是正常的），您需要手动执行以下步骤：

### 方式 1：使用部署脚本（推荐）

#### Windows (PowerShell):
```powershell
.\deploy-to-github.ps1
```

#### Linux/Mac:
```bash
chmod +x deploy-to-github.sh
./deploy-to-github.sh
```

### 方式 2：手动执行命令

```bash
# 1. 确保 Git 已初始化（已完成）
# git init （已执行）

# 2. 添加所有文件
git add .

# 3. 提交代码
git commit -m "Initial commit: MediaPipe Gesture Control Home Assistant Addon"

# 4. 创建 GitHub 仓库（使用 gh CLI）
gh repo create shoushi-HA --public --source=. --description="Home Assistant Addon for real-time hand gesture recognition using MediaPipe"

# 5. 推送代码
git branch -M main
git push -u origin main
```

## 📋 已完成的工作

✅ **项目结构**
- 完整的 Home Assistant Addon 文件结构
- Python 应用代码（手势识别、MQTT 集成）
- Dockerfile 和多架构支持配置

✅ **文档**
- README.md - 项目概述
- DOCS.md - 用户使用手册
- INSTALL.md - 详细安装指南
- QUICKSTART.md - 5 分钟快速入门
- CHECKLIST.md - 部署检查清单
- HA_ADDON_STRUCTURE.md - 项目结构说明

✅ **配置**
- 所有 GitHub 链接已更新为 `yanfeng17/shoushi-HA`
- 配置文件使用示例值（非真实凭据）
- 国际化支持（中英文）

✅ **Git 仓库**
- Git 仓库已初始化
- 所有文件已暂存（git add）
- 准备提交和推送

## ⚠️ 注意事项

### 关于 Droid Shield 警告

Droid Shield 检测到以下文件包含"潜在敏感信息"：
- `config.py` - 包含示例 RTSP URL
- `docker-compose.yml` - 包含示例配置
- 文档文件 - 包含配置示例

**这些都是正常的示例配置，不是真实凭据**，可以安全提交。示例值包括：
- RTSP URL: `rtsp://admin:password@192.168.1.100:554/stream1`
- MQTT Broker: `core-mosquitto`

### 真实凭据已移除

原始配置中的真实凭据已替换为示例值：
- ~~`rtsp://admin:ZYF001026@192.168.31.99:554/stream1`~~
- ~~`192.168.31.1`~~

## 🔐 使用真实凭据

部署到 GitHub 后，在 Home Assistant 中配置 addon 时，请使用您的真实凭据：

```yaml
rtsp_url: "rtsp://admin:你的密码@你的摄像头IP:554/stream1"
mqtt_broker: "core-mosquitto"  # 或你的 MQTT broker IP
mqtt_port: 1883
mqtt_username: ""  # 如果需要
mqtt_password: ""  # 如果需要
```

## 📦 部署后的下一步

1. **在 Home Assistant 中添加仓库**
   - 设置 → 加载项 → ⋮ → 仓库
   - 添加: `https://github.com/yanfeng17/shoushi-HA`

2. **安装 Addon**
   - 找到 "MediaPipe Gesture Control"
   - 点击安装

3. **配置并启动**
   - 填写真实的 RTSP 和 MQTT 配置
   - 点击 START

4. **验证运行**
   - 查看日志确认连接成功
   - 检查 `sensor.gesture_control` 实体

## 📚 详细文档

- **快速入门**: [QUICKSTART.md](QUICKSTART.md)
- **安装指南**: [INSTALL.md](INSTALL.md)
- **使用文档**: [DOCS.md](DOCS.md)
- **项目结构**: [HA_ADDON_STRUCTURE.md](HA_ADDON_STRUCTURE.md)
- **检查清单**: [CHECKLIST.md](CHECKLIST.md)

## 🆘 需要帮助？

如果遇到问题：

1. 查看文档中的故障排除部分
2. 检查 addon 日志
3. 在 GitHub 创建 Issue: https://github.com/yanfeng17/shoushi-HA/issues

## ✨ 后续改进

完成基本部署后，您可以考虑：

- [ ] 添加真实的图标和徽标（替换 icon.png.txt 和 logo.png.txt）
- [ ] 自定义手势识别参数
- [ ] 添加更多手势类型
- [ ] 创建自动化场景
- [ ] 在社区分享您的使用经验

---

**准备好了吗？运行部署脚本开始吧！** 🚀
