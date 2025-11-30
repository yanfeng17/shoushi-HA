# MediaPipe Gesture Control Addon

实时手势识别 Home Assistant 插件，使用 MediaPipe 进行手势检测并通过 MQTT 集成到 Home Assistant。

## 功能特性

- **实时手势识别**：使用 Google MediaPipe 技术检测手部动作
- **支持多种手势**：张开手掌、握拳、食指向上、OK手势
- **自动集成**：通过 MQTT Auto Discovery 自动创建传感器实体
- **断线重连**：RTSP 视频流自动重连机制
- **防抖动**：智能状态机避免误触发
- **性能优化**：低 CPU 占用，适合运行在树莓派等设备

## 支持的手势

| 手势 | 描述 | 状态值 |
|------|------|--------|
| 张开手掌 | 五根手指全部伸直 | `OPEN_PALM` |
| 握拳 | 五根手指全部卷曲 | `CLOSED_FIST` |
| 食指向上 | 仅食指伸直 | `POINTING_UP` |
| OK手势 | 拇指和食指接触，其余手指伸直 | `OK_SIGN` |
| 无手势 | 未检测到手或手势不明确 | `NONE` |

## 配置说明

### RTSP 摄像头设置

```
rtsp_url: rtsp://username:password@camera_ip:554/stream1
```

**说明**：
- 替换 `username` 和 `password` 为摄像头的登录凭据
- 替换 `camera_ip` 为摄像头的 IP 地址
- 端口号和路径根据摄像头型号可能不同

**常见摄像头 RTSP 路径**：
- 海康威视: `/Streaming/Channels/101`
- 大华: `/cam/realmonitor?channel=1&subtype=0`
- TP-Link: `/stream1`
- 通用: `/stream1` 或 `/live`

### MQTT 设置

```yaml
mqtt_broker: core-mosquitto
mqtt_port: 1883
mqtt_username: ""  # 可选
mqtt_password: ""  # 可选
```

**说明**：
- 如果使用 Home Assistant 内置的 Mosquitto addon，`mqtt_broker` 设置为 `core-mosquitto`
- 如果使用外部 MQTT broker，填写 IP 地址
- 如果 MQTT 需要认证，填写用户名和密码

### 视频处理参数

```yaml
frame_width: 640          # 处理帧宽度 (320-1920)
frame_height: 480         # 处理帧高度 (240-1080)
target_fps: 10            # 目标处理帧率 (5-30)
```

**调优建议**：
- **性能优先**：`640x480 @ 10fps` - CPU占用低，响应快
- **质量优先**：`1280x720 @ 15fps` - 识别更准确，远距离效果好
- **树莓派**：`480x360 @ 8fps` - 适合低性能设备

### 手势识别参数

```yaml
gesture_confidence_threshold: 0.8    # 置信度阈值 (0.5-1.0)
gesture_stable_duration: 0.5         # 稳定持续时间（秒）(0.1-5.0)
gesture_cooldown: 2.0                # 冷却时间（秒）(0.5-10.0)
```

**参数说明**：

- **gesture_confidence_threshold**（置信度阈值）
  - 值越高，误触发越少，但可能漏检
  - 值越低，更敏感，但可能误触发
  - 推荐：`0.8`（平衡）、`0.7`（更敏感）、`0.9`（更严格）

- **gesture_stable_duration**（稳定持续时间）
  - 手势必须保持多少秒才被识别
  - 值越大，防抖效果越好，但响应变慢
  - 推荐：`0.5`（平衡）、`0.3`（快速响应）、`1.0`（防误触）

- **gesture_cooldown**（冷却时间）
  - 同一手势触发后多久才能再次触发
  - 防止重复发送指令
  - 推荐：`2.0`（防止重复）、`1.0`（频繁操作）

### 连接参数

```yaml
rtsp_reconnect_delay: 5    # RTSP 重连延迟（秒）(1-60)
```

## 使用方法

### 1. 安装 Addon

1. 在 Home Assistant 中，进入 **设置** → **加载项**
2. 点击右上角的三个点，选择 **仓库**
3. 添加仓库 URL（如果使用本地安装，跳过此步）
4. 在加载项商店中找到 "MediaPipe Gesture Control"
5. 点击安装

### 2. 配置 Addon

安装完成后，进入配置页面：

```yaml
rtsp_url: "rtsp://admin:your_password@192.168.1.100:554/stream1"
mqtt_broker: "core-mosquitto"
mqtt_port: 1883
```

根据你的摄像头和网络环境调整配置。

### 3. 启动 Addon

1. 保存配置
2. 切换到 "Info" 标签
3. 点击 "START" 启动 addon
4. 建议启用 "Start on boot"（开机自启）
5. 启用 "Watchdog"（自动重启）

### 4. 查看日志

切换到 "Log" 标签查看运行状态：

```
[INFO] Starting MediaPipe Gesture Control addon...
[INFO] Configuration loaded:
[INFO]   MQTT Broker: core-mosquitto:1883
[INFO]   Frame Size: 640x480
[INFO]   Target FPS: 10
[INFO] Connected to MQTT broker successfully
[INFO] RTSP stream connected successfully
```

### 5. 在 Home Assistant 中使用

启动成功后，会自动创建一个传感器实体：

- **实体 ID**: `sensor.gesture_control`
- **名称**: Gesture Control
- **状态**: 显示当前识别的手势

#### 查看实体状态

