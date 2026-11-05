"""
==============================================================================
模块名称: os_layer/idle_detector.py
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    本模块利用 Windows 内核接口检测用户的“物理键鼠空闲时间”。
    
底层原理:
    调用 Windows 底层 user32.dll 导出的 GetLastInputInfo 函数。
    操作系统在内核层面记录了用户上一次敲击键盘或移动鼠标的毫秒级时间戳 (TickCount)。
    本检测不会监听用户具体按了哪个键（绝无键盘记录器风险，保障用户隐私安全），
    仅计算“距离上一次任意操作过去了多久”。
==============================================================================
"""

import ctypes


class _LASTINPUTINFO(ctypes.Structure):
    """
    定义与 Windows C 语言 API 对齐的结构体
    """
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint)
    ]


class IdleDetector:
    """
    空闲状态探测器
    """
    def __init__(self):
        self._lii = _LASTINPUTINFO()
        self._lii.cbSize = ctypes.sizeof(_LASTINPUTINFO)

    def get_idle_seconds(self) -> float:
        """
        获取当前距离用户最后一次活动（敲键盘/动鼠标）已过去的秒数
        """
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(self._lii)):
            # 获取系统开机至今的毫秒总数
            current_tick = ctypes.windll.kernel32.GetTickCount()
            # 两个时间戳做差值即为闲置时间
            elapsed_ms = current_tick - self._lii.dwTime
            return max(0.0, elapsed_ms / 1000.0)
        return 0.0

    def is_user_idle(self, threshold_seconds: float) -> bool:
        """
        判断用户当前是否已达到空闲阈值
        :param threshold_seconds: 认定的空闲阈值（秒）
        """
        return self.get_idle_seconds() >= threshold_seconds
