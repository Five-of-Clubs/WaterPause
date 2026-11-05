"""
==============================================================================
模块名称: os_layer/session_listener.py
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    本模块负责感知系统环境：
    1. 检测当前是否有独占全屏应用程序（如全屏 PPT 放映、全屏看课视频、全屏游戏）。
    2. 如果当前有全屏软件，防久坐工具应智能暂缓弹出蒙版，避免惊扰演示或游戏。
==============================================================================
"""

import win32gui
import win32api
import win32con


def is_foreground_window_fullscreen() -> bool:
    """
    【检测当前激活的窗口是否处于全屏状态】
    逻辑步骤:
        1. 获取当前具有焦点的最前台窗口句柄。
        2. 排除 Windows 桌面 (Desktop) 与 任务栏 (Shell_TrayWnd)。
        3. 获取该窗口所在显示器的几何尺寸。
        4. 如果窗口的矩形区域完全覆盖了该屏幕，说明用户正在进行全屏操作。
    """
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd or not win32gui.IsWindow(hwnd):
            return False

        # 排除桌面和外壳程序
        desktop_hwnd = win32gui.GetDesktopWindow()
        shell_hwnd = win32gui.GetShellWindow()
        if hwnd in (desktop_hwnd, shell_hwnd):
            return False

        # 排除 Windows 任务栏自身
        class_name = win32gui.GetClassName(hwnd)
        if class_name in ("Shell_TrayWnd", "Progman", "WorkerW"):
            return False

        # 获取窗口矩形 (left, top, right, bottom)
        win_rect = win32gui.GetWindowRect(hwnd)
        win_w = win_rect[2] - win_rect[0]
        win_h = win_rect[3] - win_rect[1]

        # 获取当前窗口所在的显示器信息
        monitor_handle = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
        monitor_info = win32api.GetMonitorInfo(monitor_handle)
        mon_rect = monitor_info["Monitor"]
        mon_w = mon_rect[2] - mon_rect[0]
        mon_h = mon_rect[3] - mon_rect[1]

        # 如果前台窗口的尺寸大于等于当前屏幕尺寸，判定为全屏运行
        if win_w >= mon_w and win_h >= mon_h and win_rect[0] <= mon_rect[0] and win_rect[1] <= mon_rect[1]:
            return True

        return False
    except Exception:
        # 防御性容错，遇到任何异常不让主程序崩溃
        return False
