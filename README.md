# MediaPipe 手势与表情识别 Home Assistant 插件

🤚 😊 一个基于 MediaPipe 的 Home Assistant 插件，支持实时手势识别和面部表情识别，通过 MQTT 自动发现无缝集成到 Home Assistant。

> **注意**：这是一个 Home Assistant 插件。安装说明请参见 [INSTALL.md](INSTALL.md)。

## ✨ 核心功能

### 手势识别
- **实时手势识别**：使用 MediaPipe Hands 检测和分类 4 种手势
- **高精度识别**：基于 21 个手部关键点的几何分析
- **防抖动机制**：防止误触发，支持稳定性检查和冷却时间

### 表情识别 🆕
- **实时面部表情识别**：使用 MediaPipe Face Landmarker 检测表情
- **支持 10+ 种表情**：微笑、张嘴、惊讶、打哈欠等
- **52 个 Blendshapes 系数**：导出详细的面部表情数据
- **478 个面部关键点**：高精度面部追踪

### 调试与可视化 🆕
- **实时调试显示**：在视频画面上显示检测信息
- **FPS 监控**：实时显示处理帧率
- **Blendshapes 可视化**：显示关键表情参数和进度条
- **手势和表情同时显示**：直观查看识别结果

### 系统集成
- **MQTT 自动发现**：无需手动配置即可在 Home Assistant 中创建传感器
- **详细数据发布**：可选发布完整的 Blendshapes 数据用于高级自动化
- **稳定的视频流**：自动 RTSP 重连，支持网络中断恢复
- **Docker 支持**：简单部署，跨平台运行
- **高度可配置**：所有参数可通过配置文件调整

## 🖐️ 可识别的手势

| 手势 | 描述 | 用途示例 |
|------|------|---------|
| 🖐️ **张开手掌** | 五指全部伸直 | 开灯、播放 |
| ✊ **握拳** | 五指全部卷曲 | 关灯、暂停 |
| ☝️ **食指向上** | 只有食指伸直 | 音量增加 |
| 👌 **OK 手势** | 拇指和食指圈起来 | 确认操作 |

## 😊 可识别的表情（v1.0.7 新增）

| 表情 | 代码 | 触发条件 |
|------|------|---------|
| 😮 **张嘴** | `MOUTH_OPEN` | 嘴巴张开 > 30% |
| 😲 **大张嘴** | `MOUTH_WIDE_OPEN` | 下巴张开 > 50% |
| 😄 **微笑** | `SMILE` | 嘴角上扬 > 40% |
| 😊 **真笑** | `GENUINE_SMILE` | 微笑 + 眼睛眯起（杜兴微笑）|
| 😔 **皱眉** | `FROWN` | 嘴角下垂 > 30% |
| 🥱 **打哈欠** | `YAWNING` | 大张嘴 + 嘴巴呈漏斗状 |
| 😑 **嘟嘴** | `PUCKER` | 嘴唇撅起 > 40% |
| 😉 **眨眼** | `WINK_LEFT/RIGHT` | 单眼闭合 > 70% |
| 😌 **闭眼** | `BLINK_BOTH` | 双眼闭合 > 70% |
| 😲 **惊讶** | `SURPRISED` | 大张嘴 + 睁大眼 + 扬眉 |
| 😐 **中性** | `NEUTRAL` | 无明显表情 |

## 📋 系统要求

- **Docker** 和 Docker Compose（或 Home Assistant Supervisor）
- **RTSP 摄像头**（支持 H.264/H.265）
- **Home Assistant** 与 Mosquitto MQTT broker
- **网络连接**：各组件之间的网络访问
- **硬件建议**：
  - CPU：双核及以上（推荐四核）
  - 内存：至少 2GB（推荐 4GB）
  - 支持的架构：amd64, aarch64, armv7, armhf, i386

## 🚀 快速开始

### 方法 1：作为 Home Assistant 插件安装（推荐）

