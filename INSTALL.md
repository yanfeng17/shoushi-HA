# MediaPipe Gesture Control - 安装指南

本文档详细说明如何将此项目作为 Home Assistant Addon 安装和使用。

## 安装方式

### 方式一：通过 GitHub 仓库安装（推荐）

#### 1. 准备工作

确保你的 Home Assistant 已经安装并正常运行。

#### 2. 上传到 GitHub

将整个项目上传到你的 GitHub 仓库：

```bash
cd shoushi-HA
git init
git add .
git commit -m "Initial commit: MediaPipe Gesture Control addon"
git branch -M main
git remote add origin https://github.com/yanfeng17/shoushi-HA.git
git push -u origin main
```

#### 3. 在 Home Assistant 中添加仓库

1. 登录 Home Assistant
2. 进入 **设置** → **加载项**
3. 点击右上角 **⋮** (三个点)
4. 选择 **仓库**
5. 添加你的 GitHub 仓库 URL：
   ```
   https://github.com/yanfeng17/shoushi-HA
   ```
6. 点击 **添加**

#### 4. 安装 Addon

1. 刷新页面，在加载项商店中应该能看到 "MediaPipe Gesture Control"
2. 点击 addon 卡片
3. 点击 **安装** 按钮
4. 等待安装完成（首次安装需要下载依赖，可能需要 5-10 分钟）

### 方式二：本地安装（测试用）

如果你想在本地测试，不通过 GitHub：

#### 1. 找到 Home Assistant 的 addons 目录

通常位于：
- Hassio: `/addons/local/`
- Docker: `/usr/share/hassio/addons/local/`
- 如果使用 SSH addon，路径是 `/root/addons/`

#### 2. 创建 addon 目录

```bash
# SSH 登录到 Home Assistant 主机
ssh root@homeassistant.local

# 创建本地 addon 目录
mkdir -p /addons/local/mediapipe_gesture_control

# 或者使用完整路径
mkdir -p /usr/share/hassio/addons/local/mediapipe_gesture_control
```

#### 3. 上传文件

将以下文件复制到创建的目录中：

```
mediapipe_gesture_control/
├── config.yaml
├── Dockerfile
├── build.yaml
├── run.sh
├── requirements.txt
├── config.py
├── main.py
├── DOCS.md
├── CHANGELOG.md
├── README.md
└── src/
    ├── __init__.py
    ├── gesture_engine.py
    └── mqtt_client.py
```

可以使用 SCP、SFTP 或 Samba 共享上传。

#### 4. 重新加载 Addons

1. 在 Home Assistant 中，进入 **设置** → **加载项**
2. 点击右上角 **⋮** → **检查更新**
3. 或者重启 Supervisor

#### 5. 安装本地 Addon

在加载项页面的 "本地加载项" 部分应该能看到 "MediaPipe Gesture Control"，点击安装。

## 配置 Addon

### 1. 基本配置

安装完成后，进入配置页面：

```yaml
rtsp_url: "rtsp://admin:your_password@192.168.1.100:554/stream1"
mqtt_broker: "core-mosquitto"
mqtt_port: 1883
mqtt_username: ""
mqtt_password: ""
frame_width: 640
frame_height: 480
target_fps: 10
gesture_confidence_threshold: 0.8
gesture_stable_duration: 0.5
gesture_cooldown: 2.0
rtsp_reconnect_delay: 5
```

### 2. 获取摄像头 RTSP URL

#### 测试 RTSP 连接

使用 VLC 媒体播放器测试：

1. 打开 VLC
2. **媒体** → **打开网络串流**
3. 输入 RTSP URL
4. 如果能播放，说明 URL 正确

#### 常见摄像头品牌 RTSP 格式

**海康威视 (Hikvision)**
```
rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101
```

**大华 (Dahua)**
```
rtsp://admin:password@192.168.1.100:554/cam/realmonitor?channel=1&subtype=0
```

**TP-Link**
```
rtsp://admin:password@192.168.1.100:554/stream1
```

**小米/米家**
```
rtsp://admin:password@192.168.1.100:8554/live
```

**其他通用格式**
```
rtsp://username:password@ip:554/stream1
rtsp://username:password@ip:554/live
rtsp://username:password@ip:554/h264
```

### 3. 配置 MQTT

