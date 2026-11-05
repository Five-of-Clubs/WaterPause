"""
==============================================================================
模块名称: main.py (主应用程序入口)
作    者: VibeCoder
创建时间: 2026-11-05
项目描述:
    轻量级桌面防久坐与饮水提醒工具 (Break & Hydration Reminder)
    
软件工程架构说明:
    本应用遵循现代桌面客户端分层架构 (Layered Architecture):
    1. 【core/ 核心业务层】:
       - ConfigManager: 负责配置读取、校验、观察者广播与 JSON 落盘。
       - BreakStateMachine: 状态机引擎，管理 WORKING / PRE_BREAK / BREAKING / PAUSED 四大状态。
    2. 【os_layer/ 系统集成层】:
       - win_api: 封装高 DPI 感知、多显示器虚拟桌面计算与 Windows 鼠标完全穿透 (WS_EX_TRANSPARENT)。
       - idle_detector: 基于 GetLastInputInfo 的键鼠闲置超时智能归位。
       - session_listener: 全屏演示/视频应用检测与智能顺延。
       - hotkey_manager: 操作系统级全局快捷键生命周期管理。
    3. 【ui/ 视觉呈现层】:
       - BreakOverlayWindow: 全屏半透明、高对比度居中倒计时与关怀语录穿透蒙版。
       - PreBreakToast: 休息前 30 秒右下角无焦点预告卡片。
       - SettingsDialog: 完整的图形化偏好设置面板（时长/不透明度/颜色/语录自由定制）。
       - TrayIconManager: 系统托盘区常驻图标与悬停倒计时。
==============================================================================
"""

import sys
import tkinter as tk
from typing import Optional

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

        # 2. 创建 Tkinter 隐形根窗口（静默常驻，不在任务栏显示图标）
        self.root = tk.Tk()
        self.root.withdraw()

        # 3. 初始化配置管理器（自动从本地 config.json 读取）
        self.config = ConfigManager("config.json")

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

        # 8. 建立核心层与 UI 层的事件回调管道（观察者模式）
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
        用户在偏好设置面板修改保存后，热重载配置
        """
        print("[App] 检测到配置热更新，正在应用新参数...")
        self._bind_hotkey()

    def _handle_state_change(self, old_state: AppStatus, new_state: AppStatus):
        """
        【状态机响应路由】：当状态发生跃迁时，协调不同窗口的显隐
        """
        if new_state == AppStatus.WORKING:
            # 进入工作态：隐藏蒙版与预告卡片
            self.overlay.hide()
            self.toast.hide()

        elif new_state == AppStatus.PRE_BREAK:
            # 进入最后预告态：在右下角弹出克制的小提醒
            pre_break_sec = self.config.get("pre_break_seconds", 30)
            self.toast.show(pre_break_sec)

        elif new_state == AppStatus.BREAKING:
            # 进入休息态：收起预告卡片，平滑铺开全屏半透明鼠标穿透蒙版
            self.toast.hide()
            self.overlay.show()

        elif new_state == AppStatus.PAUSED:
            # 暂停态：收起所有提醒窗口
            self.overlay.hide()
            self.toast.hide()

    def _handle_tick(self, remaining_seconds: int, state: AppStatus):
        """
        【每秒心跳刷新】：更新托盘气泡与正在显示的窗口倒计时
        """
        mins = remaining_seconds // 60
        secs = remaining_seconds % 60
        time_str = f"{mins:02d}:{secs:02d}"

        # 1. 动态更新托盘鼠标悬停文字
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
        驱动状态机心跳：利用 Tkinter 事件循环，精准每 1000 毫秒脉冲一次，不占额外 CPU 资源
        """
        self.state_machine.tick()
        self.root.after(1000, self._schedule_tick)

    def run(self):
        """
        启动应用：启动托盘并进入操作系统主消息循环
        """
        print("==================================================")
        print(">>> 轻量级防久坐与饮水提醒工具已启动！")
        print(">>> 托盘图标已就绪，正在后台静默计时...")
        print(">>> 点击右键托盘图标可打开【偏好设置】定制不透明度与时长")
        print("==================================================")
        self.tray.start()
        self.root.mainloop()

    def exit_app(self):
        """
        安全释放所有系统资源并彻底退出
        """
        print("[App] 正在安全释放系统钩子与托盘图标...")
        self.hotkey_manager.unregister()
        self.overlay.hide()
        self.toast.hide()
        self.tray.stop()
        self.root.destroy()
        sys.exit(0)


if __name__ == "__main__":
    app = BreakReminderApplication()
    app.run()
