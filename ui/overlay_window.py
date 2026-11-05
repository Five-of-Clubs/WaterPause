"""
==============================================================================
模块名称: ui/overlay_window.py
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    本模块实现全屏半透明、背景与文字透明度解绑的休息提醒蒙版。
    
双层协同架构原理 (Two-Layer Coordinated Overlay):
    1. 【底层背景幕布 (Backdrop Layer)】:
       - 负责全屏暗色遮罩或用户自定义背景图（保持原图比例居中填充裁剪 Cover/Fill）。
       - 独立绑定 overlay_opacity (例如 35%)，不影响前景文字。
       - 注入 WS_EX_TRANSPARENT 鼠标穿透样式。
    2. 【顶层文字视显 (HUD Foreground Layer)】:
       - 利用 Windows 颜色剔除机制 (-transparentcolor)，让窗体背景 100% 透明。
       - 倒计时大字与关怀语录保持 100% 纯正不透明（或通过 text_opacity 自定义）。
       - 彻底解决“蒙版透明度调低后文字发虚看不清”的痛点！
       - 同样注入 WS_EX_TRANSPARENT 鼠标完全穿透。
    3. 【无损预览模式 (Preview Mode)】:
       - 支持传入草稿配置实时预览，不扰动后台正式专注工作倒计时。
       - 按 ESC、快捷键或 8 秒后自动安全退出预览。
==============================================================================
"""

import os
import random
import tkinter as tk
from typing import Optional, Dict, Any
from PIL import Image, ImageTk, ImageOps
import keyboard

