# Home Assistant Addon 项目结构说明

本文档说明该项目作为 Home Assistant Addon 的完整结构和部署方式。

## 📂 完整项目结构

```
shoushi-HA/
│
├── 🔧 Home Assistant Addon 核心文件
│   ├── config.yaml                 # Addon 配置定义（必需）
│   ├── build.yaml                  # 多架构构建配置
│   ├── Dockerfile                  # Docker 镜像定义（使用 HA 基础镜像）
│   ├── run.sh                      # Addon 启动脚本
│   └── repository.json             # Addon 仓库元数据
│
├── 📝 文档文件
│   ├── README.md                   # 项目主文档
│   ├── DOCS.md                     # 用户使用文档（显示在 HA UI）
│   ├── INSTALL.md                  # 详细安装指南
│   ├── QUICKSTART.md               # 5分钟快速入门
│   ├── CHANGELOG.md                # 版本更新日志
│   └── HA_ADDON_STRUCTURE.md       # 本文档
│
├── 🐍 Python 应用代码
│   ├── main.py                     # 主程序入口
│   ├── config.py                   # 配置管理（读取环境变量）
│   ├── requirements.txt            # Python 依赖
│   └── src/
│       ├── __init__.py
│       ├── gesture_engine.py       # MediaPipe 手势识别引擎
│       └── mqtt_client.py          # MQTT 客户端和 HA Discovery
│
├── 🌍 国际化支持
│   └── translations/
│       ├── en.yaml                 # 英文翻译
│       └── zh-Hans.yaml            # 简体中文翻译
│
├── 🎨 资源文件（待添加）
│   ├── icon.png.txt                # 图标占位符（需替换为真实 PNG）
│   └── logo.png.txt                # 徽标占位符（需替换为真实 PNG）
│
├── 🔒 配置文件
│   ├── .env.example                # 环境变量示例（用于 Docker Compose）
│   ├── .gitignore                  # Git 忽略规则
│   ├── .gitattributes              # Git 属性配置
│   └── .dockerignore               # Docker 构建忽略规则
│
└── 🐳 可选文件（非 Addon 必需）
    └── docker-compose.yml          # 独立 Docker 部署配置
```

## 🔑 关键文件说明

### 1. config.yaml - Addon 配置定义

这是 Home Assistant Addon 的核心配置文件，定义了：
- Addon 名称、版本、描述
- 支持的架构（amd64, aarch64, armv7, armhf, i386）
- 配置选项和默认值
- 配置项的验证规则（schema）

```yaml
name: "MediaPipe Gesture Control"
version: "1.0.0"
slug: mediapipe_gesture_control
arch: [aarch64, amd64, armhf, armv7, i386]
startup: application
boot: auto
host_network: true
options:
  rtsp_url: "rtsp://..."
  mqtt_broker: "core-mosquitto"
  # ... 其他选项
schema:
  rtsp_url: str
  mqtt_port: port
  # ... 验证规则
```

### 2. run.sh - Addon 启动脚本

使用 `bashio` 库从 HA 读取配置并设置环境变量：

```bash
#!/usr/bin/with-contenv bashio

export RTSP_URL=$(bashio::config 'rtsp_url')
export MQTT_BROKER=$(bashio::config 'mqtt_broker')
# ... 读取其他配置

cd /app
exec python3 main.py
```

### 3. build.yaml - 多架构构建

定义不同架构使用的基础镜像：

```yaml
build_from:
  aarch64: ghcr.io/home-assistant/aarch64-base-python:3.11-alpine3.19
  amd64: ghcr.io/home-assistant/amd64-base-python:3.11-alpine3.19
  # ...
```

### 4. Dockerfile - 容器镜像

使用 Home Assistant 的基础 Python 镜像，安装必要依赖：