进入 **开发者工具** → **状态**，搜索 `sensor.gesture_control`，可以看到：

```yaml
state: OPEN_PALM
attributes:
  gesture: OPEN_PALM
  confidence: 0.95
  timestamp: 1234567890
  friendly_name: Gesture Control
```

## 自动化示例

### 示例 1：用手势控制灯光

```yaml
automation:
  - alias: "张开手掌开灯"
    trigger:
      - platform: state
        entity_id: sensor.gesture_control
        to: "OPEN_PALM"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          brightness: 255

  - alias: "握拳关灯"
    trigger:
      - platform: state
        entity_id: sensor.gesture_control
        to: "CLOSED_FIST"
    action:
      - service: light.turn_off
        target:
          entity_id: light.living_room
```

### 示例 2：食指向上播放音乐

```yaml
automation:
  - alias: "食指向上播放音乐"
    trigger:
      - platform: state
        entity_id: sensor.gesture_control
        to: "POINTING_UP"
    action:
      - service: media_player.media_play
        target:
          entity_id: media_player.living_room_speaker
```

### 示例 3：OK手势切换场景

```yaml
automation:
  - alias: "OK手势切换场景"
    trigger:
      - platform: state
        entity_id: sensor.gesture_control
        to: "OK_SIGN"
    action:
      - service: scene.turn_on
        target:
          entity_id: scene.movie_mode
```

### 示例 4：带条件的手势控制

```yaml
automation:
  - alias: "夜间手势控制"
    trigger:
      - platform: state
        entity_id: sensor.gesture_control
        to: "OPEN_PALM"
    condition:
      - condition: time
        after: "22:00:00"
        before: "06:00:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.bedroom
        data:
          brightness: 50  # 夜间低亮度
```

## 故障排除

### Addon 无法启动

1. **检查日志**：查看是否有错误信息
2. **验证配置**：确保 RTSP URL 格式正确
3. **测试摄像头**：使用 VLC 播放器测试 RTSP 流是否可访问

### 无法连接到 RTSP 摄像头

- 确认摄像头 IP 地址正确
- 检查用户名和密码
- 确保 Home Assistant 与摄像头在同一网络
- 尝试降低摄像头的分辨率和帧率设置
- 某些摄像头可能需要在设置中启用 RTSP

### MQTT 连接失败

- 确认 Mosquitto addon 已安装并运行
- 检查 MQTT broker 地址（使用内置 broker 时应为 `core-mosquitto`）
- 验证 MQTT 用户名密码（如果设置了认证）

### 手势识别不准确

**误触发太多**：
- 增加 `gesture_confidence_threshold` (例如 0.9)
- 增加 `gesture_stable_duration` (例如 1.0)
- 增加 `gesture_cooldown` (例如 3.0)

**识别不到手势**：
- 降低 `gesture_confidence_threshold` (例如 0.7)
- 减少 `gesture_stable_duration` (例如 0.3)
- 改善光照条件
- 调整摄像头角度和距离
- 增加视频分辨率

### CPU 占用过高

- 降低 `frame_width` 和 `frame_height` (例如 480x360)
- 降低 `target_fps` (例如 5-8)
- 确保没有其他高负载程序运行

### 传感器实体未出现

- 等待 1-2 分钟，MQTT Discovery 需要时间
- 重启 Home Assistant 核心
- 检查 MQTT 集成是否已启用
- 查看 addon 日志确认 "discovery config sent" 消息

## 性能指标

### 推荐配置

| 设备 | 分辨率 | FPS | CPU 占用 | 延迟 |
|------|--------|-----|----------|------|
| 树莓派 3B+ | 480x360 | 8 | ~60% | 300-500ms |
| 树莓派 4 | 640x480 | 10 | ~40% | 200-300ms |
| NUC/x86 | 1280x720 | 15 | ~30% | 100-200ms |

### 内存占用

- 基础内存：~300 MB
- 运行时：~400-600 MB
- 峰值：~800 MB

## 高级设置

### 使用外部 MQTT Broker

如果不使用 Home Assistant 内置的 Mosquitto：

```yaml
mqtt_broker: "192.168.1.50"  # 外部 broker IP
mqtt_port: 1883
mqtt_username: "mqtt_user"
mqtt_password: "mqtt_pass"
```

### 多摄像头部署

目前每个 addon 实例只支持一个摄像头。如果需要多个摄像头：

1. 创建多个 addon 副本（需要手动修改代码）
2. 修改 `config.py` 中的 `MQTT_DEVICE_NAME` 为不同的名称
3. 每个实例使用不同的 RTSP URL

## 安全建议

1. **不要在配置中使用明文密码**：考虑使用 Secrets
2. **限制摄像头访问权限**：确保 RTSP 流不暴露在公网
3. **使用 MQTT 认证**：为 MQTT broker 设置用户名密码
4. **定期更新**：保持 addon 和依赖库更新

## 技术支持

- **GitHub Issues**: [报告问题](https://github.com/yanfeng17/shoushi-HA/issues)
- **Home Assistant 社区**: [讨论帖](https://community.home-assistant.io/)
- **文档**: [完整文档](https://github.com/yanfeng17/shoushi-HA)

## 更新日志

### v1.0.0 (2025-11-30)
- 初始版本发布
- 支持 5 种手势识别
- MQTT Auto Discovery 集成
- RTSP 自动重连机制
- 状态机防抖动逻辑
