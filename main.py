"""
==============================================================================
模块名称: main.py (主应用程序入口)
作    者: VibeCoder
创建时间: 2026-11-05
项目描述:
    轻量级桌面防久坐与饮水提醒工具 (Break & Hydration Reminder)
==============================================================================
"""

import os
import sys
import ctypes
import tkinter as tk
from typing import Optional

# 核心 Windows 技巧：设置独立 AppUserModelID
# 告诉 Windows 任务栏这是一个独立应用程序，不要套用 Python 默认的小蟒蛇图标！
try:
    myappid = "antigravity.breakreminder.water.1.0"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# 将项目根目录加入模块搜索路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.config_manager import ConfigManager
from core.state_machine import BreakStateMachine, AppStatus
from os_layer.win_api import enable_dpi_awareness
from os_layer.hotkey_manager import HotkeyManager
from ui.overlay_window import BreakOverlayWindow
from ui.toast_window import PreBreakToast
from ui.settings_dialog import SettingsDialog
from ui.tray_icon import TrayIconManager


class BreakReminderApplication:
    """
    应用程序总控制器 (Application Coordinator)
    负责装配依赖、连接各层接口并驱动主事件循环
    """
    def __init__(self):
        # 1. 启动高 DPI 自适应感知，保障所有显示器画面清晰
        enable_dpi_awareness()

        # 2. 创建 Tkinter 根窗口（隐藏根窗口，静默运行于托盘区）
        self.root = tk.Tk()
        self.root.withdraw()

        # 绑定应用图标
        icon_path = os.path.join(PROJECT_ROOT, "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        # 3. 初始化配置管理器
        config_path = os.path.join(PROJECT_ROOT, "config.json")
        self.config = ConfigManager(config_path)

        # 4. 初始化核心业务状态机
        self.state_machine = BreakStateMachine(self.config)

        # 5. 初始化全局快捷键管理器
        self.hotkey_manager = HotkeyManager()
        self._bind_hotkey()

        # 6. 初始化 UI 视图组件
        self.overlay = BreakOverlayWindow(self.root, self.config)
        self.toast = PreBreakToast(self.root)
        self.settings_dialog = SettingsDialog(self.root, self.config)

        # 7. 初始化系统托盘图标管理器
        self.tray = TrayIconManager(
            root=self.root,
            on_trigger_break=self.state_machine.trigger_break_now,
            on_pause=self.state_machine.pause,
            on_resume=self.state_machine.resume,
            on_open_settings=self.settings_dialog.show,
            on_exit=self.exit_app
        )

        # 8. 建立核心层与 UI 层的事件回调管道
        self.state_machine.on_state_change = self._handle_state_change
        self.state_machine.on_tick = self._handle_tick
        self.config.add_listener(self._handle_config_changed)

        # 9. 启动每秒一次的事件脉冲定时器
        self._schedule_tick()

    def _bind_hotkey(self):
        """
        根据当前配置注册全局跳过快捷键
        """
        hotkey_str = self.config.get("emergency_hotkey", "ctrl+shift+space")
        self.hotkey_manager.register(hotkey_str, self._on_hotkey_pressed)

    def _on_hotkey_pressed(self):
        """
        当用户按下紧急跳过快捷键时触发（线程安全分发给主线程）
        """
        self.root.after(0, self.state_machine.skip_break)

    def _handle_config_changed(self, new_config):
        """
        配置热重载
        """
        self._bind_hotkey()

    def _handle_state_change(self, old_state: AppStatus, new_state: AppStatus):
        """
        【状态机响应路由】：当状态发生跃迁时，协调不同窗口的显隐
        """
        if new_state == AppStatus.WORKING:
            self.overlay.hide()
            self.toast.hide()

        elif new_state == AppStatus.PRE_BREAK:
            pre_break_sec = self.config.get("pre_break_seconds", 30)
            self.toast.show(pre_break_sec)

        elif new_state == AppStatus.BREAKING:
            self.toast.hide()
            self.overlay.show()

        elif new_state == AppStatus.PAUSED:
            self.overlay.hide()
            self.toast.hide()

    def _handle_tick(self, remaining_seconds: int, state: AppStatus):
        """
        【每秒心跳刷新】：更新托盘气泡与正在显示的窗口倒计时
        """
        mins = remaining_seconds // 60
        secs = remaining_seconds % 60
        time_str = f"{mins:02d}:{secs:02d}"

        if state == AppStatus.WORKING:
            self.tray.update_tooltip(f"距离下次休息还有：{time_str}")
        elif state == AppStatus.PRE_BREAK:
            self.tray.update_tooltip(f"即将休息 (预告中)：{time_str}")
            self.toast.update_countdown(remaining_seconds)
        elif state == AppStatus.BREAKING:
            self.tray.update_tooltip(f"正在休息中：{time_str}")
            self.overlay.update_countdown(remaining_seconds)
        elif state == AppStatus.PAUSED:
            self.tray.update_tooltip("计时器已暂停")

    def _schedule_tick(self):
        """
        驱动状态机心跳：精准每秒一次事件驱动
        """
        self.state_machine.tick()
        self.root.after(1000, self._schedule_tick)

    def run(self):
        """
        启动应用
        """
        self.tray.start()
        self.root.mainloop()

    def exit_app(self):
        """
        安全释放所有系统资源并彻底退出
        """
        self.hotkey_manager.unregister()
        self.overlay.hide()
        self.toast.hide()
        self.tray.stop()
        self.root.destroy()
        sys.exit(0)


if __name__ == "__main__":
    app = BreakReminderApplication()
    app.run()
