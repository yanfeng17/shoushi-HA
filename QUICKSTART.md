# 快速入门指南

## 5分钟快速部署

### 步骤 1: 上传到 GitHub

```bash
cd shoushi-HA

# 初始化 Git 仓库
git init
git add .
git commit -m "Initial commit"

# 创建 GitHub 仓库并推送（替换为你的仓库地址）
git remote add origin https://github.com/yanfeng17/shoushi-HA.git
git branch -M main
git push -u origin main
```

### 步骤 2: 添加到 Home Assistant

1. 打开 Home Assistant
2. **设置** → **加载项** → **⋮** → **仓库**
3. 添加仓库 URL: `https://github.com/yanfeng17/shoushi-HA`
4. 找到并安装 "MediaPipe Gesture Control"

### 步骤 3: 配置

```yaml
rtsp_url: "rtsp://admin:your_password@192.168.1.100:554/stream1"
mqtt_broker: "core-mosquitto"
mqtt_port: 1883
```

### 步骤 4: 启动

点击 **START** → 查看 **Log** 确认运行正常

### 步骤 5: 创建自动化

```yaml
automation:
  - alias: "张开手掌开灯"
    trigger:
      platform: state
      entity_id: sensor.gesture_control
      to: "OPEN_PALM"
    action:
      service: light.turn_on
      target:
        entity_id: light.living_room
```

## 测试手势

在摄像头前尝试以下手势：

- ✋ **张开手掌** - 五指伸直
- ✊ **握拳** - 五指卷曲  
- ☝️ **食指向上** - 只有食指伸直
- 👌 **OK手势** - 拇指和食指接触

观察 `sensor.gesture_control` 状态变化。

## 常见问题

**Q: Addon 无法启动？**
- 检查 RTSP URL 格式是否正确
- 使用 VLC 测试摄像头连接

**Q: 没有创建传感器实体？**
- 等待 2-3 分钟
- 确保 MQTT 集成已启用
- 重启 Home Assistant

**Q: 手势识别不准确？**
- 改善光照条件
- 调整 `gesture_confidence_threshold` (默认 0.8)
- 增加 `gesture_stable_duration` (默认 0.5秒)

## 详细文档

- [INSTALL.md](INSTALL.md) - 完整安装指南
- [DOCS.md](DOCS.md) - 配置和使用文档
- [README.md](README.md) - 技术文档

## 需要帮助？

- GitHub Issues: https://github.com/yanfeng17/shoushi-HA/issues
- Home Assistant 社区: https://community.home-assistant.io/
