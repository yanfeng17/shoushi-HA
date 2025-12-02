# 手势扩展示例

## 如何添加新手势

### 示例 1：点赞手势 👍

**特征**：只有拇指向上伸直，其余手指卷曲

```python
def _is_thumbs_up(self, landmarks) -> bool:
    """检测点赞手势：只有拇指伸直向上"""
    fingers = self._get_fingers_extended(landmarks)
    
    # 拇指伸直，其他手指卷曲
    if (fingers[0] and  # 拇指伸直
        not fingers[1] and  # 食指卷曲
        not fingers[2] and  # 中指卷曲
        not fingers[3] and  # 无名指卷曲
        not fingers[4]):    # 小指卷曲
        
        # 额外检查：拇指尖应该在手腕上方（y坐标更小）
        thumb_tip = landmarks[4]
        wrist = landmarks[0]
        if thumb_tip.y < wrist.y - 0.1:  # 拇指明显高于手腕
            return True
    
    return False

# 在 _recognize_gesture 中添加：
def _recognize_gesture(self, landmarks):
    lm = landmarks.landmark
    fingers_extended = self._get_fingers_extended(lm)
    
    # ... 现有的手势检测 ...
    
    # 添加点赞检测（在 OK_SIGN 之后）
    if self._is_thumbs_up(lm):
        return 'THUMBS_UP', 0.90
    
    return 'NONE', 0.5
```

### 示例 2：胜利手势 ✌️

**特征**：食指和中指伸直，其他手指卷曲

```python
def _is_peace_sign(self, landmarks) -> bool:
    """检测胜利/和平手势：食指和中指伸直"""
    fingers = self._get_fingers_extended(landmarks)
    
    if (not fingers[0] and  # 拇指卷曲
        fingers[1] and      # 食指伸直
        fingers[2] and      # 中指伸直
        not fingers[3] and  # 无名指卷曲
        not fingers[4]):    # 小指卷曲
        
        # 检查食指和中指是否分开（不是紧贴）
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        distance = self._distance(index_tip, middle_tip)
        
        if distance > 0.05:  # 两指分开
            return True
    
    return False

# 在 _recognize_gesture 中添加：
if self._is_peace_sign(lm):
    return 'PEACE_SIGN', 0.90
```

### 示例 3：数字手势（1-5）

**特征**：伸直不同数量的手指

```python
def _recognize_number(self, landmarks) -> Tuple[str, float]:
    """识别数字手势 1-5"""
    fingers = self._get_fingers_extended(landmarks)
    count = sum(fingers)
    
    if count == 1:
        if fingers[1]:  # 只有食指
            return 'NUMBER_ONE', 0.90
        elif fingers[0]:  # 只有拇指
            return 'THUMBS_UP', 0.90
    elif count == 2:
        if fingers[1] and fingers[2]:  # 食指+中指
            return 'NUMBER_TWO', 0.90
    elif count == 3:
        if fingers[1] and fingers[2] and fingers[3]:  # 食指+中指+无名指
            return 'NUMBER_THREE', 0.90
    elif count == 4:
        if not fingers[0]:  # 除了拇指都伸直
            return 'NUMBER_FOUR', 0.90
    elif count == 5:
        return 'NUMBER_FIVE', 0.95  # 已经实现为 OPEN_PALM
    
    return None, 0.0
```

### 示例 4：摇滚手势 🤟

**特征**：食指、中指、小指伸直

```python
def _is_rock_sign(self, landmarks) -> bool:
    """检测摇滚手势：食指和小指伸直，中指无名指卷曲"""
    fingers = self._get_fingers_extended(landmarks)
    
    if (fingers[1] and      # 食指伸直
        not fingers[2] and  # 中指卷曲
        not fingers[3] and  # 无名指卷曲
        fingers[4]):        # 小指伸直
        return True
    
    return False
```

### 示例 5：打电话手势 🤙

**特征**：拇指和小指伸直，其他卷曲

```python
def _is_call_sign(self, landmarks) -> bool:
    """检测打电话手势：拇指和小指伸直"""
    fingers = self._get_fingers_extended(landmarks)
    
    if (fingers[0] and      # 拇指伸直
        not fingers[1] and  # 食指卷曲
        not fingers[2] and  # 中指卷曲
        not fingers[3] and  # 无名指卷曲
        fingers[4]):        # 小指伸直
        return True
    
    return False
```

## 动态手势示例

### 挥手检测（需要时序数据）

```python
class GestureBuffer:
    def __init__(self):
        # ... 现有代码 ...
        self.hand_positions = deque(maxlen=10)  # 记录手掌位置
    
    def _detect_wave(self) -> bool:
        """检测挥手：手掌快速左右摆动"""
        if len(self.hand_positions) < 5:
            return False
        
        # 计算手掌 X 坐标的变化
        x_positions = [pos['x'] for pos in self.hand_positions]
        
        # 检测左右摆动（X 坐标来回变化）
        changes = 0
        for i in range(1, len(x_positions)):
            if abs(x_positions[i] - x_positions[i-1]) > 0.05:
                changes += 1
        
        # 如果有至少 3 次明显的位置变化，认为是挥手
        return changes >= 3
```

### 滑动检测

```python
def _detect_swipe(self) -> Optional[str]:
    """检测滑动方向"""
    if len(self.hand_positions) < 5:
        return None
    
    start_pos = self.hand_positions[0]
    end_pos = self.hand_positions[-1]
    
    dx = end_pos['x'] - start_pos['x']
    dy = end_pos['y'] - start_pos['y']
    
    # 水平滑动
    if abs(dx) > abs(dy) and abs(dx) > 0.2:
        return 'SWIPE_RIGHT' if dx > 0 else 'SWIPE_LEFT'
    
    # 垂直滑动
    if abs(dy) > abs(dx) and abs(dy) > 0.2:
        return 'SWIPE_DOWN' if dy > 0 else 'SWIPE_UP'
    
    return None
```

## 调试技巧

### 可视化手部关键点

```python
import cv2
import mediapipe as mp

def draw_landmarks(frame, hand_landmarks):
    """在帧上绘制手部关键点，用于调试"""
    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands
    
    mp_drawing.draw_landmarks(
        frame,
        hand_landmarks,
        mp_hands.HAND_CONNECTIONS,
        mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2),
        mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
    )
    
    return frame
```

### 打印关键点坐标

```python
def debug_landmarks(landmarks):
    """打印所有关键点坐标，用于分析"""
    for idx, lm in enumerate(landmarks.landmark):
        print(f"Point {idx}: x={lm.x:.3f}, y={lm.y:.3f}, z={lm.z:.3f}")
```

## 性能优化建议

1. **按难度顺序检测**：先检测简单手势（如握拳），再检测复杂手势（如OK手势）
2. **早期返回**：一旦匹配到高置信度手势，立即返回
3. **缓存计算**：重复使用 `_get_fingers_extended()` 的结果
4. **阈值调整**：根据实际测试调整距离和角度阈值

## 常见问题

### Q: 为什么我的手势识别不准？
A: 
- 检查光线条件（MediaPipe 需要良好光照）
- 调整置信度阈值
- 确保手势动作清晰、标准
- 检查摄像头角度和距离

### Q: 如何区分相似手势？
A: 
- 添加更多约束条件（如角度、距离）
- 提高某些手势的优先级
- 使用时序信息（动态手势）

### Q: 动态手势延迟大怎么办？
A: 
- 减少 buffer 大小
- 降低检测阈值
- 使用滑动窗口而不是固定窗口
