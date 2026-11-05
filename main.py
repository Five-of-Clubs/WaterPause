"""
==============================================================================
模块名称: main.py (主应用程序入口)
作    者: VibeCoder
创建时间: 2026-11-05
更新说明:
    1. 【自动隐藏黑色控制台窗口】:
       当常规启动时，利用 Windows API (ShowWindow SW_HIDE) 瞬间静默隐藏控制台，
       彻底解决用户反馈的“黑框关不掉，一关主程序就退”的痛点。
       同时支持传入 --console 参数便于开发者调试打印。
    2. 【重设 Windows 任务栏 AppUserModelID】:
       调用 shell32.SetCurrentProcessExplicitAppUserModelID 剥离 Python 默认进程标识，
       让任务栏展示我们的专属应用图标，彻底告别 Python 蓝黄蛇形图标。
    3. 【双图层半透明穿透蒙版调度】:
       适配新的 BreakOverlayWindow，实现蒙版半透明但倒计时文字 100% 不透明鲜亮。
==============================================================================
"""

import os
import sys
import ctypes
import tkinter as tk
from typing import Optional

# ---------------------------------------------------------------------------
# 1. 彻底解决“弹出黑色 Python 对话框”的痛点
# ---------------------------------------------------------------------------
def hide_console_window_if_present():
    """
    【静默运行】：若以普通 python.exe 启动，Windows 会分配控制台窗口。
    此处调用 Windows 原生 API 将控制台窗口置入后台隐藏模式 (SW_HIDE)。
    若需要查看调试日志，可在命令行追加 --console 参数启动。
    """
    if "--console" not in sys.argv and "--debug" not in sys.argv:
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                # 0 代表 SW_HIDE (隐藏窗口)
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except Exception:
            pass

# 立即执行控制台隐藏
hide_console_window_if_present()

# ---------------------------------------------------------------------------
# 2. 彻底解决“任务栏显示 Python 默认蓝黄蛇图标”的痛点
# ---------------------------------------------------------------------------
def set_app_user_model_id():
    """
    【独立应用标识】：告诉 Windows 任务栏“我是独立的防久坐提醒软件，不要把我归类为 Python 解释器”，
    使得任务栏展示属于我们自己的高清图标。
    """
    try:
        myappid = "vibecoding.breakreminder.desktop.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

set_app_user_model_id()


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
    应用程序总控制器
    """
    def __init__(self):
        # 1. 启动高 DPI 自适应感知
        enable_dpi_awareness()

        # 2. 创建 Tkinter 根窗口（隐形后台根容器）
        self.root = tk.Tk()
        self.root.withdraw()

        # 设置应用程序图标（任务栏与子窗口通用）
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "app_icon.ico"))
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        # 3. 初始化配置管理器
        self.config = ConfigManager(os.path.abspath(os.path.join(os.path.dirname(__file__), "config.json")))

        # 4. 初始化核心业务状态机
        self.state_machine = BreakStateMachine(self.config)

        # 5. 初始化全局快捷键
        self.hotkey_manager = HotkeyManager()
        self._bind_hotkey()

        # 6. 初始化 UI 视图组件（包含双图层蒙版、预告卡片、全新选项卡设置面板）
        self.overlay = BreakOverlayWindow(self.root, self.config)
        self.toast = PreBreakToast(self.root)
        self.settings_dialog = SettingsDialog(self.root, self.config)

        # 7. 初始化系统托盘图标
        self.tray = TrayIconManager(
            root=self.root,
            on_trigger_break=self.state_machine.trigger_break_now,
            on_pause=self.state_machine.pause,
            on_resume=self.state_machine.resume,
            on_open_settings=self.settings_dialog.show,
            on_exit=self.exit_app
        )

        # 8. 建立事件总线连接
        self.state_machine.on_state_change = self._handle_state_change
        self.state_machine.on_tick = self._handle_tick
        self.config.add_listener(self._handle_config_changed)

        # 9. 启动定时心跳
        self._schedule_tick()

    def _bind_hotkey(self):
        hotkey_str = self.config.get("emergency_hotkey", "ctrl+shift+space")
        self.hotkey_manager.register(hotkey_str, self._on_hotkey_pressed)

    def _on_hotkey_pressed(self):
        self.root.after(0, self.state_machine.skip_break)

    def _handle_config_changed(self, new_config):
        self._bind_hotkey()

    def _handle_state_change(self, old_state: AppStatus, new_state: AppStatus):
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
        self.state_machine.tick()
        self.root.after(1000, self._schedule_tick)

    def run(self):
        self.tray.start()
        self.root.mainloop()

    def exit_app(self):
        self.hotkey_manager.unregister()
        self.overlay.hide()
        self.toast.hide()
        self.tray.stop()
        self.root.destroy()
        sys.exit(0)


if __name__ == "__main__":
    app = BreakReminderApplication()
    app.run()
