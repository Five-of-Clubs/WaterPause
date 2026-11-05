"""
==============================================================================
模块名称: ui/overlay_window.py
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    本模块实现全屏半透明、背景与文字透明度解绑的休息提醒蒙版。
    
双层协同架构原理 (Two-Layer Coordinated Overlay):
    1. 【底层背景幕布 (Backdrop Layer)】:
       - 负责全屏暗色遮罩或用户自定义背景图。
       - 独立绑定 overlay_opacity (例如 35%)，不影响前景文字。
       - 注入 WS_EX_TRANSPARENT 鼠标穿透样式。
    2. 【顶层文字视显 (HUD Foreground Layer)】:
       - 利用 Windows 颜色剔除机制 (-transparentcolor)，让窗体背景 100% 透明。
       - 倒计时大字与关怀语录保持 100% 纯正不透明（或通过 text_opacity 自定义）。
       - 彻底解决“蒙版透明度调低后文字发虚看不清”的痛点！
       - 同样注入 WS_EX_TRANSPARENT 鼠标完全穿透。
==============================================================================
"""

import os
import random
import tkinter as tk
from typing import Optional
from PIL import Image, ImageTk

from core.config_manager import ConfigManager
from os_layer.win_api import enable_dpi_awareness, get_virtual_screen_geometry, make_window_click_through

# 用于顶层 HUD 窗口背景透明色键（Chroma Key）的特殊保留色
CHROMA_KEY = "#010203"