```dockerfile
ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.11-alpine3.19
FROM ${BUILD_FROM}

# 安装系统依赖
RUN apk add --no-cache libstdc++ libgomp ...

# 安装 Python 依赖
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 复制应用代码和启动脚本
COPY src/ /app/src/
COPY main.py config.py /app/
COPY run.sh /
RUN chmod a+x /run.sh

CMD ["/run.sh"]
```

### 5. translations/ - 国际化

为 HA UI 提供多语言支持：

```yaml
# en.yaml
configuration:
  rtsp_url:
    name: RTSP URL
    description: The RTSP stream URL of your camera
```

## 🚀 部署流程

### 方式一：GitHub 仓库（推荐）

1. **上传到 GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yanfeng17/shoushi-HA.git
   git push -u origin main
   ```

2. **在 HA 中添加仓库**
   - 设置 → 加载项 → ⋮ → 仓库
   - 添加: `https://github.com/yanfeng17/shoushi-HA`

3. **安装 Addon**
   - 在加载项商店找到并安装
   - 配置并启动

### 方式二：本地安装（测试）

1. **复制到 HA 的 addons 目录**
   ```bash
   scp -r shoushi-HA root@homeassistant.local:/addons/local/mediapipe_gesture_control
   ```

2. **重新加载 Addons**
   - 设置 → 加载项 → ⋮ → 检查更新

3. **安装本地 Addon**
   - 在"本地加载项"中找到并安装

## ⚙️ 配置流程

用户在 HA UI 中配置 → `run.sh` 读取配置 → 设置环境变量 → `config.py` 使用环境变量 → 应用运行

```
HA UI (config.yaml)
    ↓
run.sh (bashio::config)
    ↓
环境变量 (export)
    ↓
config.py (os.getenv)
    ↓
main.py (使用配置)
```

## 📋 必须完成的任务

### ✅ 已完成
- [x] 创建所有核心文件
- [x] 配置 Home Assistant Addon 结构
- [x] 实现手势识别功能
- [x] MQTT Auto Discovery 集成
- [x] 编写完整文档
- [x] 添加国际化支持

### ⚠️ 待完成

1. **创建图标和徽标**
   - 将 `icon.png.txt` 替换为真实的 128x128 PNG 图标
   - 将 `logo.png.txt` 替换为真实的 256x256 PNG 徽标
   - 推荐使用手势或 AI 相关图标

2. **更新仓库信息**
   - 修改 `repository.json` 中的 URL 和维护者信息
   - 修改 `config.yaml` 中的 URL
   - 更新文档中的 GitHub 链接

3. **测试和验证**
   - 在实际 Home Assistant 环境中测试
   - 验证所有架构的构建
   - 测试 RTSP 连接和 MQTT 集成
   - 验证手势识别准确性

## 🔍 与标准 Docker 部署的区别

| 特性 | Docker Compose | HA Addon |
|------|----------------|----------|
| 配置方式 | 环境变量/.env | HA UI 配置页面 |
| 启动方式 | `docker-compose up` | HA Supervisor |
| 日志查看 | `docker logs` | HA UI Log 标签 |
| 自动重启 | restart: always | Watchdog |
| 网络 | 手动配置 | host_network: true |
| 更新 | 手动重建 | HA UI 一键更新 |
| 集成度 | 独立运行 | 深度集成 HA |

## 📚 相关资源

- [Home Assistant Addon 开发文档](https://developers.home-assistant.io/docs/add-ons)
- [Bashio 文档](https://github.com/hassio-addons/bashio)
- [MediaPipe 文档](https://google.github.io/mediapipe/)
- [MQTT Discovery 规范](https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery)

## 🆘 获取帮助

- **安装问题**: 查看 [INSTALL.md](INSTALL.md)
- **配置问题**: 查看 [DOCS.md](DOCS.md)
- **快速开始**: 查看 [QUICKSTART.md](QUICKSTART.md)
- **Bug 报告**: GitHub Issues
- **社区讨论**: Home Assistant 社区论坛