1. **添加插件仓库**
   ```
   设置 → 加载项 → 插件商店 → ⋮ → 仓库
   添加：https://github.com/你的用户名/shoushi-HA
   ```

2. **安装插件**
   - 在插件商店中找到 "MediaPipe Gesture Control"
   - 点击安装
   - 等待 8-10 分钟（首次安装需要下载模型）

3. **配置插件**
   ```yaml
   rtsp_url: "rtsp://USERNAME:PASS@192.168.1.100:554/stream1"
   mqtt_broker: "core-mosquitto"
   mqtt_port: 1883
   enable_expression_detection: true
   debug_visualization: true
   ```

4. **启动插件**
   - 点击 "启动"
   - 查看日志确认正常运行

### 方法 2：使用 Docker Compose

1. **克隆仓库并配置**
   ```bash
   git clone https://github.com/你的用户名/shoushi-HA.git
   cd shoushi-HA
   cp .env.example .env
   nano .env
   ```

2. **构建并运行**
   ```bash
   docker-compose build
   docker-compose up -d
   docker-compose logs -f
   ```

### 在 Home Assistant 中验证

启动后，应该会自动创建传感器实体：

- **实体 ID**：`sensor.gesture_control`
- **实体名称**："Gesture Control"
- **可能的状态**：
  - 手势：OPEN_PALM, CLOSED_FIST, POINTING_UP, OK_SIGN
  - 表情：SMILE, MOUTH_OPEN, SURPRISED, YAWNING 等
- **属性**：
  - `confidence`：识别置信度（0-1）
  - `type`：类型（"gesture" 或 "expression"）
  - `blendshapes`：52 个面部表情系数（如果启用）

## ⚙️ 配置参数

### 视频处理

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `frame_width` | 320 | 处理帧宽度（像素）|
| `frame_height` | 240 | 处理帧高度（像素）|
| `target_fps` | 15 | 目标处理帧率 |
| `skip_frames` | 1 | 跳帧处理（1=全部，2=一半）|

### 手势识别

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `gesture_confidence_threshold` | 0.65 | 手势置信度阈值 |
| `gesture_stable_duration` | 0.3 | 手势稳定持续时间（秒）|
| `gesture_cooldown` | 1.5 | 手势触发冷却时间（秒）|

### 表情识别（v1.0.7 新增）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `enable_expression_detection` | true | 启用表情识别 |
| `expression_confidence_threshold` | 0.3 | 表情置信度阈值 |
| `mouth_open_threshold` | 0.3 | 张嘴阈值 |
| `jaw_open_threshold` | 0.5 | 大张嘴阈值 |
| `smile_threshold` | 0.4 | 微笑阈值 |
| `frown_threshold` | 0.3 | 皱眉阈值 |
| `blink_threshold` | 0.7 | 眨眼阈值 |
| `pucker_threshold` | 0.4 | 嘟嘴阈值 |

### 调试与可视化（v1.0.7 新增）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `debug_visualization` | true | 在画面显示调试信息 |
| `publish_detailed_blendshapes` | true | 发布详细 blendshapes 数据 |
| `blendshapes_min_threshold` | 0.05 | Blendshapes 最小发布值 |

### 连接设置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `rtsp_reconnect_delay` | 5 | RTSP 重连延迟（秒）|
| `log_level` | INFO | 日志级别（DEBUG/INFO/WARNING/ERROR）|

## 🏗️ 系统架构