from core.config_manager import ConfigManager, sanitize_color
from os_layer.win_api import enable_dpi_awareness, get_virtual_screen_geometry, make_window_click_through
from os_layer.font_manager import load_font_resource

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
        
        # 预览模式状态
        self.is_preview_mode = False
        self._preview_timer_id: Optional[str] = None

    def show(self, override_config: Optional[Dict[str, Any]] = None, is_preview: bool = False):
        """
        创建并展示双层协同蒙版
        :param override_config: 临时覆盖配置（用于预览草稿效果）
        :param is_preview: 是否为免打扰预览模式
        """
        if self.bg_window is not None or self.fg_window is not None:
            self.hide()  # 如果已有旧窗口，先安全关闭再展示新配置

        enable_dpi_awareness()
        vx, vy, vw, vh = get_virtual_screen_geometry()
        self.is_preview_mode = is_preview

        # 统一配置获取工具函数
        def get_val(key: str, default: Any = None) -> Any:
            if override_config is not None and key in override_config:
                return override_config[key]
            return self.config.get(key, default)

        try:
            # ==========================================
            # 1. 构建底层背景幕布 (Backdrop Window)
            # ==========================================
            self.bg_window = tk.Toplevel(self.root)
            self.bg_window.title("BreakOverlay_Backdrop")
            self.bg_window.overrideredirect(True)
            self.bg_window.attributes("-topmost", True)
            
            # 读取背景不透明度 (默认 0.60)
            bg_opacity = float(get_val("overlay_opacity", 0.60))
            self.bg_window.attributes("-alpha", bg_opacity)
            self.bg_window.geometry(f"{vw}x{vh}+{vx}+{vy}")

            # 防呆清洗背景底色：若用户输入 '003153' 或乱填，自动清洗为 '#003153'，绝不崩溃
            raw_bg = get_val("overlay_bg_color", "#003153")
            bg_color = sanitize_color(raw_bg, fallback="#003153")
            try:
                self.bg_window.configure(bg=bg_color)
            except Exception as e:
                print(f"[BreakOverlayWindow] 配置背景底色异常，平滑回退安全色: {e}")
                bg_color = "#003153"
                self.bg_window.configure(bg=bg_color)

            # 检查是否配置了自定义背景图
            bg_img_path = str(get_val("bg_image_path", "")).strip()
            if bg_img_path and os.path.exists(bg_img_path):
                try:
                    pil_img = Image.open(bg_img_path)
                    # 等比例居中填充裁剪 (Cover/Fill)，保证任何比例图片绝不变形
                    fitted_img = ImageOps.fit(
                        pil_img, (vw, vh),
                        method=Image.Resampling.LANCZOS,
                        centering=(0.5, 0.5)
                    )
                    self._bg_photo = ImageTk.PhotoImage(fitted_img)
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
            
            # 读取文字层独立不透明度 (默认 1.0)
            text_alpha = float(get_val("text_opacity", 1.0))
            self.fg_window.attributes("-alpha", text_alpha)
            
            self.fg_window.configure(bg=CHROMA_KEY)
            self.fg_window.attributes("-transparentcolor", CHROMA_KEY)
            self.fg_window.geometry(f"{vw}x{vh}+{vx}+{vy}")

            # 构建居中内容卡片容器
            card_bg = str(get_val("card_bg_color", "")).strip()
            actual_card_bg = sanitize_color(card_bg, fallback=CHROMA_KEY) if card_bg else CHROMA_KEY
            border_width = int(get_val("card_border_width", 0))
            border_color = sanitize_color(get_val("card_border_color", "#89b4fa"), fallback="#89b4fa")

            try:
                container = tk.Frame(
                    self.fg_window,
                    bg=actual_card_bg,
                    highlightbackground=border_color if border_width > 0 else actual_card_bg,
                    highlightthickness=border_width,
                    padx=35,
                    pady=25
                )
                container.place(relx=0.5, rely=0.45, anchor="center")
            except Exception as e:
                print(f"[BreakOverlayWindow] 卡片边框配置异常，使用无边框透明卡片: {e}")
                container = tk.Frame(self.fg_window, bg=CHROMA_KEY, padx=35, pady=25)
                container.place(relx=0.5, rely=0.45, anchor="center")
                actual_card_bg = CHROMA_KEY

            # 2.1 倒计时大字（支持字体、字号、颜色、粗细自定义）
            custom_font = str(get_val("custom_font_path", "")).strip()
            if custom_font and os.path.exists(custom_font):
                load_font_resource(custom_font)

            t_font = str(get_val("timer_font_family", "Segoe UI"))
            t_size = int(get_val("timer_font_size", 68))
            t_color = sanitize_color(get_val("timer_font_color", "#ffffff"), fallback="#ffffff")
            t_bold = bool(get_val("timer_font_bold", True))
            t_weight = "bold" if t_bold else "normal"

            initial_time = "03:00" if is_preview else "00:00"
            try:
                self.time_label = tk.Label(
                    container,
                    text=initial_time,
                    font=(t_font, t_size, t_weight),
                    fg=t_color,
                    bg=actual_card_bg
                )
            except Exception as e:
                print(f"[BreakOverlayWindow] 倒计时字体异常，回退默认系统字体: {e}")
                self.time_label = tk.Label(
                    container,
                    text=initial_time,
                    font=("Segoe UI", 68, "bold"),
                    fg="#ffffff",
                    bg=actual_card_bg
                )
            self.time_label.pack(pady=(0, 15))

            # 2.2 关怀提醒语录（支持字体、字号、颜色、粗细自定义）
            q_font = str(get_val("quote_font_family", "Microsoft YaHei UI"))
            q_size = int(get_val("quote_font_size", 18))
            q_color = sanitize_color(get_val("quote_font_color", "#cdd6f4"), fallback="#cdd6f4")
            q_bold = bool(get_val("quote_font_bold", False))
            q_weight = "bold" if q_bold else "normal"

            quotes = get_val("quotes", ["站起来活动一下，喝杯温水吧。"])
            current_quote = random.choice(quotes) if quotes else "去喝杯水，放松一下吧。"

            try:
                self.quote_label = tk.Label(
                    container,
                    text=current_quote,
                    font=(q_font, q_size, q_weight),
                    fg=q_color,
                    bg=actual_card_bg
                )
            except Exception as e:
                print(f"[BreakOverlayWindow] 语录字体异常，回退默认系统字体: {e}")
                self.quote_label = tk.Label(
                    container,
                    text=current_quote,
                    font=("Microsoft YaHei UI", 18),
                    fg="#cdd6f4",
                    bg=actual_card_bg
                )
            self.quote_label.pack(pady=(0, 20))

            # 2.3 底部提示文案
            hotkey = str(get_val("emergency_hotkey", "ctrl+shift+space")).upper()
            if is_preview:
                tip_text = f"[ 👁 效果实时预览中 (8秒后自动退出) | 按 ESC 或 快捷键({hotkey}) 立即返回设置，不打乱正常计时 ]"
            else:
                tip_text = f"[ 鼠标操作已完全穿透，可正常操作下方软件 | 紧急跳过请按快捷键：{hotkey} ]"

            self.tip_label = tk.Label(
                container,
                text=tip_text,
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

            # 预览模式下的退出监听与自动退出定时器
            if is_preview:
                try:
                    keyboard.add_hotkey("esc", self.hide)
                except Exception:
                    pass
                # 8 秒后自动关闭预览
                self._preview_timer_id = self.root.after(8000, self.hide)
        except Exception as e:
            print(f"[BreakOverlayWindow] 展现全屏蒙版发生未预料异常，执行防呆兜底关闭: {e}")
            self.hide()

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
        隐藏/销毁双层蒙版窗口
        """
        if self.is_preview_mode:
            try:
                keyboard.remove_hotkey("esc")
            except Exception:
                pass
            if self._preview_timer_id:
                try:
                    self.root.after_cancel(self._preview_timer_id)
                except Exception:
                    pass
                self._preview_timer_id = None
            self.is_preview_mode = False

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
