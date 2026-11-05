"""
==============================================================================
模块名称: ui/overlay_window.py
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    本模块实现全屏半透明、鼠标完全穿透的休息提醒蒙版窗口。
    
设计范式与原则:
    1. 【样式与逻辑完全数据驱动】:
       蒙版的不透明度、背景色、文字颜色、提醒文案均直接从 ConfigManager 动态读取，
       用户在设置面板修改后可即时生效。
    2. 【鼠标事件完全穿透 (Click-Through)】:
       封装了 OS 层的 WS_EX_TRANSPARENT 机制，任何鼠标硬件交互均穿透至底层。
    3. 【平滑无感呈现】:
       居中大字显示倒计时，底部提供清晰的快捷键说明。
==============================================================================
"""

import random
import tkinter as tk
from typing import Optional
from core.config_manager import ConfigManager
from os_layer.win_api import enable_dpi_awareness, get_virtual_screen_geometry, make_window_click_through


class BreakOverlayWindow:
    """
    全屏穿透休息蒙版管理器
    """
    def __init__(self, root: tk.Tk, config_manager: ConfigManager):
        self.root = root
        self.config = config_manager
        
        # 顶层子窗口引用（初始为 None，进入休息态时创建）
        self.window: Optional[tk.Toplevel] = None
        self.time_label: Optional[tk.Label] = None
        self.quote_label: Optional[tk.Label] = None
        self.tip_label: Optional[tk.Label] = None

    def show(self):
        """
        创建并弹出全屏半透明穿透蒙版
        """
        if self.window is not None:
            return  # 已经处于显示状态，避免重复创建

        enable_dpi_awareness()
        
        # 创建 Toplevel 独立置顶层
        self.window = tk.Toplevel(self.root)
        self.window.title("BreakOverlay")
        
        # 1. 移除操作系统原生标题栏与窗口边框
        self.window.overrideredirect(True)
        # 2. 窗口强制绝对置顶
        self.window.attributes("-topmost", True)
        
        # 3. 从配置中读取用户自定义不透明度 (默认 0.35)
        opacity = float(self.config.get("overlay_opacity", 0.35))
        self.window.attributes("-alpha", opacity)

        # 4. 虚拟多显示器无缝铺满
        x, y, w, h = get_virtual_screen_geometry()
        self.window.geometry(f"{w}x{h}+{x}+{y}")

        # 5. 读取用户配置的配色方案
        bg_color = self.config.get("overlay_bg_color", "#181825")
        text_color = self.config.get("overlay_text_color", "#cdd6f4")
        quote_color = self.config.get("overlay_quote_color", "#bac2de")
        self.window.configure(bg=bg_color)

        # 6. 构建居中内容容器
        container = tk.Frame(self.window, bg=bg_color)
        container.place(relx=0.5, rely=0.45, anchor="center")

        # 6.1 倒计时大字
        self.time_label = tk.Label(
            container,
            text="00:00",
            font=("Segoe UI", 68, "bold"),
            fg=text_color,
            bg=bg_color
        )
        self.time_label.pack(pady=(0, 15))

        # 6.2 随机抽取一条温暖的关怀提醒语录
        quotes = self.config.get("quotes", ["站起来活动一下，喝杯温水吧。"])
        current_quote = random.choice(quotes) if quotes else "去喝杯水，放松一下吧。"
        self.quote_label = tk.Label(
            container,
            text=current_quote,
            font=("Microsoft YaHei UI", 18),
            fg=quote_color,
            bg=bg_color
        )
        self.quote_label.pack(pady=(0, 25))

        # 6.3 底部紧急跳过快捷键提示
        hotkey = self.config.get("emergency_hotkey", "ctrl+shift+space").upper()
        self.tip_label = tk.Label(
            container,
            text=f"[ 鼠标操作已完全穿透，可正常操作下方软件 | 紧急跳过请按快捷键：{hotkey} ]",
            font=("Microsoft YaHei UI", 11),
            fg="#a6adc8",
            bg=bg_color
        )
        self.tip_label.pack()

        # 7. 刷新窗口并注入 Windows 原生鼠标穿透样式
        self.window.update_idletasks()
        try:
            hwnd = int(self.window.wm_frame(), 16)
            make_window_click_through(hwnd)
        except Exception as e:
            print(f"[BreakOverlayWindow] 注入穿透样式异常: {e}")

    def update_countdown(self, remaining_seconds: int):
        """
        更新蒙版上的剩余倒计时显示
        """
        if self.time_label and self.window:
            minutes = remaining_seconds // 60
            seconds = remaining_seconds % 60
            self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")

    def hide(self):
        """
        销毁并隐藏休息蒙版
        """
        if self.window is not None:
            try:
                self.window.destroy()
            except Exception:
                pass
            self.window = None
            self.time_label = None
            self.quote_label = None
            self.tip_label = None

    def is_visible(self) -> bool:
        """
        判断蒙版当前是否正在显示
        """
        return self.window is not None