```
main.py                              # 主应用程序循环
├── VideoStreamProcessor             # RTSP 流处理与自动重连
├── GestureEngine                    # MediaPipe Hands 封装
│   └── 手势识别                     # 基于几何关键点分析
├── ExpressionEngine (v1.0.7)       # MediaPipe Face Landmarker 封装
│   ├── 表情识别                     # 基于 52 个 Blendshapes
│   └── 478 个面部关键点             # 高精度面部追踪
├── DebugVisualizer (v1.0.7)        # 调试可视化
│   ├── FPS 显示                     # 实时帧率监控
│   ├── 手势/表情显示                # 识别结果可视化
│   └── Blendshapes 进度条           # 表情参数可视化
├── GestureBuffer                    # 状态机与防抖逻辑
└── MQTTClient                       # MQTT 连接与 HA 自动发现
    ├── 状态发布                     # 手势/表情状态
    └── Blendshapes 数据             # 详细表情系数
```

## 🔧 工作原理

### 1. 视频流处理

- 连接 RTSP 流，支持自动重连
- 调整帧大小以优化性能（320×240）
- 实现帧率限制以降低 CPU 使用（10-15 FPS）
- 可选的跳帧处理以进一步提升性能

### 2. 手势识别

MediaPipe 检测 **21 个手部关键点**，通过几何分析识别手势：

- **手指伸展检测**：比较指尖与 PIP/MCP 关节的位置
- **拇指状态**：计算与手掌中心的距离
- **几何关系**：特定关键点间的距离（如拇指-食指距离判断 OK 手势）

### 3. 表情识别（v1.0.7）

MediaPipe Face Landmarker 检测 **478 个面部关键点**和 **52 个 Blendshapes**：

- **Blendshapes**：52 个表情系数（0-1 范围）
  - `mouthOpen`：嘴巴张开程度
  - `mouthSmile`：微笑程度
  - `jawOpen`：下巴张开程度
  - `eyeBlinkLeft/Right`：眨眼程度
  - 等等...

- **表情分类**：基于 Blendshapes 组合判断表情
  - 微笑 = `mouthSmile > 0.4`
  - 真笑 = `mouthSmile > 0.4 && eyeSquint > 0.3`
  - 惊讶 = `jawOpen > 0.5 && eyeWide > 0.5 && browUp > 0.4`

### 4. 状态机与防抖

```
检测 → 缓冲 → 稳定性检查 → 冷却检查 → 触发 → MQTT 发布
```

- 手势/表情必须连续检测到 **2 次**才触发
- 触发后，相同状态在 `cooldown` 时间内不会重复触发
- 不同状态可以立即触发

### 5. MQTT 与 Home Assistant

**启动时**：
- 发送 MQTT 自动发现配置到 Home Assistant
- 自动创建传感器实体

**状态发布**（基础）：
```json
{
  "state": "SMILE",
  "confidence": 0.78,
  "type": "expression",
  "timestamp": 1701234567.89
}
```

**状态发布**（包含 Blendshapes）：
```json
{
  "state": "SMILE",
  "confidence": 0.78,
  "type": "expression",
  "timestamp": 1701234567.89,
  "blendshapes": {
    "mouthSmile": 0.78,
    "eyeSquintLeft": 0.42,
    "eyeSquintRight": 0.39,
    "jawOpen": 0.15,
    "mouthOpen": 0.08
  }
}
```

## 🔍 故障排查

### 插件无法启动

**检查日志**：
```bash
# Docker Compose
docker-compose logs -f

# Home Assistant 插件
设置 → 加载项 → MediaPipe Gesture Control → 日志
```

**常见启动错误**：
- ✅ 应该看到：`Expression Engine initialized successfully`
- ✅ 应该看到：`Connected to MQTT broker successfully`
- ❌ 如果看到 `Model file not found`：重建插件
- ❌ 如果看到 `MQTT connection failed`：检查 MQTT 配置

### RTSP 连接失败

- 验证 RTSP URL 格式：`rtsp://USERNAME:PASS@IP:PORT/PATH`
- 检查网络连通性：`ping 摄像头IP`
- 确认摄像头支持 RTSP
- 尝试在 VLC 中打开 RTSP URL 测试

### MQTT 无法连接

