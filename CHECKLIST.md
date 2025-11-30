# 部署前检查清单

在将项目部署为 Home Assistant Addon 之前，请按照此清单检查所有必要步骤。

## ✅ 文件完整性检查

### 核心 Addon 文件（必需）
- [x] `config.yaml` - Addon 配置定义
- [x] `Dockerfile` - 容器镜像定义
- [x] `build.yaml` - 多架构构建配置
- [x] `run.sh` - 启动脚本
- [x] `DOCS.md` - 用户文档（显示在 HA UI）
- [x] `CHANGELOG.md` - 版本历史

### 应用代码文件（必需）
- [x] `main.py` - 主程序
- [x] `config.py` - 配置管理
- [x] `requirements.txt` - Python 依赖
- [x] `src/gesture_engine.py` - 手势识别引擎
- [x] `src/mqtt_client.py` - MQTT 客户端
- [x] `src/__init__.py` - 模块初始化

### 文档文件（推荐）
- [x] `README.md` - 项目说明
- [x] `INSTALL.md` - 安装指南
- [x] `QUICKSTART.md` - 快速开始
- [x] `HA_ADDON_STRUCTURE.md` - 项目结构说明

### 配置文件（推荐）
- [x] `.gitignore` - Git 忽略规则
- [x] `.dockerignore` - Docker 构建忽略
- [x] `.gitattributes` - Git 属性
- [x] `repository.json` - 仓库元数据

### 国际化支持（可选）
- [x] `translations/en.yaml` - 英文翻译
- [x] `translations/zh-Hans.yaml` - 中文翻译

### 图标资源（待添加）
- [ ] `icon.png` - 128x128 像素图标
- [ ] `logo.png` - 256x256+ 像素徽标

## 📝 配置修改检查

### 1. 更新仓库信息

**文件**: `repository.json`
```json
{
  "name": "MediaPipe Gesture Control Addons",
  "url": "https://github.com/yanfeng17/shoushi-HA",
  "maintainer": "yanfeng17 <yanfeng17@users.noreply.github.com>"
}
```

**已完成**:
- [x] 替换 GitHub URL
- [x] 替换维护者信息

---

**文件**: `config.yaml`
```yaml
url: "https://github.com/yanfeng17/shoushi-HA"
```

**已完成**:
- [x] 替换 URL

---

### 2. 更新文档链接

需要在以下文件中替换 GitHub 链接：

**文件列表**:
- [ ] `README.md`
- [ ] `DOCS.md`
- [ ] `INSTALL.md`
- [ ] `QUICKSTART.md`
- [ ] `HA_ADDON_STRUCTURE.md`

**搜索并替换**:
```
已完成：所有文件已更新为
https://github.com/yanfeng17/shoushi-HA
```
```

---

### 3. 验证配置文件语法

**config.yaml**:
- [ ] YAML 语法正确（缩进使用空格，不用Tab）
- [ ] 所有必需字段已填写
- [ ] Schema 定义与 options 匹配

**验证方法**:
```bash
# 在线验证
# https://www.yamllint.com/

# 或使用工具
yamllint config.yaml
```

---

**build.yaml**:
- [ ] 所有架构都有对应的基础镜像
- [ ] 镜像标签正确

---

**run.sh**:
- [ ] 有执行权限（`chmod +x run.sh`）
- [ ] 使用 Unix 换行符（LF，不是 CRLF）

**检查和修改**:
```bash
# 检查换行符
file run.sh

# 转换为 Unix 格式（如果需要）
dos2unix run.sh
# 或
sed -i 's/\r$//' run.sh
```

---

### 4. 检查默认配置

**config.yaml** 中的默认值:
- [ ] `rtsp_url` 是示例值，用户需要修改
- [ ] `mqtt_broker` 默认为 `core-mosquitto`（内置 broker）
- [ ] 其他参数有合理的默认值

---

## 🎨 创建图标（重要）

### Icon.png (必需)
- **尺寸**: 128x128 像素
- **格式**: PNG，透明背景
- **内容**: 手势、手掌或 AI 相关图标

### Logo.png (推荐)
- **尺寸**: 256x256 像素或更大
- **格式**: PNG，透明背景
- **内容**: 与 icon 一致，更精细

### 创建方法

**方案 1: 在线工具**
- [Flaticon](https://www.flaticon.com/) - 搜索 "hand gesture"
- [Canva](https://www.canva.com/) - 设计自定义图标
- [Remove.bg](https://www.remove.bg/) - 去除背景

**方案 2: 使用 Emoji**
```bash
# 使用 ImageMagick 将 emoji 转为 PNG
convert -background none -font "Apple Color Emoji" -pointsize 100 label:"🤚" icon.png
```

**方案 3: 使用现有图片**
```bash
# 调整尺寸
convert input.png -resize 128x128 icon.png
convert input.png -resize 256x256 logo.png
```

---

## 🔒 安全检查

- [ ] `.gitignore` 包含敏感文件（.env, *.log）
- [ ] 示例 RTSP URL 不包含真实密码
- [ ] MQTT 密码使用配置项，不硬编码
- [ ] 文档中没有泄露敏感信息

---

## 🧪 本地测试（推荐）

### 测试 Python 应用

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export RTSP_URL="rtsp://admin:password@192.168.1.100:554/stream1"
export MQTT_BROKER="192.168.1.1"
export MQTT_PORT="1883"

# 运行应用
python main.py
```

