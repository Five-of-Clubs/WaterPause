"""
==============================================================================
模块名称: ui/toast_window.py
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    本模块实现休息前最后 30 秒的“右下角克制预告小弹窗 (Toast Notification)”。
    
设计原则:
    1. 【绝不抢夺焦点】: 窗口出现时绝不中断用户的键盘打字光标。
    2. 【克制与优雅】: 浮于屏幕右下角任务栏上方，呈现简短温和的收尾提示。
==============================================================================
"""

import tkinter as tk
from typing import Optional
import win32gui
import win32con
from os_layer.win_api import enable_dpi_awareness


class PreBreakToast:
    """
    休息前 30 秒角落预告小弹窗
    """
    def __init__(self, root: tk.Tk):
        self.root = root
        self.window: Optional[tk.Toplevel] = None
        self.countdown_label: Optional[tk.Label] = None

    def show(self, remaining_seconds: int = 30):
        """
        显示右下角预告小卡片
        """
        if self.window is not None:
            self.update_countdown(remaining_seconds)
            return

        enable_dpi_awareness()
        
        self.window = tk.Toplevel(self.root)
        self.window.title("PreBreakReminder")
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", 0.92)

        # 尺寸与位置计算（停靠在主屏幕右下角，避开任务栏）
        toast_w, toast_h = 320, 90
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = screen_w - toast_w - 20
        pos_y = screen_h - toast_h - 60
        self.window.geometry(f"{toast_w}x{toast_h}+{pos_x}+{pos_y}")

        # 配色与卡片布局
        bg_card = "#1e1e2e"
        self.window.configure(bg=bg_card)

        # 外边框线框与内边距
        frame = tk.Frame(self.window, bg=bg_card, highlightbackground="#313244", highlightthickness=1)
        frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 标题栏：小图标 + 提示标题
        title_box = tk.Frame(frame, bg=bg_card)
        title_box.pack(fill=tk.X, padx=12, pady=(10, 4))

        tk.Label(
            title_box,
            text="☕ 休息预告",
            font=("Microsoft YaHei UI", 11, "bold"),
            fg="#fab387",
            bg=bg_card
        ).pack(side=tk.LEFT)

        self.countdown_label = tk.Label(
            title_box,
            text=f"{remaining_seconds}s 后",
            font=("Segoe UI", 10, "bold"),
            fg="#a6adc8",
            bg=bg_card
        )
        self.countdown_label.pack(side=tk.RIGHT)

        # 正文描述
        tk.Label(
            frame,
            text="即将进入全屏放松与饮水时间，请保存当前工作并收尾思绪。",
            font=("Microsoft YaHei UI", 9),
            fg="#cdd6f4",
            bg=bg_card,
            wraplength=290,
            justify=tk.LEFT
        ).pack(padx=12, pady=(0, 8), anchor="w")

        # 避免抢焦点的底层样式注入
        self.window.update_idletasks()
        try:
            hwnd = int(self.window.wm_frame(), 16)
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style | 0x08000000)  # WS_EX_NOACTIVATE
        except Exception:
            pass

    def update_countdown(self, seconds: int):
        """
        实时更新预告弹窗上的倒数秒数
        """
        if self.countdown_label:
            self.countdown_label.config(text=f"{seconds}s 后")

    def hide(self):
        """
        关闭隐藏小卡片
        """
        if self.window is not None:
            try:
                self.window.destroy()
            except Exception:
                pass
            self.window = None
            self.countdown_label = None
