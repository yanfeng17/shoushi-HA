import logging
import time
import numpy as np
from collections import deque
from typing import Optional, Tuple, Dict
import config

logger = logging.getLogger(__name__)


class MotionDetector:
    """
    动态手势检测器
    追踪手部运动轨迹，识别挥手、滑动等动态手势
    
    支持的动态手势：
    - WAVE: 挥手（水平来回摆动）
    - SWIPE_LEFT: 向左滑动
    - SWIPE_RIGHT: 向右滑动
    - SWIPE_UP: 向上滑动
    - SWIPE_DOWN: 向下滑动
    """
    
    def __init__(self):
        # 位置历史缓冲区（存储最近的手腕位置）
        self.position_history = deque(maxlen=config.MOTION_DETECTION_WINDOW)
        
        # 最后检测到的动态手势（用于防抖）
        self.last_motion_gesture: Optional[str] = None
        self.last_motion_time: float = 0
        self.motion_cooldown: float = 1.0  # 动态手势冷却时间（秒）
        
        logger.info(f"Motion Detector initialized (window={config.MOTION_DETECTION_WINDOW} frames)")
    
    def add_hand_position(self, wrist_landmark, timestamp: float):
        """
        添加手腕位置到历史记录
        
        Args:
            wrist_landmark: MediaPipe 手腕关键点（landmark[0]）
            timestamp: 时间戳
        """
        self.position_history.append({
            'x': wrist_landmark.x,  # 0.0-1.0 (归一化坐标)
            'y': wrist_landmark.y,
            'z': wrist_landmark.z,
            'time': timestamp
        })
    
    def reset(self):
        """重置位置历史（手消失时调用）"""
        self.position_history.clear()
    
    def detect_motion(self) -> Tuple[Optional[str], float]:
        """
        检测动态手势
        
        Returns:
            Tuple of (gesture_name, confidence)
            - gesture_name: 'WAVE', 'SWIPE_LEFT', 'SWIPE_RIGHT', 'SWIPE_UP', 'SWIPE_DOWN' 或 None
            - confidence: 0.0-1.0
        """
        current_time = time.time()
        
        # 冷却检查
        if (self.last_motion_gesture and 
            current_time - self.last_motion_time < self.motion_cooldown):
            return None, 0.0
        
        # 历史记录不足
        if len(self.position_history) < 10:
            return None, 0.0
        
        # 优先级：挥手 > 滑动（挥手需要更多数据点）
        
        # 1. 检测挥手
        if config.ENABLED_MOTION_GESTURES.get('WAVE', False):
            wave_confidence = self._detect_wave()
            if wave_confidence > 0.6:
                self.last_motion_gesture = 'WAVE'
                self.last_motion_time = current_time
                logger.info(f"✓ MOTION DETECTED: WAVE (confidence: {wave_confidence:.2f})")
                return 'WAVE', wave_confidence
        
        # 2. 检测滑动
        swipe_gesture, swipe_confidence = self._detect_swipe()
        if swipe_gesture and swipe_confidence > 0.7:
            # 检查该滑动方向是否启用
            if config.ENABLED_MOTION_GESTURES.get(swipe_gesture, False):
                self.last_motion_gesture = swipe_gesture
                self.last_motion_time = current_time
                logger.info(f"✓ MOTION DETECTED: {swipe_gesture} (confidence: {swipe_confidence:.2f})")
                return swipe_gesture, swipe_confidence
        
        return None, 0.0
    
    def _detect_wave(self) -> float:
        """
        挥手检测：检测 X 坐标的周期性变化
        
        算法：
        1. 提取最近帧的 X 坐标
        2. 找到局部最大值和最小值（峰值检测）
        3. 计算方向改变次数
        4. 检查摆动幅度是否 > 0.15
        5. 检查频率是否在 1-3 Hz 范围内
        
        Returns:
            置信度 (0.0-1.0)
        """
        # 需要足够的历史数据
        if len(self.position_history) < 20:
            return 0.0
        
        # 提取 X 坐标序列
        x_coords = [p['x'] for p in self.position_history]
        
        # 峰值检测（局部最大值和最小值）
        peaks = []      # (index, value)
        valleys = []    # (index, value)
        
        for i in range(1, len(x_coords) - 1):
            # 局部最大值（峰）
            if x_coords[i] > x_coords[i-1] and x_coords[i] > x_coords[i+1]:
                peaks.append((i, x_coords[i]))
            # 局部最小值（谷）
            elif x_coords[i] < x_coords[i-1] and x_coords[i] < x_coords[i+1]:
                valleys.append((i, x_coords[i]))
        
        # 至少需要 wave_min_cycles 个完整周期
        # 一个周期 = 峰 + 谷
        min_cycles = config.WAVE_MIN_CYCLES
        if len(peaks) < min_cycles or len(valleys) < min_cycles:
            logger.debug(f"Wave: insufficient cycles (peaks={len(peaks)}, valleys={len(valleys)}, need={min_cycles})")
            return 0.0
        
        # 计算平均摆动幅度
        amplitudes = []
        for peak in peaks:
            # 找到最近的谷
            nearest_valley = min(valleys, key=lambda v: abs(v[0] - peak[0]))
            amplitude = abs(peak[1] - nearest_valley[1])
            amplitudes.append(amplitude)
        
        avg_amplitude = sum(amplitudes) / len(amplitudes) if amplitudes else 0.0
        
        # 检查幅度是否足够（至少 15% 画面宽度）
        if avg_amplitude < 0.15:
            logger.debug(f"Wave: amplitude too small ({avg_amplitude:.3f} < 0.15)")
            return 0.0
        
        # 计算频率
        time_span = self.position_history[-1]['time'] - self.position_history[0]['time']
        if time_span <= 0:
            return 0.0
        
        frequency = len(peaks) / time_span
        
        # 挥手频率通常在 1-3 Hz（每秒 1-3 次摆动）
        if not (1.0 <= frequency <= 3.5):
            logger.debug(f"Wave: frequency out of range ({frequency:.2f} Hz)")
            return 0.0
        
        # 计算置信度（基于幅度和频率）
        amplitude_score = min(1.0, avg_amplitude * 3)  # 幅度越大越好
        frequency_score = 1.0 if (1.5 <= frequency <= 2.5) else 0.7  # 2Hz 左右最佳
        
        confidence = (amplitude_score + frequency_score) / 2
        
        logger.debug(f"Wave detected: amplitude={avg_amplitude:.3f}, frequency={frequency:.2f}Hz, confidence={confidence:.2f}")
        return confidence
    
    def _detect_swipe(self) -> Tuple[Optional[str], float]:
        """
        滑动检测：检测持续单向移动
        
        算法：
        1. 计算起点和终点的位置差
        2. 检查是否持续朝一个方向移动（单调性）
        3. 检查移动距离是否 > swipe_min_distance
        4. 检查时长是否 < swipe_max_duration
        
        Returns:
            (方向, 置信度) 或 (None, 0.0)
        """
        # 需要足够的数据点
        if len(self.position_history) < 10:
            return None, 0.0
        
        # 获取起点和终点
        start = self.position_history[0]
        end = self.position_history[-1]
        
        # 计算位移
        dx = end['x'] - start['x']
        dy = end['y'] - start['y']
        time_span = end['time'] - start['time']
        
        # 时长检查（滑动应该快速）
        if time_span > config.SWIPE_MAX_DURATION:
            return None, 0.0
        
        # 检查是否持续单向移动（单调性）
        x_coords = [p['x'] for p in self.position_history]
        y_coords = [p['y'] for p in self.position_history]
        
        x_monotonic = self._is_monotonic(x_coords)
        y_monotonic = self._is_monotonic(y_coords)
        
        # 水平滑动（左/右）
        if abs(dx) > abs(dy) and abs(dx) > config.SWIPE_MIN_DISTANCE:
            if x_monotonic:
                direction = 'SWIPE_RIGHT' if dx > 0 else 'SWIPE_LEFT'
                # 置信度基于移动距离和单调性程度
                confidence = min(1.0, abs(dx) * 2)
                logger.debug(f"Swipe detected: {direction}, distance={abs(dx):.3f}, time={time_span:.2f}s")
                return direction, confidence
        
        # 垂直滑动（上/下）
        if abs(dy) > abs(dx) and abs(dy) > config.SWIPE_MIN_DISTANCE:
            if y_monotonic:
                # 注意：Y 坐标向下递增，所以 dy > 0 表示向下
                direction = 'SWIPE_DOWN' if dy > 0 else 'SWIPE_UP'
                confidence = min(1.0, abs(dy) * 2)
                logger.debug(f"Swipe detected: {direction}, distance={abs(dy):.3f}, time={time_span:.2f}s")
                return direction, confidence
        
        return None, 0.0
    
    def _is_monotonic(self, values: list, tolerance: float = 0.8) -> bool:
        """
        检查序列是否单调（允许小幅波动）
        
        Args:
            values: 数值序列
            tolerance: 单调性阈值（0.8 表示至少 80% 朝同一方向）
            
        Returns:
            True if 序列基本单调递增或递减
        """
        if len(values) < 2:
            return False
        
        # 计算递增和递减的次数
        increasing = sum(1 for i in range(len(values)-1) if values[i+1] > values[i])
        decreasing = sum(1 for i in range(len(values)-1) if values[i+1] < values[i])
        
        total = len(values) - 1
        if total == 0:
            return False
        
        # 至少 tolerance% 朝同一方向
        increasing_ratio = increasing / total
        decreasing_ratio = decreasing / total
        
        return (increasing_ratio >= tolerance) or (decreasing_ratio >= tolerance)
    
    def get_stats(self) -> Dict:
        """获取运动检测统计信息（用于调试）"""
        if not self.position_history:
            return {}
        
        x_coords = [p['x'] for p in self.position_history]
        y_coords = [p['y'] for p in self.position_history]
        
        return {
            'buffer_size': len(self.position_history),
            'time_span': self.position_history[-1]['time'] - self.position_history[0]['time'] if len(self.position_history) > 1 else 0,
            'x_range': (min(x_coords), max(x_coords)),
            'y_range': (min(y_coords), max(y_coords)),
            'x_displacement': x_coords[-1] - x_coords[0],
            'y_displacement': y_coords[-1] - y_coords[0],
        }