class BreakOverlayWindow:
    """
    双层协同全屏穿透休息蒙版管理器
    """
    def __init__(self, root: tk.Tk, config_manager: ConfigManager):
        self.root = root
        self.config = config_manager
        
        # 底层背景窗口与顶层文字窗口
        self.bg_window: Optional[tk.Toplevel] = None
        self.fg_window: Optional[tk.Toplevel] = None
        
        self.time_label: Optional[tk.Label] = None
        self.quote_label: Optional[tk.Label] = None
        self.tip_label: Optional[tk.Label] = None
        
        # 缓存背景图 PhotoImage，避免被 Python 垃圾回收
        self._bg_photo: Optional[ImageTk.PhotoImage] = None

    def show(self):
        """
        创建并展示双层协同蒙版
        """
        if self.bg_window is not None or self.fg_window is not None:
            return  # 避免重复创建

        enable_dpi_awareness()
        vx, vy, vw, vh = get_virtual_screen_geometry()

        # ==========================================
        # 1. 构建底层背景幕布 (Backdrop Window)
        # ==========================================
        self.bg_window = tk.Toplevel(self.root)
        self.bg_window.title("BreakOverlay_Backdrop")
        self.bg_window.overrideredirect(True)
        self.bg_window.attributes("-topmost", True)
        
        # 读取背景不透明度 (默认 0.35)
        bg_opacity = float(self.config.get("overlay_opacity", 0.35))
        self.bg_window.attributes("-alpha", bg_opacity)
        self.bg_window.geometry(f"{vw}x{vh}+{vx}+{vy}")

        bg_color = self.config.get("overlay_bg_color", "#181825")
        self.bg_window.configure(bg=bg_color)

        # 检查是否配置了自定义背景图
        bg_img_path = self.config.get("bg_image_path", "").strip()
        if bg_img_path and os.path.exists(bg_img_path):
            try:
                pil_img = Image.open(bg_img_path)
                pil_img = pil_img.resize((vw, vh), Image.Resampling.LANCZOS)
                self._bg_photo = ImageTk.PhotoImage(pil_img)
                lbl_img = tk.Label(self.bg_window, image=self._bg_photo, bg=bg_color)
                lbl_img.place(x=0, y=0, width=vw, height=vh)
            except Exception as e:
                print(f"[BreakOverlayWindow] 加载自定义背景图失败: {e}")

        # 注入背景层鼠标穿透
        self.bg_window.update_idletasks()
        try:
            hwnd_bg = int(self.bg_window.wm_frame(), 16)
            make_window_click_through(hwnd_bg)
        except Exception as e:
            print(f"[BreakOverlayWindow] 注入背景层穿透失败: {e}")

        # ==========================================
        # 2. 构建顶层前景文字 HUD (Foreground Window)
        # ==========================================
        self.fg_window = tk.Toplevel(self.root)
        self.fg_window.title("BreakOverlay_Foreground")
        self.fg_window.overrideredirect(True)
        self.fg_window.attributes("-topmost", True)
        
        # 读取文字层独立不透明度 (默认 1.0，即 100% 纯正清晰)
        text_alpha = float(self.config.get("text_opacity", 1.0))
        self.fg_window.attributes("-alpha", text_alpha)
        
        # 开启色键剔除：窗口中所有 CHROMA_KEY 颜色的像素都会变成绝对透明
        self.fg_window.configure(bg=CHROMA_KEY)
        self.fg_window.attributes("-transparentcolor", CHROMA_KEY)
        self.fg_window.geometry(f"{vw}x{vh}+{vx}+{vy}")

        # 构建居中内容卡片容器
        card_bg = self.config.get("card_bg_color", "").strip()
        actual_card_bg = card_bg if card_bg else CHROMA_KEY
        border_width = int(self.config.get("card_border_width", 0))
        border_color = self.config.get("card_border_color", "#89b4fa")

        container = tk.Frame(
            self.fg_window,
            bg=actual_card_bg,
            highlightbackground=border_color if border_width > 0 else actual_card_bg,
            highlightthickness=border_width,
            padx=35,
            pady=25
        )
        container.place(relx=0.5, rely=0.45, anchor="center")

        # 2.1 倒计时大字（支持字体、字号、颜色自定义）
        t_font = self.config.get("timer_font_family", "Segoe UI")
        t_size = int(self.config.get("timer_font_size", 68))
        t_color = self.config.get("timer_font_color", "#ffffff")

        self.time_label = tk.Label(
            container,
            text="00:00",
            font=(t_font, t_size, "bold"),
            fg=t_color,
            bg=actual_card_bg
        )
        self.time_label.pack(pady=(0, 15))

        # 2.2 关怀提醒语录（支持字体、字号、颜色自定义）
        q_font = self.config.get("quote_font_family", "Microsoft YaHei UI")
        q_size = int(self.config.get("quote_font_size", 18))
        q_color = self.config.get("quote_font_color", "#cdd6f4")
        quotes = self.config.get("quotes", ["站起来活动一下，喝杯温水吧。"])
        current_quote = random.choice(quotes) if quotes else "去喝杯水，放松一下吧。"

        self.quote_label = tk.Label(
            container,
            text=current_quote,
            font=(q_font, q_size),
            fg=q_color,
            bg=actual_card_bg
        )
        self.quote_label.pack(pady=(0, 20))

        # 2.3 快捷键跳过提示
        hotkey = self.config.get("emergency_hotkey", "ctrl+shift+space").upper()
        self.tip_label = tk.Label(
            container,
            text=f"[ 鼠标操作已完全穿透，可正常操作下方软件 | 紧急跳过请按快捷键：{hotkey} ]",
            font=("Microsoft YaHei UI", 11),
            fg="#a6adc8",
            bg=actual_card_bg
        )
        self.tip_label.pack()

        # 注入文字层鼠标穿透
        self.fg_window.update_idletasks()
        try:
            hwnd_fg = int(self.fg_window.wm_frame(), 16)
            make_window_click_through(hwnd_fg)
        except Exception as e:
            print(f"[BreakOverlayWindow] 注入前景层穿透失败: {e}")

    def update_countdown(self, remaining_seconds: int):
        """
        实时更新蒙版上的倒计时
        """
        if self.time_label and self.fg_window:
            minutes = remaining_seconds // 60
            seconds = remaining_seconds % 60
            self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")

    def hide(self):
        """
        同时隐藏/销毁双层蒙版窗口
        """
        if self.fg_window is not None:
            try:
                self.fg_window.destroy()
            except Exception:
                pass
            self.fg_window = None

        if self.bg_window is not None:
            try:
                self.bg_window.destroy()
            except Exception:
                pass
            self.bg_window = None

        self.time_label = None
        self.quote_label = None
        self.tip_label = None
        self._bg_photo = None

    def is_visible(self) -> bool:
        """
        判断蒙版是否处于显示中
        """
        return self.bg_window is not None or self.fg_window is not None
