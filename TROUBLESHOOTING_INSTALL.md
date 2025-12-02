# 安装进度查看指南

如果 addon 安装时间过长或卡在转圈状态，可以通过以下方式查看进度。

## 方法 1：查看 Supervisor 日志（推荐）

### 步骤：

1. **打开设置**
   - 进入 **设置** → **系统** → **日志**

2. **切换到 Supervisor 日志**
   - 在日志页面顶部，点击下拉菜单
   - 选择 **Supervisor**

3. **查看构建输出**
   - 向下滚动到最新的日志
   - 应该能看到类似输出：
   ```
   INFO (SyncWorker_X) [supervisor.docker.addon] Build add-on 3d064c2c/amd64-addon-mediapipe_gesture_control:1.0.0
   INFO (SyncWorker_X) [supervisor.docker.interface] Downloading python:3.11-slim-bookworm
   INFO (SyncWorker_X) [supervisor.docker.interface] #1 [internal] load build definition
   INFO (SyncWorker_X) [supervisor.docker.interface] #2 FROM python:3.11-slim-bookworm
   INFO (SyncWorker_X) [supervisor.docker.interface] #3 RUN apt-get update...
   INFO (SyncWorker_X) [supervisor.docker.interface] #4 RUN pip3 install...
   ```

4. **判断状态**
   - ✅ 正常：看到持续的日志输出
   - ⚠️ 卡住：超过 3 分钟没有新日志
   - ❌ 失败：看到 ERROR 或 failed 信息

## 方法 2：使用 SSH/Terminal Addon 查看（详细）

如果你安装了 **Terminal & SSH** addon：

### 步骤：

1. **打开 Terminal & SSH**
   - 进入 **设置** → **加载项**
   - 找到并打开 "Terminal & SSH"
   - 点击 **START**（如果未启动）
   - 点击 **OPEN WEB UI**

2. **查看 Docker 构建日志**
   ```bash
   # 查看正在运行的 Docker 进程
   docker ps -a
   
   # 查看最近的构建日志
   docker logs --tail 100 -f hassio_supervisor
   
   # 或者查看 Supervisor 日志
   ha supervisor logs
   ```

3. **实时监控构建**
   ```bash
   # 查看 Docker 构建进度
   watch -n 2 'docker ps -a | grep -i build'
   ```

## 方法 3：查看系统资源使用

### 检查是否在下载/构建：

1. **打开 Supervisor**
   - 进入 **设置** → **系统** → **Supervisor**
   - 查看 **主机** 部分

2. **观察 CPU/内存使用**
   - CPU 使用率 > 50%：可能在编译依赖
   - 网络活动：可能在下载镜像
   - 内存使用高：正在处理数据

## 常见安装阶段和耗时

### 阶段 1：下载基础镜像（2-5 分钟）
```
#2 [internal] load metadata for python:3.11-slim-bookworm
#3 [ 1/10] FROM python:3.11-slim-bookworm
Pulling from library/python...
```
**预期时间**：2-5 分钟（取决于网络速度）

### 阶段 2：安装系统依赖（1-2 分钟）
```
#4 [ 2/10] RUN apt-get update && apt-get install...
Get:1 http://deb.debian.org/debian bookworm InRelease
Reading package lists...
```
**预期时间**：1-2 分钟

### 阶段 3：安装 Python 包（3-8 分钟）
```
#8 [ 6/10] RUN pip3 install --no-cache-dir -r requirements.txt
Collecting opencv-python-headless==4.8.1.78
Downloading opencv_python_headless... (68.6 MB)
Collecting mediapipe==0.10.8
Downloading mediapipe... (65 MB)
```
**预期时间**：3-8 分钟（MediaPipe 包很大）

### 阶段 4：复制文件（10-30 秒）
```
#9 [ 7/10] COPY src/
#10 [ 8/10] COPY main.py config.py
```
**预期时间**：少于 1 分钟

**总计预期时间**：约 8-15 分钟

## 如何判断是否卡住

### ✅ 正常情况：
- Supervisor 日志持续更新
- 看到进度百分比或 MB 下载量
- CPU/网络有活动

### ⚠️ 可能卡住：
- 超过 5 分钟没有新日志
- 停在某个下载步骤不动
- CPU 和网络都没有活动

### ❌ 确定失败：
- 看到 ERROR 字样
- 看到 "exit code 1"
- 构建进程消失

## 如果确定卡住了怎么办

### 方案 1：等待并重试

1. **等待 20 分钟**
   - 有时下载很慢，耐心等待

2. **取消安装**
   - 刷新浏览器页面
   - 或点击其他地方再返回

3. **重新安装**
   - 再次点击 **安装** 按钮

### 方案 2：清理并重试

如果有 SSH 访问：

```bash
# 1. 停止 Supervisor
ha supervisor stop

# 2. 清理 Docker 缓存
docker system prune -f

# 3. 重启 Supervisor
ha supervisor start

# 4. 等待 Supervisor 重启（约 1 分钟）
# 5. 返回 Web UI 重新安装 addon
```