#### 使用 Home Assistant 内置 MQTT (推荐)

1. 安装 Mosquitto broker addon
2. 配置中使用：
   ```yaml
   mqtt_broker: "core-mosquitto"
   mqtt_port: 1883
   mqtt_username: ""  # 如果没有设置认证，留空
   mqtt_password: ""
   ```

#### 使用外部 MQTT Broker

```yaml
mqtt_broker: "192.168.1.50"
mqtt_port: 1883
mqtt_username: "mqtt_user"
mqtt_password: "your_mqtt_password"
```

## 启动和测试

### 1. 启动 Addon

1. 保存配置
2. 切换到 **Info** 标签
3. 点击 **START**
4. 观察日志输出

### 2. 查看日志

切换到 **Log** 标签，应该看到类似输出：

```
[INFO] Starting MediaPipe Gesture Control addon...
[INFO] Configuration loaded:
[INFO]   MQTT Broker: core-mosquitto:1883
[INFO]   Frame Size: 640x480
[INFO]   Target FPS: 10
[INFO] Connecting to MQTT broker at core-mosquitto:1883
[INFO] Connected to MQTT broker successfully
[INFO] Home Assistant discovery config sent to homeassistant/sensor/gesture_control/config
[INFO] Connecting to RTSP stream: rtsp://admin:***@192.168.1.100:554/stream1
[INFO] RTSP stream connected successfully
```

### 3. 验证传感器实体

1. 进入 **开发者工具** → **状态**
2. 搜索 `sensor.gesture_control`
3. 应该能看到实体及其当前状态

### 4. 测试手势识别

在摄像头前做手势：

- **张开手掌**：五指伸直
- **握拳**：五指卷曲
- **食指向上**：只有食指伸直
- **OK手势**：拇指和食指接触

观察传感器状态是否变化。

## 故障排除

### Addon 构建失败

**错误**: `Build failed`

**解决方案**:
1. 检查 `config.yaml` 和 `build.yaml` 语法
2. 确保所有文件都已正确上传
3. 查看详细错误日志
4. 可能是网络问题，尝试重新构建

### RTSP 连接失败

**错误**: `Failed to open RTSP stream`

**解决方案**:
1. 使用 VLC 测试 RTSP URL
2. 检查摄像头是否在线
3. 确认用户名密码正确
4. 检查网络连接
5. 某些摄像头需要在设置中启用 RTSP

### MQTT 连接失败

**错误**: `Failed to connect to MQTT broker`

**解决方案**:
1. 确认 Mosquitto addon 正在运行
2. 检查 MQTT broker 地址
3. 如果使用内置 broker，确保使用 `core-mosquitto`
4. 检查 MQTT 认证配置

### 传感器实体未出现

**解决方案**:
1. 等待 2-3 分钟
2. 检查 addon 日志，确认有 "discovery config sent" 消息
3. 重启 Home Assistant 核心
4. 确保 MQTT 集成已启用

### CPU 占用过高

**解决方案**:
1. 降低分辨率：`frame_width: 480`, `frame_height: 360`
2. 降低帧率：`target_fps: 5`
3. 检查是否有其他高负载进程

## 创建自动化

安装成功后，可以创建自动化：

```yaml
# configuration.yaml 或自动化 UI
automation:
  - alias: "手势控制灯光"
    trigger:
      - platform: state
        entity_id: sensor.gesture_control
        to: "OPEN_PALM"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
```

## 更新 Addon

### GitHub 仓库安装

1. 推送新版本到 GitHub
2. 在 Home Assistant 中，进入 **设置** → **加载项**
3. 找到 addon，点击进入
4. 如果有更新，会显示 **更新** 按钮
5. 点击更新并等待完成

### 本地安装

1. 替换文件
2. 在 addon 页面点击 **重建**
3. 重启 addon

## 卸载 Addon

1. 停止 addon
2. 点击 **卸载**
3. 如果不再需要，可以从仓库中删除

## 支持和反馈

- **GitHub Issues**: https://github.com/yanfeng17/shoushi-HA/issues
- **Home Assistant 社区**: https://community.home-assistant.io/

## 下一步

- 阅读 [DOCS.md](DOCS.md) 了解详细配置选项
- 查看 [README.md](README.md) 了解技术细节
- 创建自动化场景使用手势控制
