"""
==============================================================================
模块名称: ui/tray_icon.py
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    本模块实现 Windows 系统托盘区图标常驻与交互菜单。
    
设计原则:
    1. 【极低资源占用】: 
       使用 pystray (纯 Win32 原生 Shell_NotifyIcon 封装) + Pillow 动态生成图标，
       无需常驻庞大的图形引擎。
    2. 【线程安全交互 (Thread-Safe Dispatch)】:
       托盘菜单点击事件在独立线程触发，通过 root.after(0, ...) 调度到 Tkinter 主线程执行，
       严格遵循现代 GUI 开发的线程隔离范式。
==============================================================================
"""

import threading
import tkinter as tk
from typing import Callable, Optional
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item, Menu


def create_tray_image(color: str = "#89b4fa") -> Image.Image:
    """
    【动态生成托盘图标】
    在内存中动态绘制一个 64x64 的柔和时钟/防久坐水滴小图标
    """
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制外圈圆环
    draw.ellipse((6, 6, 58, 58), outline=color, width=5)
    
    # 绘制指针（表盘 3 点与 12 点方向，示意专注与休息）
    draw.line((32, 32, 32, 16), fill=color, width=4)
    draw.line((32, 32, 44, 32), fill=color, width=4)
    draw.ellipse((29, 29, 35, 35), fill=color)
    
    return img


class TrayIconManager:
    """
    系统托盘管理器
    """
    def __init__(
        self,
        root: tk.Tk,
        on_trigger_break: Callable[[], None],
        on_pause: Callable[[Optional[int]], None],
        on_resume: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_exit: Callable[[], None]
    ):
        self.root = root
        self.on_trigger_break = on_trigger_break
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_open_settings = on_open_settings
        self.on_exit = on_exit

        self._icon: Optional[pystray.Icon] = None
        self._is_running = False

    def start(self):
        """
        在后台启动托盘图标（异步守护运行）
        """
        image = create_tray_image()
        
        # 构建右键上下文菜单
        menu = Menu(
            item("☕ 立即进入休息", self._wrap(self.on_trigger_break), default=True),
            Menu.SEPARATOR,
            item("⏸ 暂停计时", Menu(
                item("暂停 30 分钟", self._wrap(lambda: self.on_pause(30 * 60))),
                item("暂停 1 小时", self._wrap(lambda: self.on_pause(60 * 60))),
                item("暂停至手动恢复", self._wrap(lambda: self.on_pause(None)))
            )),
            item("▶ 恢复计时", self._wrap(self.on_resume)),
            Menu.SEPARATOR,
            item("⚙ 偏好设置...", self._wrap(self.on_open_settings)),
            Menu.SEPARATOR,
            item("❌ 彻底退出", self._wrap(self.on_exit))
        )

        self._icon = pystray.Icon(
            name="BreakReminder",
            icon=image,
            title="防久坐与饮水提醒 | 初始化中...",
            menu=menu
        )

        self._is_running = True
        # 在独立后台线程运行托盘事件循环
        threading.Thread(target=self._icon.run, daemon=True).start()

    def update_tooltip(self, text: str):
        """
        更新鼠标悬停在托盘图标时的气泡提示文案
        """
        if self._icon and self._is_running:
            self._icon.title = f"防久坐与饮水提醒\n{text}"

    def stop(self):
        """
        退出并注销托盘图标
        """
        self._is_running = False
        if self._icon:
            self._icon.stop()
            self._icon = None

    def _wrap(self, action: Callable[[], None]):
        """
        【线程安全包装器】：将后台线程的菜单点击事件转发回 Tkinter 主线程执行
        """
        def handler(icon, item):
            self.root.after(0, action)
        return handler
