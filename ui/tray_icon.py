"""
==============================================================================
模块名称: ui/tray_icon.py
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    本模块实现 Windows 系统托盘区图标常驻与交互菜单。
    
设计原则:
    1. 【极低资源占用】: 
       使用 pystray (纯 Win32 原生 Shell_NotifyIcon 封装) + 自定义专属高清图标，
       无需常驻庞大的图形引擎。
    2. 【线程安全交互 (Thread-Safe Dispatch)】:
       托盘菜单点击事件在独立线程触发，通过 root.after(0, ...) 调度到 Tkinter 主线程执行，
       严格遵循现代 GUI 开发的线程隔离范式。
==============================================================================
"""

import os
import threading
import tkinter as tk
from typing import Callable, Optional
from PIL import Image
import pystray
from pystray import MenuItem as item, Menu


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

    def _load_tray_image(self) -> Image.Image:
        """
        加载应用专属的高清小水滴与时钟托盘图标（兼容 PyInstaller 冻结打包）
        """
        import sys
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        icon_path = os.path.join(base_dir, "app_icon.png")
        if os.path.exists(icon_path):
            try:
                return Image.open(icon_path)
            except Exception:
                pass
        # 降级备用
        return Image.new("RGBA", (64, 64), (137, 180, 250, 255))

    def start(self):
        """
        在后台启动托盘图标（异步守护运行）
        """
        image = self._load_tray_image()
        
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
            title="防久坐与饮水提醒 | 正在后台静默守护中...",
            menu=menu
        )

        self._is_running = True
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
