"""
==============================================================================
模块名称: os_layer/win_api.py
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    本模块封装与 Windows 操作系统窗口管理相关的底层 API。
    
设计范式与原则:
    1. 【高内聚低耦合】: 将所有与 ctypes / pywin32 相关的黑魔法逻辑集中于此，
       上层业务代码无需关心底层十六进制标志位。
    2. 【跨平台/版本健壮性】: 针对 Windows 不同版本（Win10/Win11）的 DPI 策略提供自适应兼容。
==============================================================================
"""

import ctypes
from typing import Tuple
import win32gui
import win32con
import win32api


def enable_dpi_awareness():
    """
    【开启高 DPI 感知】
    让 Windows 停止对本程序进行位图拉伸，确保获取到的屏幕坐标是真正的物理像素点。
    """
    try:
        # Windows 10 1703 以上推荐策略: Per-Monitor V2
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            # 旧版 Windows 回退策略
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def get_virtual_screen_geometry() -> Tuple[int, int, int, int]:
    """
    【获取跨多显示器的虚拟桌面坐标与尺寸】
    返回值: (x, y, width, height)
    例如双显示器横向并排时，x 可能是 0，width 可能是 1920 + 2560 = 4480。
    """
    x = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
    y = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
    w = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    h = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    return x, y, w, h


def make_window_click_through(hwnd: int):
    """
    【核心：为 Windows 窗口注入鼠标完全穿透属性】
    :param hwnd: 目标顶层窗口句柄 (HWND)
    """
    # 获取已有样式
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    
    # 扩展标志位定义
    WS_EX_LAYERED = win32con.WS_EX_LAYERED        # 支持透明度与通道
    WS_EX_TRANSPARENT = win32con.WS_EX_TRANSPARENT  # 鼠标碰撞检测穿透
    WS_EX_NOACTIVATE = 0x08000000                 # 不抢占前台输入焦点
    
    target_style = ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, target_style)
