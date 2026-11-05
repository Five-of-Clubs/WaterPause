"""
==============================================================================
模块名称: ui/settings_dialog.py
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    本模块实现“偏好设置图形化配置面板 (Settings Dialog)”。
    
架构与体验重构亮点:
    1. 【底部操作栏永不被遮挡】:
       采用自底向上的布局管理（side=tk.BOTTOM 优先吸附），
       彻底解决“默认打开看不到保存和取消按钮”的排版缺陷。
    2. 【现代化分页选项卡 (ttk.Notebook)】:
       将设置清晰划分为 4 大分类：
       - ⏱ 时间节奏: 工作/休息/预告时长
       - 🎨 视觉与外观: 背景不透明度、文字不透明度、倒计时与语录字体/字号/粗细/选色、导入外部字体、背景图
       - 📝 关怀语录库: 列表增删
       - ⚙ 系统与高级: 开机自启、快捷键、闲置归位、全屏顺延、UI字号缩放
    3. 【Windows 原生应用图标绑定与全部系统字体枚举】:
       支持系统内 500+ 款字体自由挑选，并支持一键导入任意本地 .ttf / .otf 字体文件。
==============================================================================
"""

import os
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from typing import Optional, List, Callable

from core.config_manager import ConfigManager, DEFAULT_CONFIG
from os_layer.autostart import is_autostart_enabled, set_autostart
from os_layer.font_manager import get_available_fonts, load_font_resource, get_font_family_from_file


