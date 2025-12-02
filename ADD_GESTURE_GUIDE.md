# 快速添加新手势指南

## 步骤 1：在 gesture_engine.py 中添加手势名称

```python
# 在 __init__ 方法中添加
self.GESTURES = {
    'OPEN_PALM': 'Open Palm',
    'CLOSED_FIST': 'Closed Fist',
    'POINTING_UP': 'Pointing Up',
    'OK_SIGN': 'OK Sign',
    'PEACE_SIGN': 'Peace Sign',      # 新增：胜利手势
    'THUMBS_UP': 'Thumbs Up',        # 新增：点赞
    'ROCK_SIGN': 'Rock Sign',        # 新增：摇滚
    'NONE': 'None'
}
```

## 步骤 2：添加检测函数

```python
def _is_peace_sign(self, landmarks) -> bool:
    """检测胜利/和平手势 ✌️"""
    fingers = self._get_fingers_extended(landmarks)
    
    # 只有食指和中指伸直
    if (not fingers[0] and  # 拇指卷曲
        fingers[1] and      # 食指伸直
        fingers[2] and      # 中指伸直
        not fingers[3] and  # 无名指卷曲
        not fingers[4]):    # 小指卷曲
        return True
    
    return False
```

## 步骤 3：在 _recognize_gesture 中添加检测逻辑

```python
def _recognize_gesture(self, landmarks) -> Tuple[str, float]:
    lm = landmarks.landmark
    fingers_extended = self._get_fingers_extended(lm)
    
    # 现有手势检测...
    if all(fingers_extended):
        return 'OPEN_PALM', 0.95
    
    if not any(fingers_extended):
        return 'CLOSED_FIST', 0.95
    
    # 新增：胜利手势检测
    if self._is_peace_sign(lm):
        return 'PEACE_SIGN', 0.90
    
    if (fingers_extended[1] and not fingers_extended[2] and 
        not fingers_extended[3] and not fingers_extended[4]):
        return 'POINTING_UP', 0.9
    
    if self._is_ok_sign(lm):
        return 'OK_SIGN', 0.85
    
    return 'NONE', 0.5
```

## 步骤 4：更新版本并推送

```bash
# 修改 config.yaml
version: "1.0.7"

# 提交
git add src/gesture_engine.py config.yaml
git commit -m "Add PEACE_SIGN gesture support"
git push
```

## 步骤 5：重建 addon

在 Home Assistant 中：
1. 进入 设置 → 加载项 → MediaPipe Gesture Control
2. 点击 "重建"
3. 重启

## 完整示例：添加 3 个新手势

```python
# gesture_engine.py

def _recognize_gesture(self, landmarks) -> Tuple[str, float]:
    lm = landmarks.landmark
    fingers = self._get_fingers_extended(lm)
    
    # 张开手掌
    if all(fingers):
        return 'OPEN_PALM', 0.95
    
    # 握拳
    if not any(fingers):
        return 'CLOSED_FIST', 0.95
    
    # 点赞 👍
    if fingers[0] and not any(fingers[1:]):
        thumb_tip = lm[4]
        wrist = lm[0]
        if thumb_tip.y < wrist.y - 0.1:
            return 'THUMBS_UP', 0.90
    
    # 胜利 ✌️
    if not fingers[0] and fingers[1] and fingers[2] and not fingers[3] and not fingers[4]:
        return 'PEACE_SIGN', 0.90
    
    # 摇滚 🤟
    if fingers[1] and not fingers[2] and not fingers[3] and fingers[4]:
        return 'ROCK_SIGN', 0.85
    
    # 食指向上
    if fingers[1] and not fingers[2] and not fingers[3] and not fingers[4]:
        return 'POINTING_UP', 0.9
    
    # OK手势
    if self._is_ok_sign(lm):
        return 'OK_SIGN', 0.85
    
    return 'NONE', 0.5
```

## 测试新手势

在 Home Assistant 日志中查看：

```
[Processed 20] Hand detected: PEACE_SIGN (confidence: 0.90) [buffer: 2]
✓ Gesture PEACE_SIGN is STABLE (last 2 detections consistent)
✓ Gesture TRIGGERED: PEACE_SIGN (confidence: 0.90)
```

在 Home Assistant 中：
- 开发者工具 → 状态 → 搜索 `gesture_control`
- 状态应该显示 `PEACE_SIGN`

## 调试技巧

### 打印手指状态

```python
def _recognize_gesture(self, landmarks):
    lm = landmarks.landmark
    fingers = self._get_fingers_extended(lm)
    
    # 调试：打印手指状态
    finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
    logger.debug(f"Fingers: {', '.join(f'{n}={f}' for n, f in zip(finger_names, fingers))}")
    
    # 继续手势识别...
```

### 降低日志级别查看详情

在 config.yaml 中：
```yaml
log_level: "DEBUG"
```

## 常见问题

**Q: 新手势不触发？**
- 检查手势是否清晰标准
- 降低 `gesture_confidence_threshold`
- 查看 DEBUG 日志确认手指状态

**Q: 新手势和旧手势冲突？**
- 调整检测顺序（高优先级的放前面）
- 增加更严格的约束条件
- 提高冲突手势的置信度要求

**Q: 如何让某个手势更容易触发？**
- 提高该手势的置信度（返回值）
- 降低全局 `gesture_confidence_threshold`
- 在检测逻辑中放宽条件
