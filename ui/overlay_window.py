"""
==============================================================================
模块名称: ui/overlay_window.py
作    者: VibeCoder
创建时间: 2026-11-05
更新说明:
    【重大架构升级 - 双图层技术 (Dual-Layer Architecture)】:
    1. 【背景图层 (Layer 1)】: 全屏覆盖，支持用户调节的不透明度 (如 35%)，
       可显示深色纯色遮罩，也可加载用户自定义的高清壁纸背景图。
    2. 【文字前景图层 (Layer 2)】: 采用 Windows 原生透明色键控 (-transparentcolor)，
       文字保持 100% 绝对不透明与高亮清晰，即使在低透明度下也绝不发灰发暗。
    3. 【双层联动穿透】: 两个图层均注入 WS_EX_TRANSPARENT 与 WS_EX_NOACTIVATE，
       鼠标操作 100% 完全穿透，不抢占底层软件输入焦点。
==============================================================================
"""

import os
import random
import tkinter as tk
from typing import Optional
from PIL import Image, ImageTk

from core.config_manager import ConfigManager
from os_layer.win_api import enable_dpi_awareness, get_virtual_screen_geometry, make_window_click_through


class BreakOverlayWindow:
    """
    双图层休息提醒蒙版管理器
    """
    # 调色板色键：此颜色的像素会被 Windows 硬件渲染为 100% 透光
    CHROMA_KEY_COLOR = "#000001"

    def __init__(self, root: tk.Tk, config_manager: ConfigManager):
        self.root = root
        self.config = config_manager
        
        # 图层 1: 半透明背景层 (纯色或自定义壁纸)
        self.bg_window: Optional[tk.Toplevel] = None
        # 图层 2: 100% 不透明前景文字层
        self.text_window: Optional[tk.Toplevel] = None

        self.time_label: Optional[tk.Label] = None
        self.quote_label: Optional[tk.Label] = None
        self.tip_label: Optional[tk.Label] = None
        
        # 缓存壁纸对象，防止被 Python 垃圾回收
        self._bg_photo: Optional[ImageTk.PhotoImage] = None

    def show(self):
        """
        弹出双图层休息提醒窗口
        """
        if self.is_visible():
            return

        enable_dpi_awareness()
        x, y, w, h = get_virtual_screen_geometry()

        # 读取用户配置
        opacity = float(self.config.get("overlay_opacity", 0.35))
        bg_color = self.config.get("overlay_bg_color", "#181825")
        text_color = self.config.get("overlay_text_color", "#ffffff")
        quote_color = self.config.get("overlay_quote_color", "#f5e0dc")
        bg_image_path = self.config.get("bg_image_path", "")
        font_family = self.config.get("font_family", "Microsoft YaHei UI")
        time_font_size = int(self.config.get("time_font_size", 76))
        quote_font_size = int(self.config.get("quote_font_size", 22))

        # ==========================================
        # 1. 构建图层 1：半透明背景遮罩层
        # ==========================================
        self.bg_window = tk.Toplevel(self.root)
        self.bg_window.title("BreakOverlay_Background")
        self.bg_window.overrideredirect(True)
        self.bg_window.attributes("-topmost", True)
        self.bg_window.attributes("-alpha", opacity)
        self.bg_window.geometry(f"{w}x{h}+{x}+{y}")
        self.bg_window.configure(bg=bg_color)

        # 如果用户配置了自定义背景图片且文件有效
        if bg_image_path and os.path.exists(bg_image_path):
            try:
                pil_img = Image.open(bg_image_path).convert("RGBA")
                pil_img = pil_img.resize((w, h), Image.Resampling.LANCZOS)
                self._bg_photo = ImageTk.PhotoImage(pil_img)
                lbl_bg = tk.Label(self.bg_window, image=self._bg_photo, bg=bg_color)
                lbl_bg.place(x=0, y=0, width=w, height=h)
            except Exception as e:
                print(f"[BreakOverlayWindow] 加载自定义背景图失败: {e}")

        # ==========================================
        # 2. 构建图层 2：100% 不透明前景文字层
        # ==========================================
        self.text_window = tk.Toplevel(self.root)
        self.text_window.title("BreakOverlay_Foreground")
        self.text_window.overrideredirect(True)
        self.text_window.attributes("-topmost", True)
        self.text_window.attributes("-alpha", 1.0)  # 文字保持 100% 鲜明实色
        self.text_window.geometry(f"{w}x{h}+{x}+{y}")
        
        # 设置色键透明通道：窗体底色透光，但字形完全不透明
        self.text_window.configure(bg=self.CHROMA_KEY_COLOR)
        self.text_window.attributes("-transparentcolor", self.CHROMA_KEY_COLOR)

        # 内容容器置于屏幕居中偏上位置
        container = tk.Frame(self.text_window, bg=self.CHROMA_KEY_COLOR)
        container.place(relx=0.5, rely=0.45, anchor="center")

        # 2.1 倒计时大字
        self.time_label = tk.Label(
            container,
            text="00:00",
            font=(font_family, time_font_size, "bold"),
            fg=text_color,
            bg=self.CHROMA_KEY_COLOR
        )
        self.time_label.pack(pady=(0, 15))

        # 2.2 关怀语录
        quotes = self.config.get("quotes", ["站起来活动一下，喝杯温水吧。"])
        current_quote = random.choice(quotes) if quotes else "去喝杯水，放松一下吧。"
        self.quote_label = tk.Label(
            container,
            text=current_quote,
            font=(font_family, quote_font_size),
            fg=quote_color,
            bg=self.CHROMA_KEY_COLOR
        )
        self.quote_label.pack(pady=(0, 25))

        # 2.3 快捷键提示
        hotkey = self.config.get("emergency_hotkey", "ctrl+shift+space").upper()
        self.tip_label = tk.Label(
            container,
            text=f"[ 鼠标已完全穿透，可正常操作下方软件 | 紧急跳过请按快捷键：{hotkey} ]",
            font=(font_family, 11),
            fg="#a6adc8",
            bg=self.CHROMA_KEY_COLOR
        )
        self.tip_label.pack()

        # ==========================================
        # 3. 注入 Windows 原生鼠标穿透与防抢焦点属性
        # ==========================================
        self.bg_window.update_idletasks()
        self.text_window.update_idletasks()
        try:
            hwnd_bg = int(self.bg_window.wm_frame(), 16)
            make_window_click_through(hwnd_bg)
            
            hwnd_text = int(self.text_window.wm_frame(), 16)
            make_window_click_through(hwnd_text)
        except Exception as e:
            print(f"[BreakOverlayWindow] 注入穿透样式异常: {e}")

    def update_countdown(self, remaining_seconds: int):
        """
        实时更新倒计时文字
        """
        if self.time_label and self.text_window:
            minutes = remaining_seconds // 60
            seconds = remaining_seconds % 60
            self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")

    def hide(self):
        """
        销毁隐藏双图层
        """
        if self.bg_window is not None:
            try:
                self.bg_window.destroy()
            except Exception:
                pass
            self.bg_window = None

        if self.text_window is not None:
            try:
                self.text_window.destroy()
            except Exception:
                pass
            self.text_window = None
            self.time_label = None
            self.quote_label = None
            self.tip_label = None
            self._bg_photo = None

    def is_visible(self) -> bool:
        """
        判断当前是否处于显示状态
        """
        return self.bg_window is not None or self.text_window is not None