- 验证 MQTT broker IP 和端口
- 检查 MQTT 认证信息（用户名和凭据）
- 确认 Home Assistant 的 Mosquitto 插件正在运行
- 查看 Mosquitto 日志：`设置 → 加载项 → Mosquitto broker → 日志`

### 手势识别不准确

**光线问题**：
- 确保良好的照明条件
- 避免背光（逆光）
- 均匀的照明最佳

**距离问题**：
- 建议距离：0.5-2 米
- 手部应在画面中心
- 手部应占画面 20-40%

**配置调整**：
- 降低阈值：`gesture_confidence_threshold: 0.5`（更敏感）
- 减少稳定时间：`gesture_stable_duration: 0.2`（更快响应）

### 表情识别不工作

**面部角度**：
- 需要正面或半侧面（< 45°）
- 面部应清晰可见
- 避免遮挡（口罩、眼镜反光等）

**光线要求**：
- 表情识别对光线更敏感
- 需要面部正面光照
- 避免强阴影

**配置调整**：
- 降低阈值：`smile_threshold: 0.3`
- 检查日志：`log_level: DEBUG`

### 误触发太多

**增加稳定性**：
- 提高置信度：`gesture_confidence_threshold: 0.8`
- 增加稳定时间：`gesture_stable_duration: 0.5`
- 增加冷却时间：`gesture_cooldown: 3.0`

**减少检测**：
- 降低帧率：`target_fps: 8`
- 增加跳帧：`skip_frames: 2`

### 性能问题（FPS 太低）

**优化建议**：
1. 降低分辨率：`frame_width: 256`
2. 关闭调试可视化：`debug_visualization: false`
3. 关闭表情识别：`enable_expression_detection: false`
4. 增加跳帧：`skip_frames: 2`

## 🏠 Home Assistant 自动化示例

### 基础手势控制

```yaml
automation:
  # 张开手掌开灯
  - alias: "张手开灯"
    trigger:
      platform: state
      entity_id: sensor.gesture_control
      to: "OPEN_PALM"
    action:
      service: light.turn_on
      target:
        entity_id: light.living_room
  
  # 握拳关灯
  - alias: "握拳关灯"
    trigger:
      platform: state
      entity_id: sensor.gesture_control
      to: "CLOSED_FIST"
    action:
      service: light.turn_off
      target:
        entity_id: light.living_room
```

### 表情控制（v1.0.7 新增）

```yaml
automation:
  # 张嘴暂停播放
  - alias: "张嘴暂停"
    trigger:
      platform: state
      entity_id: sensor.gesture_control
      to: "MOUTH_OPEN"
    action:
      service: media_player.media_pause
      target:
        entity_id: media_player.living_room
  
  # 微笑播放音乐
  - alias: "微笑播放"
    trigger:
      platform: state
      entity_id: sensor.gesture_control
      to: "SMILE"
    action:
      service: media_player.media_play
      target:
        entity_id: media_player.living_room
  
  # 打哈欠启动睡眠模式
  - alias: "哈欠睡眠"
    trigger:
      platform: state
      entity_id: sensor.gesture_control
      to: "YAWNING"
    action:
      service: scene.turn_on
      target:
        entity_id: scene.sleep_mode
```

### 使用 Blendshapes 的高级自动化

```yaml
automation:
  # 根据微笑程度调整灯光亮度
  - alias: "微笑亮度"
    trigger:
      platform: state
      entity_id: sensor.gesture_control
      to: "SMILE"
    action:
      service: light.turn_on
      target:
        entity_id: light.bedroom
      data:
        brightness: >
          {{ (state_attr('sensor.gesture_control', 'blendshapes').mouthSmile * 255) | int }}
  
  # 根据嘴巴张开程度调整音量
  - alias: "张嘴音量"
    trigger:
      platform: state
      entity_id: sensor.gesture_control
    condition:
      - condition: template
        value_template: >
          {{ state_attr('sensor.gesture_control', 'blendshapes').mouthOpen is defined }}
    action:
      service: media_player.volume_set
      target:
        entity_id: media_player.living_room
      data:
        volume_level: >
          {{ state_attr('sensor.gesture_control', 'blendshapes').mouthOpen }}
```

