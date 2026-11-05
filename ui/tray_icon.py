"""
==============================================================================
模块名称: ui/tray_icon.py
作    者: VibeCoder
创建时间: 2026-11-05
更新说明:
    1. 【加载高清专属图标】: 优先加载 assets/app_icon.png，提供与任务栏一致的品牌视觉。
    2. 【线程安全菜单回调】: 依然严格使用 root.after(0, ...) 将菜单点击事件投递至主线程。
==============================================================================
"""

import os
import threading
import tkinter as tk
from typing import Callable, Optional
from PIL import Image
import pystray
from pystray import MenuItem as item, Menu


def load_app_tray_icon() -> Image.Image:
    """
    加载应用专属托盘图标，若文件缺失则在内存中绘制备用图标
    """
    icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "app_icon.png"))
    if os.path.exists(icon_path):
        try:
            return Image.open(icon_path)
        except Exception:
            pass
    # 备用方案
    return Image.new("RGBA", (64, 64), (137, 180, 250, 255))


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
        在后台守护线程中启动托盘图标
        """
        image = load_app_tray_icon()
        
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
            title="防久坐与饮水提醒 | 静默运行中",
            menu=menu
        )

        self._is_running = True
        threading.Thread(target=self._icon.run, daemon=True).start()

    def update_tooltip(self, text: str):
        """
        更新鼠标悬停提示
        """
        if self._icon and self._is_running:
            self._icon.title = f"防久坐与饮水提醒\n{text}"

    def stop(self):
        """
        退出托盘
        """
        self._is_running = False
        if self._icon:
            self._icon.stop()
            self._icon = None

    def _wrap(self, action: Callable[[], None]):
        """
        将托盘菜单的异步操作派发给 Tkinter 主线程
        """
        def handler(icon, item):
            self.root.after(0, action)
        return handler