**检查**:
- [ ] 应用能成功启动
- [ ] RTSP 连接成功
- [ ] MQTT 连接成功
- [ ] 手势识别正常工作

---

### 测试 Docker 构建

```bash
# 构建镜像
docker build -t gesture-control-test .

# 运行容器
docker run --rm \
  -e RTSP_URL="rtsp://..." \
  -e MQTT_BROKER="192.168.1.1" \
  --network host \
  gesture-control-test
```

**检查**:
- [ ] 镜像构建成功
- [ ] 容器能正常启动
- [ ] 日志输出正常
- [ ] 功能正常工作

---

## 📤 部署到 GitHub

### 1. 初始化 Git 仓库

```bash
cd shoushi-HA
git init
git add .
git commit -m "Initial commit: MediaPipe Gesture Control addon"
```

### 2. 创建 GitHub 仓库

1. 访问 https://github.com/new
2. 仓库名称: `ha-addon-gesture-control`
3. 描述: "Home Assistant addon for real-time hand gesture recognition"
4. 公开或私有（建议公开）
5. 不要初始化 README（我们已经有了）
6. 创建仓库

### 3. 推送到 GitHub

```bash
git remote add origin https://github.com/你的用户名/ha-addon-gesture-control.git
git branch -M main
git push -u origin main
```

**检查**:
- [ ] 所有文件已上传
- [ ] 仓库可访问
- [ ] README 正确显示

---

## 🏠 在 Home Assistant 中测试

### 1. 添加仓库

- 设置 → 加载项 → ⋮ → 仓库
- 添加: `https://github.com/你的用户名/ha-addon-gesture-control`

**检查**:
- [ ] 仓库添加成功
- [ ] 能看到 addon 卡片

---

### 2. 安装 Addon

- 点击 addon 卡片
- 点击"安装"
- 等待构建完成

**检查**:
- [ ] 安装成功
- [ ] 没有构建错误
- [ ] 配置页面正确显示

---

### 3. 配置 Addon

填写必要配置：
- [ ] RTSP URL 正确
- [ ] MQTT 配置正确
- [ ] 其他参数根据需要调整

---

### 4. 启动和验证

- 点击"START"
- 切换到"Log"标签

**检查日志**:
- [ ] 成功连接 MQTT
- [ ] 成功连接 RTSP
- [ ] 发送 Discovery 配置
- [ ] 开始处理视频帧
- [ ] 没有错误信息

---

### 5. 验证集成

**开发者工具 → 状态**:
- [ ] `sensor.gesture_control` 实体已创建
- [ ] 状态随手势变化
- [ ] 属性包含 confidence 和 timestamp

**创建测试自动化**:
```yaml
automation:
  - alias: "测试手势识别"
    trigger:
      platform: state
      entity_id: sensor.gesture_control
    action:
      service: persistent_notification.create
      data:
        title: "手势检测"
        message: "检测到: {{ trigger.to_state.state }}"
```

**检查**:
- [ ] 自动化能触发
- [ ] 通知显示正确
- [ ] 响应及时

---

## 🎉 发布检查清单

准备正式发布时：

- [ ] 所有文档已更新
- [ ] 版本号正确（config.yaml）
- [ ] CHANGELOG 已更新
- [ ] 图标和徽标已添加
- [ ] 在实际环境测试通过
- [ ] GitHub 仓库 README 完整
- [ ] 添加 GitHub Topics（home-assistant, addon, mediapipe）
- [ ] 创建 GitHub Release
- [ ] 在 Home Assistant 社区发帖

---

## 📞 获取帮助

如果遇到问题：

1. **查看文档**:
   - [INSTALL.md](INSTALL.md)
   - [DOCS.md](DOCS.md)
   - [HA_ADDON_STRUCTURE.md](HA_ADDON_STRUCTURE.md)

2. **检查日志**:
   - Addon 日志
   - Home Assistant 核心日志
   - Supervisor 日志

3. **社区支持**:
   - Home Assistant 社区论坛
   - GitHub Issues
   - Discord 频道

---

## ✨ 可选改进

完成基本部署后，可以考虑：

- [ ] 添加更多手势类型
- [ ] 实现手势自定义训练
- [ ] 添加 Web UI 配置界面
- [ ] 支持多摄像头
- [ ] 添加性能监控
- [ ] 实现手势历史记录
- [ ] 添加手势可视化
- [ ] 支持手势宏（组合手势）
- [ ] 集成 TTS 反馈
- [ ] 添加测试用例

---

**完成日期**: ___________

**部署者**: ___________

**版本**: 1.0.0