## ⚡ 性能与优化

### 性能指标

**仅手势识别**（v1.0.6）：
- FPS：15 @ 320×240
- CPU：40-50%
- 内存：~400 MB
- 响应时间：0.15-0.25 秒

**手势 + 表情识别**（v1.0.7）：
- FPS：10-12 @ 320×240
- CPU：55-65%
- 内存：~500-600 MB
- 响应时间：0.20-0.35 秒

**手势 + 表情 + 调试可视化**：
- FPS：9-11 @ 320×240
- CPU：60-70%
- 内存：~500-600 MB
- 响应时间：0.25-0.40 秒

### 优化建议

**提升性能**：
1. 降低分辨率：`frame_width: 256, frame_height: 192`
2. 增加跳帧：`skip_frames: 2`（处理一半的帧）
3. 关闭调试可视化：`debug_visualization: false`
4. 关闭表情识别：`enable_expression_detection: false`
5. 关闭详细数据：`publish_detailed_blendshapes: false`

**提升准确性**：
1. 提高分辨率：`frame_width: 640, frame_height: 480`
2. 处理所有帧：`skip_frames: 1`
3. 提高置信度阈值：`gesture_confidence_threshold: 0.8`
4. 增加稳定时间：`gesture_stable_duration: 0.5`

**平衡配置**（推荐）：
```yaml
frame_width: 320
frame_height: 240
target_fps: 15
skip_frames: 1
gesture_confidence_threshold: 0.65
enable_expression_detection: true
debug_visualization: false  # 生产环境关闭
```

## 📊 数据隐私

- ✅ **所有处理均在本地**：视频流不会上传到云端
- ✅ **不存储视频**：仅实时处理，不保存任何帧
- ✅ **仅发布状态**：只通过 MQTT 发布识别结果
- ✅ **可选 Blendshapes**：可以关闭详细数据发布

## 🆕 更新日志

### v1.0.7（2025-11-30）
- ✨ 添加面部表情识别（10+ 种表情）
- ✨ 支持 52 个 Blendshapes 系数输出
- ✨ 实时调试可视化（FPS、手势、表情）
- 🐛 修复 MediaPipe Image 构造错误
- 🐛 优化错误日志输出
- ⚡ 性能优化（降低分辨率到 320×240）
- 📝 完善中文文档

### v1.0.6（2025-11-30）
- ⚡ 性能优化（降低分辨率、减少检测次数）
- 🐛 修复手势触发逻辑（改为基于计数）

### v1.0.5（2025-11-30）
- 🐛 修复时间窗口逻辑 Bug

### v1.0.0（初始版本）
- ✨ 基础手势识别（4 种手势）
- ✨ MQTT 自动发现集成
- ✨ RTSP 视频流处理
- ✨ 防抖动机制

## 📄 许可证

MIT License - 可自由使用和修改。

## 🙏 致谢

- **MediaPipe**：Google 的机器学习框架，用于手部和面部追踪
- **OpenCV**：计算机视觉库
- **Home Assistant**：开源家庭自动化平台
- **Paho MQTT**：MQTT 客户端库

## 🔗 相关链接

- [安装指南](INSTALL.md)
- [详细文档](DOCS.md)
- [快速开始](QUICKSTART.md)
- [故障排查](TROUBLESHOOTING_INSTALL.md)
- [更新日志](CHANGELOG.md)

## 💬 支持与反馈

如有问题或建议，欢迎：
- 提交 [Issue](https://github.com/你的用户名/shoushi-HA/issues)
- 发起 [Pull Request](https://github.com/你的用户名/shoushi-HA/pulls)
- 参与 [Discussions](https://github.com/你的用户名/shoushi-HA/discussions)

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**