class SettingsDialog:
    """
    偏好设置现代化配置面板
    """
    def __init__(
        self,
        parent: tk.Tk,
        config_manager: ConfigManager,
        on_preview: Optional[Callable[[dict], None]] = None
    ):
        self.parent = parent
        self.config = config_manager
        self.on_preview = on_preview
        self.window: Optional[tk.Toplevel] = None
        self.system_fonts = get_available_fonts()

    def show(self):
        """
        弹出或置顶设置面板
        """
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("偏好设置 - 轻量级防久坐与饮水提醒")
        self.window.geometry("680x600")
        self.window.minsize(620, 520)
        self.window.attributes("-topmost", True)

        # 绑定应用专属图标
        icon_path = os.path.abspath("app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.window.iconbitmap(icon_path)
            except Exception:
                pass

        # 优雅暗夜主题配色
        self.c_bg = "#1e1e2e"
        self.c_card = "#252538"
        self.c_fg = "#cdd6f4"
        self.c_sub = "#a6adc8"
        self.c_accent = "#89b4fa"
        self.c_btn = "#313244"

        # 字号基准（字号调大，解决字体看不清问题）
        scale_pref = self.config.get("settings_font_scale", "标准 (11pt)")
        base_size = 13 if "大" in scale_pref else (15 if "特大" in scale_pref else 11)
        self.f_base = ("Microsoft YaHei UI", base_size)
        self.f_bold = ("Microsoft YaHei UI", base_size, "bold")
        self.f_sub = ("Microsoft YaHei UI", max(9, base_size - 2))

        self.window.configure(bg=self.c_bg)

        # 1. 优先固定底部操作栏（永不被遮挡）
        self._build_bottom_dock(self.window)

        # 2. 选项卡主体
        style = ttk.Style(self.window)
        style.theme_use("clam")
        style.configure("TNotebook", background=self.c_bg, borderwidth=0)
        style.configure("TNotebook.Tab", background=self.c_btn, foreground=self.c_fg,
                        padding=[14, 6], font=self.f_bold)
        style.map("TNotebook.Tab",
                  background=[("selected", self.c_accent)],
                  foreground=[("selected", "#11111b")])

        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=16, pady=(12, 0))

        # Tab 1: 时间节奏
        tab_time = tk.Frame(self.notebook, bg=self.c_card, padx=16, pady=16)
        self.notebook.add(tab_time, text=" ⏱ 时间节奏 ")
        self._build_tab_time(tab_time)

        # Tab 2: 视觉外观与字体排版
        tab_visual = tk.Frame(self.notebook, bg=self.c_card, padx=16, pady=14)
        self.notebook.add(tab_visual, text=" 🎨 视觉与字体 ")
        self._build_tab_visual(tab_visual)

        # Tab 3: 关怀语录库
        tab_quotes = tk.Frame(self.notebook, bg=self.c_card, padx=16, pady=16)
        self.notebook.add(tab_quotes, text=" 📝 关怀语录 ")
        self._build_tab_quotes(tab_quotes)

        # Tab 4: 系统与高级（开机自启、快捷键等）
        tab_system = tk.Frame(self.notebook, bg=self.c_card, padx=16, pady=16)
        self.notebook.add(tab_system, text=" ⚙ 系统与高级 ")
        self._build_tab_system(tab_system)

    def _build_bottom_dock(self, parent: tk.Widget):
        """
        钉在底部的操作按钮栏（保证 100% 始终可见）
        """
        dock = tk.Frame(parent, bg=self.c_bg, padx=16, pady=12)
        dock.pack(side=tk.BOTTOM, fill=tk.X)

        # 右侧操作组：保存 / 预览 / 取消
        btn_save = tk.Button(
            dock, text="💾 保存并应用", command=self._save_and_apply,
            bg=self.c_accent, fg="#11111b", font=self.f_bold,
            relief=tk.FLAT, padx=16, pady=6, cursor="hand2"
        )
        btn_save.pack(side=tk.RIGHT, padx=(8, 0))

        btn_preview = tk.Button(
            dock, text="👁 预览效果", command=self._trigger_preview,
            bg="#fab387", fg="#11111b", font=self.f_bold,
            relief=tk.FLAT, padx=14, pady=6, cursor="hand2"
        )
        btn_preview.pack(side=tk.RIGHT, padx=(8, 0))

        btn_cancel = tk.Button(
            dock, text="取消", command=self.window.destroy,
            bg=self.c_btn, fg=self.c_fg, font=self.f_base,
            relief=tk.FLAT, padx=14, pady=6, cursor="hand2"
        )
        btn_cancel.pack(side=tk.RIGHT)

        # 左侧：恢复默认值
        btn_reset = tk.Button(
            dock, text="恢复默认设置", command=self._reset_defaults,
            bg=self.c_btn, fg="#f38ba8", font=self.f_sub,
            relief=tk.FLAT, padx=10, pady=6, cursor="hand2"
        )
        btn_reset.pack(side=tk.LEFT)

    def _collect_current_ui_settings(self) -> dict:
        """
        收集当前界面上用户正在编辑的所有草稿参数（即使尚未点击保存）
        """
        quotes = list(self.quotes_listbox.get(0, tk.END)) if hasattr(self, 'quotes_listbox') else []
        return {
            "work_duration_minutes": max(1, self.var_work_min.get()),
            "break_duration_minutes": max(1, self.var_break_min.get()),
            "pre_break_seconds": max(5, self.var_pre_sec.get()),
            "overlay_opacity": round(self.var_bg_opacity.get() / 100.0, 2),
            "text_opacity": round(self.var_text_opacity.get() / 100.0, 2),
            "overlay_bg_color": self.var_bg_color.get().strip() or "#181825",
            
            "timer_font_family": self.var_timer_font.get().strip() or "Segoe UI",
            "timer_font_size": max(24, self.var_timer_size.get()),
            "timer_font_color": self.var_timer_color.get().strip() or "#ffffff",
            "timer_font_bold": self.var_timer_bold.get(),
            
            "quote_font_family": self.var_quote_font.get().strip() or "Microsoft YaHei UI",
            "quote_font_size": max(10, self.var_quote_size.get()),
            "quote_font_color": self.var_quote_color.get().strip() or "#cdd6f4",
            "quote_font_bold": self.var_quote_bold.get(),
            "custom_font_path": self.var_custom_font.get().strip(),

            "card_border_width": max(0, self.var_border_width.get()),
            "card_border_color": self.var_border_color.get().strip() or "#89b4fa",
            "bg_image_path": self.var_bg_image.get().strip(),
            "emergency_hotkey": self.var_hotkey.get().strip().lower() or "ctrl+shift+space",
            "idle_threshold_minutes": max(0, self.var_idle.get()),
            "fullscreen_delay_enabled": self.var_fs.get(),
            "settings_font_scale": self.var_font_scale.get(),
            "autostart": self.var_autostart.get(),
            "quotes": quotes or ["预览模式：这是一条示例关怀文案。"]
        }

    def _trigger_preview(self):
        """
        触发无损预览，不打乱真实状态机工作倒计时
        """
        draft_settings = self._collect_current_ui_settings()
        if self.on_preview:
            self.on_preview(draft_settings)

    def _build_tab_time(self, tab: tk.Frame):
        """
        构建时间节奏面板
        """
        r1 = tk.Frame(tab, bg=self.c_card)
        r1.pack(fill=tk.X, pady=8)
        tk.Label(r1, text="专注工作时长 (分钟):", font=self.f_base, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_work_min = tk.IntVar(value=int(self.config.get("work_duration_minutes", 45)))
        tk.Spinbox(r1, from_=1, to=240, textvariable=self.var_work_min, width=10, font=self.f_base).pack(side=tk.RIGHT)

        r2 = tk.Frame(tab, bg=self.c_card)
        r2.pack(fill=tk.X, pady=8)
        tk.Label(r2, text="每次休息时长 (分钟):", font=self.f_base, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_break_min = tk.IntVar(value=int(self.config.get("break_duration_minutes", 3)))
        tk.Spinbox(r2, from_=1, to=60, textvariable=self.var_break_min, width=10, font=self.f_base).pack(side=tk.RIGHT)

        r3 = tk.Frame(tab, bg=self.c_card)
        r3.pack(fill=tk.X, pady=8)
        tk.Label(r3, text="角落下预告提前量 (秒):", font=self.f_base, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_pre_sec = tk.IntVar(value=int(self.config.get("pre_break_seconds", 30)))
        tk.Spinbox(r3, from_=5, to=120, textvariable=self.var_pre_sec, width=10, font=self.f_base).pack(side=tk.RIGHT)

    def _build_tab_visual(self, tab: tk.Frame):
        """
        构建视觉外观定制（解绑透明度、倒计时与语录字体/字号/加粗/颜色、外部字体导入、背景图）
        """
        # ==================== 1. 不透明度调节 ====================
        r_bg_op = tk.Frame(tab, bg=self.c_card)
        r_bg_op.pack(fill=tk.X, pady=3)
        init_bg_op = int(float(self.config.get("overlay_opacity", 0.35)) * 100)
        self.lbl_bg_op = tk.Label(r_bg_op, text=f"蒙版背景不透明度: {init_bg_op}%", font=self.f_base, fg=self.c_fg, bg=self.c_card)
        self.lbl_bg_op.pack(side=tk.LEFT)
        self.var_bg_opacity = tk.IntVar(value=init_bg_op)
        scale_bg = tk.Scale(
            r_bg_op, from_=5, to=95, orient=tk.HORIZONTAL, variable=self.var_bg_opacity,
            bg=self.c_card, fg=self.c_fg, highlightthickness=0, showvalue=False,
            command=lambda v: self.lbl_bg_op.config(text=f"蒙版背景不透明度: {v}%")
        )
        scale_bg.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(15, 0))

        r_fg_op = tk.Frame(tab, bg=self.c_card)
        r_fg_op.pack(fill=tk.X, pady=3)
        init_fg_op = int(float(self.config.get("text_opacity", 1.0)) * 100)
        self.lbl_fg_op = tk.Label(r_fg_op, text=f"文字与倒计时不透明度: {init_fg_op}%", font=self.f_base, fg=self.c_fg, bg=self.c_card)
        self.lbl_fg_op.pack(side=tk.LEFT)
        self.var_text_opacity = tk.IntVar(value=init_fg_op)
        scale_fg = tk.Scale(
            r_fg_op, from_=20, to=100, orient=tk.HORIZONTAL, variable=self.var_text_opacity,
            bg=self.c_card, fg=self.c_fg, highlightthickness=0, showvalue=False,
            command=lambda v: self.lbl_fg_op.config(text=f"文字与倒计时不透明度: {v}%")
        )
        scale_fg.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(15, 0))

        # ==================== 2. 倒计时文字定制 ====================
        r_timer = tk.Frame(tab, bg=self.c_card)
        r_timer.pack(fill=tk.X, pady=5)
        tk.Label(r_timer, text="倒计时字体:", font=self.f_base, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_timer_font = tk.StringVar(value=self.config.get("timer_font_family", "Segoe UI"))
        self.cb_timer_font = ttk.Combobox(r_timer, textvariable=self.var_timer_font, values=self.system_fonts, width=15, font=self.f_base)
        self.cb_timer_font.pack(side=tk.LEFT, padx=5)

        tk.Label(r_timer, text="字号:", font=self.f_base, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT, padx=(6, 0))
        self.var_timer_size = tk.IntVar(value=int(self.config.get("timer_font_size", 68)))
        tk.Spinbox(r_timer, from_=36, to=120, textvariable=self.var_timer_size, width=5, font=self.f_base).pack(side=tk.LEFT, padx=3)

        self.var_timer_bold = tk.BooleanVar(value=bool(self.config.get("timer_font_bold", True)))
        tk.Checkbutton(r_timer, text="加粗", variable=self.var_timer_bold, bg=self.c_card, fg=self.c_fg, selectcolor="#313244", font=self.f_base).pack(side=tk.LEFT, padx=5)

        self.var_timer_color = tk.StringVar(value=self.config.get("timer_font_color", "#ffffff"))
        tk.Button(r_timer, text="🎨 颜色", command=self._pick_timer_color, bg=self.c_btn, fg=self.c_fg, relief=tk.FLAT).pack(side=tk.LEFT, padx=3)

        # ==================== 3. 提示语录文字定制 ====================
        r_quote = tk.Frame(tab, bg=self.c_card)
        r_quote.pack(fill=tk.X, pady=5)
        tk.Label(r_quote, text="提示词字体:", font=self.f_base, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_quote_font = tk.StringVar(value=self.config.get("quote_font_family", "Microsoft YaHei UI"))
        self.cb_quote_font = ttk.Combobox(r_quote, textvariable=self.var_quote_font, values=self.system_fonts, width=15, font=self.f_base)
        self.cb_quote_font.pack(side=tk.LEFT, padx=5)

        tk.Label(r_quote, text="字号:", font=self.f_base, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT, padx=(6, 0))
        self.var_quote_size = tk.IntVar(value=int(self.config.get("quote_font_size", 18)))
        tk.Spinbox(r_quote, from_=12, to=36, textvariable=self.var_quote_size, width=5, font=self.f_base).pack(side=tk.LEFT, padx=3)

        self.var_quote_bold = tk.BooleanVar(value=bool(self.config.get("quote_font_bold", False)))
        tk.Checkbutton(r_quote, text="加粗", variable=self.var_quote_bold, bg=self.c_card, fg=self.c_fg, selectcolor="#313244", font=self.f_base).pack(side=tk.LEFT, padx=5)

        self.var_quote_color = tk.StringVar(value=self.config.get("quote_font_color", "#cdd6f4"))
        tk.Button(r_quote, text="🎨 颜色", command=self._pick_quote_color, bg=self.c_btn, fg=self.c_fg, relief=tk.FLAT).pack(side=tk.LEFT, padx=3)

        # ==================== 4. 自主导入本地字体文件 ====================
        r_custom_font = tk.Frame(tab, bg=self.c_card)
        r_custom_font.pack(fill=tk.X, pady=4)
        tk.Label(r_custom_font, text="自主导入字体:", font=self.f_base, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_custom_font = tk.StringVar(value=self.config.get("custom_font_path", ""))
        self.lbl_custom_font_name = tk.Label(r_custom_font, text=os.path.basename(self.var_custom_font.get()) or "(未导入)", font=self.f_sub, fg=self.c_accent, bg=self.c_card)
        self.lbl_custom_font_name.pack(side=tk.LEFT, padx=6)
        tk.Button(r_custom_font, text="📂 导入字体文件 (.ttf/.otf)...", command=self._import_custom_font, bg=self.c_btn, fg=self.c_fg, relief=tk.FLAT).pack(side=tk.LEFT, padx=3)
        tk.Button(r_custom_font, text="清除", command=self._clear_custom_font, bg=self.c_btn, fg="#f38ba8", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)

        # ==================== 5. 背景色与卡片边框 ====================
        r_bg_border = tk.Frame(tab, bg=self.c_card)
        r_bg_border.pack(fill=tk.X, pady=5)
        tk.Label(r_bg_border, text="背景底色:", font=self.f_base, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_bg_color = tk.StringVar(value=self.config.get("overlay_bg_color", "#181825"))
        tk.Entry(r_bg_border, textvariable=self.var_bg_color, width=9, font=self.f_base).pack(side=tk.LEFT, padx=4)
        tk.Button(r_bg_border, text="🎨", command=self._pick_bg_color, bg=self.c_btn, fg=self.c_fg, relief=tk.FLAT).pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(r_bg_border, text="卡片边框:", font=self.f_base, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_border_width = tk.IntVar(value=int(self.config.get("card_border_width", 0)))
        tk.Spinbox(r_bg_border, from_=0, to=8, textvariable=self.var_border_width, width=4, font=self.f_base).pack(side=tk.LEFT, padx=3)
        self.var_border_color = tk.StringVar(value=self.config.get("card_border_color", "#89b4fa"))
        tk.Button(r_bg_border, text="🎨 边框色", command=self._pick_border_color, bg=self.c_btn, fg=self.c_fg, relief=tk.FLAT).pack(side=tk.LEFT, padx=3)

        # ==================== 6. 自定义背景图片 ====================
        r_img = tk.Frame(tab, bg=self.c_card)
        r_img.pack(fill=tk.X, pady=5)
        tk.Label(r_img, text="全屏壁纸图片:", font=self.f_base, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_bg_image = tk.StringVar(value=self.config.get("bg_image_path", ""))
        tk.Entry(r_img, textvariable=self.var_bg_image, font=self.f_sub).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(r_img, text="浏览...", command=self._browse_image, bg=self.c_btn, fg=self.c_fg, relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(r_img, text="清空", command=lambda: self.var_bg_image.set(""), bg=self.c_btn, fg="#f38ba8", relief=tk.FLAT).pack(side=tk.LEFT)

    def _import_custom_font(self):
        """
        自主导入本地 .ttf / .otf 字体文件
        """
        font_path = filedialog.askopenfilename(
            parent=self.window,
            title="选择要导入的字体文件",
            filetypes=[("字体文件", "*.ttf;*.otf"), ("所有文件", "*.*")]
        )
        if font_path:
            success = load_font_resource(font_path)
            font_family = get_font_family_from_file(font_path)
            if font_family:
                self.var_custom_font.set(font_path)
                self.lbl_custom_font_name.config(text=f"{font_family} ({os.path.basename(font_path)})")
                
                # 动态把新字体插入下拉选择列表中，并设为当前选中
                if font_family not in self.system_fonts:
                    self.system_fonts.insert(0, font_family)
                    self.cb_timer_font["values"] = self.system_fonts
                    self.cb_quote_font["values"] = self.system_fonts
                self.var_timer_font.set(font_family)
                self.var_quote_font.set(font_family)
                messagebox.showinfo("导入成功", f"字体【{font_family}】已成功载入！已自动设置为当前倒计时与提示词字体。", parent=self.window)
            else:
                messagebox.showwarning("提示", "未能识别该字体文件的名称，但已尝试载入。", parent=self.window)

    def _clear_custom_font(self):
        self.var_custom_font.set("")
        self.lbl_custom_font_name.config(text="(未导入)")

    def _browse_image(self):
        path = filedialog.askopenfilename(
            parent=self.window,
            title="选择自定义背景图片",
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp"), ("所有文件", "*.*")]
        )
        if path:
            self.var_bg_image.set(path)

    def _pick_bg_color(self):
        c = colorchooser.askcolor(initialcolor=self.var_bg_color.get(), title="选择背景色", parent=self.window)
        if c and c[1]: self.var_bg_color.set(c[1])

    def _pick_timer_color(self):
        c = colorchooser.askcolor(initialcolor=self.var_timer_color.get(), title="选择倒计时颜色", parent=self.window)
        if c and c[1]: self.var_timer_color.set(c[1])

    def _pick_quote_color(self):
        c = colorchooser.askcolor(initialcolor=self.var_quote_color.get(), title="选择提示词颜色", parent=self.window)
        if c and c[1]: self.var_quote_color.set(c[1])

    def _pick_border_color(self):
        c = colorchooser.askcolor(initialcolor=self.var_border_color.get(), title="选择边框颜色", parent=self.window)
        if c and c[1]: self.var_border_color.set(c[1])

    def _build_tab_quotes(self, tab: tk.Frame):
        """
        关怀提醒语录管理
        """
        list_frame = tk.Frame(tab, bg=self.c_card)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.quotes_listbox = tk.Listbox(
            list_frame, bg="#181825", fg=self.c_fg, selectbackground=self.c_accent,
            selectforeground="#11111b", relief=tk.FLAT, font=self.f_base
        )
        self.quotes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb = tk.Scrollbar(list_frame, command=self.quotes_listbox.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.quotes_listbox.config(yscrollcommand=sb.set)

        for q in self.config.get("quotes", []):
            self.quotes_listbox.insert(tk.END, q)

        bar = tk.Frame(tab, bg=self.c_card)
        bar.pack(fill=tk.X)
        self.entry_new_quote = tk.Entry(bar, bg="#181825", fg=self.c_fg, font=self.f_base, insertbackground=self.c_fg)
        self.entry_new_quote.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        tk.Button(bar, text="➕ 添加", command=self._add_quote, bg=self.c_btn, fg=self.c_fg, relief=tk.FLAT, font=self.f_base).pack(side=tk.LEFT, padx=3)
        tk.Button(bar, text="➖ 删除选中", command=self._delete_quote, bg=self.c_btn, fg="#f38ba8", relief=tk.FLAT, font=self.f_base).pack(side=tk.LEFT, padx=3)

    def _add_quote(self):
        text = self.entry_new_quote.get().strip()
        if text:
            self.quotes_listbox.insert(tk.END, text)
            self.entry_new_quote.delete(0, tk.END)

    def _delete_quote(self):
        sel = self.quotes_listbox.curselection()
        if sel:
            self.quotes_listbox.delete(sel[0])

    def _build_tab_system(self, tab: tk.Frame):
        """
        系统与高级（开机自启动、快捷键、闲置超时、设置字号等）
        """
        r_auto = tk.Frame(tab, bg=self.c_card)
        r_auto.pack(fill=tk.X, pady=8)
        self.var_autostart = tk.BooleanVar(value=is_autostart_enabled())
        tk.Checkbutton(
            r_auto, text="开机自动在后台静默启动（无需手动开启）",
            variable=self.var_autostart, bg=self.c_card, fg=self.c_fg,
            selectcolor="#313244", activebackground=self.c_card, activeforeground=self.c_fg,
            font=self.f_bold
        ).pack(side=tk.LEFT)

        r_hk = tk.Frame(tab, bg=self.c_card)
        r_hk.pack(fill=tk.X, pady=8)
        tk.Label(r_hk, text="紧急跳过快捷键:", font=self.f_base, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_hotkey = tk.StringVar(value=self.config.get("emergency_hotkey", "ctrl+shift+space"))
        tk.Entry(r_hk, textvariable=self.var_hotkey, width=20, font=self.f_base).pack(side=tk.RIGHT)

        r_idle = tk.Frame(tab, bg=self.c_card)
        r_idle.pack(fill=tk.X, pady=8)
        tk.Label(r_idle, text="键鼠离开电脑重置 (分钟):", font=self.f_base, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_idle = tk.IntVar(value=int(self.config.get("idle_threshold_minutes", 5)))
        tk.Spinbox(r_idle, from_=0, to=60, textvariable=self.var_idle, width=8, font=self.f_base).pack(side=tk.RIGHT)

        r_fs = tk.Frame(tab, bg=self.c_card)
        r_fs.pack(fill=tk.X, pady=8)
        self.var_fs = tk.BooleanVar(value=bool(self.config.get("fullscreen_delay_enabled", True)))
        tk.Checkbutton(
            r_fs, text="前台处于独占全屏 (视频/演示/游戏) 时智能顺延蒙版",
            variable=self.var_fs, bg=self.c_card, fg=self.c_fg, selectcolor="#313244",
            activebackground=self.c_card, activeforeground=self.c_fg, font=self.f_base
        ).pack(side=tk.LEFT)

        r_scale = tk.Frame(tab, bg=self.c_card)
        r_scale.pack(fill=tk.X, pady=8)
        tk.Label(r_scale, text="设置界面字体缩放 (重启面板生效):", font=self.f_base, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_font_scale = tk.StringVar(value=self.config.get("settings_font_scale", "标准 (11pt)"))
        cb_scale = ttk.Combobox(
            r_scale, textvariable=self.var_font_scale,
            values=["小 (10pt)", "标准 (11pt)", "大 (13pt)", "特大 (15pt)"],
            width=14, font=self.f_base, state="readonly"
        )
        cb_scale.pack(side=tk.RIGHT)

    def _reset_defaults(self):
        """
        重置为系统默认配置模板
        """
        if messagebox.askyesno("恢复默认确认", "是否确定将所有参数重置为出厂默认值？", parent=self.window):
            self.var_work_min.set(DEFAULT_CONFIG["work_duration_minutes"])
            self.var_break_min.set(DEFAULT_CONFIG["break_duration_minutes"])
            self.var_pre_sec.set(DEFAULT_CONFIG["pre_break_seconds"])
            self.var_bg_opacity.set(int(DEFAULT_CONFIG["overlay_opacity"] * 100))
            self.lbl_bg_op.config(text=f"蒙版背景不透明度: {int(DEFAULT_CONFIG['overlay_opacity'] * 100)}%")
            self.var_text_opacity.set(int(DEFAULT_CONFIG["text_opacity"] * 100))
            self.lbl_fg_op.config(text=f"文字与倒计时不透明度: {int(DEFAULT_CONFIG['text_opacity'] * 100)}%")
            self.var_bg_color.set(DEFAULT_CONFIG["overlay_bg_color"])
            
            self.var_timer_font.set(DEFAULT_CONFIG["timer_font_family"])
            self.var_timer_size.set(DEFAULT_CONFIG["timer_font_size"])
            self.var_timer_color.set(DEFAULT_CONFIG["timer_font_color"])
            self.var_timer_bold.set(DEFAULT_CONFIG["timer_font_bold"])
            
            self.var_quote_font.set(DEFAULT_CONFIG["quote_font_family"])
            self.var_quote_size.set(DEFAULT_CONFIG["quote_font_size"])
            self.var_quote_color.set(DEFAULT_CONFIG["quote_font_color"])
            self.var_quote_bold.set(DEFAULT_CONFIG["quote_font_bold"])
            self.var_custom_font.set("")
            self.lbl_custom_font_name.config(text="(未导入)")

            self.var_border_width.set(DEFAULT_CONFIG["card_border_width"])
            self.var_border_color.set(DEFAULT_CONFIG["card_border_color"])
            self.var_bg_image.set(DEFAULT_CONFIG["bg_image_path"])
            self.var_hotkey.set(DEFAULT_CONFIG["emergency_hotkey"])
            self.var_idle.set(DEFAULT_CONFIG["idle_threshold_minutes"])
            self.var_fs.set(DEFAULT_CONFIG["fullscreen_delay_enabled"])
            self.quotes_listbox.delete(0, tk.END)
            for q in DEFAULT_CONFIG["quotes"]:
                self.quotes_listbox.insert(tk.END, q)

    def _save_and_apply(self):
        """
        保存所有修改并写入磁盘
        """
        quotes = list(self.quotes_listbox.get(0, tk.END))
        if not quotes:
            messagebox.showwarning("提示", "语录库不能为空，请至少保留一条提醒文案！", parent=self.window)
            return

        new_data = {
            "work_duration_minutes": max(1, self.var_work_min.get()),
            "break_duration_minutes": max(1, self.var_break_min.get()),
            "pre_break_seconds": max(5, self.var_pre_sec.get()),
            "overlay_opacity": round(self.var_bg_opacity.get() / 100.0, 2),
            "text_opacity": round(self.var_text_opacity.get() / 100.0, 2),
            "overlay_bg_color": self.var_bg_color.get().strip() or "#181825",
            
            "timer_font_family": self.var_timer_font.get().strip() or "Segoe UI",
            "timer_font_size": max(24, self.var_timer_size.get()),
            "timer_font_color": self.var_timer_color.get().strip() or "#ffffff",
            "timer_font_bold": self.var_timer_bold.get(),
            
            "quote_font_family": self.var_quote_font.get().strip() or "Microsoft YaHei UI",
            "quote_font_size": max(10, self.var_quote_size.get()),
            "quote_font_color": self.var_quote_color.get().strip() or "#cdd6f4",
            "quote_font_bold": self.var_quote_bold.get(),
            "custom_font_path": self.var_custom_font.get().strip(),

            "card_border_width": max(0, self.var_border_width.get()),
            "card_border_color": self.var_border_color.get().strip() or "#89b4fa",
            "bg_image_path": self.var_bg_image.get().strip(),
            "emergency_hotkey": self.var_hotkey.get().strip().lower() or "ctrl+shift+space",
            "idle_threshold_minutes": max(0, self.var_idle.get()),
            "fullscreen_delay_enabled": self.var_fs.get(),
            "settings_font_scale": self.var_font_scale.get(),
            "autostart": self.var_autostart.get(),
            "quotes": quotes
        }

        # 同步开机自启动设置到注册表
        main_pyw_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "main.pyw")
        set_autostart(self.var_autostart.get(), main_pyw_path)

        self.config.update(new_data, auto_save=True)
        messagebox.showinfo("成功", "偏好设置已成功保存并即时生效！", parent=self.window)
        self.window.destroy()