### 方案 3：检查网络

```bash
# 测试能否访问 Docker Hub
ping -c 3 registry-1.docker.io

# 测试能否访问 PyPI
ping -c 3 pypi.org

# 如果网络有问题，检查防火墙或代理设置
```

## 常见问题和解决方案

### Q1: 卡在 "Downloading python:3.11-slim-bookworm"

**原因**：基础镜像较大（约 130 MB）

**解决方案**：
- 耐心等待 5-10 分钟
- 检查网络连接
- 如果网络慢，考虑使用镜像加速器

### Q2: 卡在 "Downloading mediapipe"

**原因**：MediaPipe 包很大（约 65 MB）

**解决方案**：
- 等待 3-5 分钟
- 观察下载进度（如果显示百分比）

### Q3: 反复失败并显示同样的错误

**解决方案**：
1. 完全删除 addon（如果已部分安装）
2. 删除仓库
3. 清理 Docker 缓存
4. 重新添加仓库
5. 重新安装

### Q4: "Out of disk space" 错误

**解决方案**：
```bash
# 查看磁盘空间
df -h

# 清理 Docker
docker system prune -a -f

# 清理旧的 addon 镜像
docker images | grep addon | awk '{print $3}' | xargs docker rmi
```

## 实时监控命令（Terminal）

如果你想持续监控：

```bash
# 方法 1：监控 Supervisor 日志
ha supervisor logs -f

# 方法 2：监控 Docker 事件
docker events

# 方法 3：监控系统资源
watch -n 1 'free -h && df -h'

# 方法 4：查看所有容器状态
watch -n 2 'docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"'
```

## 预期的成功安装日志示例

完整的成功日志应该类似：

```
2024-11-30 12:00:00 INFO (SyncWorker_0) [supervisor.docker.addon] Build add-on 3d064c2c/amd64-addon-mediapipe_gesture_control:1.0.0
2024-11-30 12:00:01 INFO (SyncWorker_0) [supervisor.docker.interface] #1 [internal] load build definition from Dockerfile
2024-11-30 12:00:01 INFO (SyncWorker_0) [supervisor.docker.interface] #1 transferring dockerfile: 783B done
2024-11-30 12:00:01 INFO (SyncWorker_0) [supervisor.docker.interface] #1 DONE 0.0s
2024-11-30 12:00:02 INFO (SyncWorker_0) [supervisor.docker.interface] #2 [internal] load metadata for python:3.11-slim-bookworm
2024-11-30 12:00:03 INFO (SyncWorker_0) [supervisor.docker.interface] #2 DONE 1.2s
2024-11-30 12:02:15 INFO (SyncWorker_0) [supervisor.docker.interface] #3 [ 1/10] FROM python:3.11-slim-bookworm
2024-11-30 12:02:15 INFO (SyncWorker_0) [supervisor.docker.interface] #3 DONE (downloaded)
2024-11-30 12:03:20 INFO (SyncWorker_0) [supervisor.docker.interface] #4 [ 2/10] RUN apt-get update...
2024-11-30 12:03:45 INFO (SyncWorker_0) [supervisor.docker.interface] #4 DONE
2024-11-30 12:03:46 INFO (SyncWorker_0) [supervisor.docker.interface] #5 [ 3/10] RUN pip3 install bashio
2024-11-30 12:03:55 INFO (SyncWorker_0) [supervisor.docker.interface] #5 Successfully installed bashio
2024-11-30 12:03:55 INFO (SyncWorker_0) [supervisor.docker.interface] #5 DONE
2024-11-30 12:03:56 INFO (SyncWorker_0) [supervisor.docker.interface] #8 [ 6/10] RUN pip3 install -r requirements.txt
2024-11-30 12:10:30 INFO (SyncWorker_0) [supervisor.docker.interface] #8 Successfully installed mediapipe-0.10.8 opencv-python-headless-4.8.1.78 paho-mqtt-1.6.1 numpy-1.24.3
2024-11-30 12:10:30 INFO (SyncWorker_0) [supervisor.docker.interface] #8 DONE
2024-11-30 12:10:32 INFO (SyncWorker_0) [supervisor.docker.interface] Successfully built
2024-11-30 12:10:33 INFO (SyncWorker_0) [supervisor.docker] Successfully built 3d064c2c/amd64-addon-mediapipe_gesture_control:1.0.0
2024-11-30 12:10:33 INFO (MainThread) [supervisor.addons] Successfully installed addon MediaPipe Gesture Control
```

## 需要帮助？

如果按照上述方法仍然无法解决：

1. **截图最新的日志**
   - Supervisor 日志的最后 50 行

2. **提供系统信息**
   - Home Assistant 版本
   - Supervisor 版本
   - 主机系统类型

3. **描述卡住的位置**
   - 最后看到的日志是什么
   - 卡了多长时间

然后可以继续寻求帮助！
