"""
==============================================================================
模块名称: ui/settings_dialog.py
作    者: VibeCoder
创建时间: 2026-11-05
更新说明:
    【UI 现代化重构与体验优化】:
    1. 【底部操作栏强置底 (Pinned at Bottom)】: 
       使用独立容器永久锚定在对话框最底部，打开即见“保存并应用”，绝不会因窗口高度不够而被遮挡截断。
    2. 【选项卡式清晰布局 (Tabbed Notebook)】:
       拆分为四大专业选项卡（⏱ 计时节奏 / 🎨 外观与壁纸 / ⚡ 快捷键与感知 / 📝 关怀语录库），
       界面宽敞舒适，告别冗长滚动条。
    3. 【字体与视觉字号升级】:
       界面整体基准字号提升至 11~12pt，文字清晰，各控件呼吸感更强。
    4. 【全方位个性化定制】:
       新增字体族切换、倒计时与语录字号调节、本地高清壁纸浏览选取支持。
    5. 【独立品牌图标】:
       加载 assets/app_icon.ico，替换掉 Python 默认蛇形图标。
==============================================================================
"""

import os
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from typing import Optional, List
from core.config_manager import ConfigManager, DEFAULT_CONFIG


class SettingsDialog:
    """
    偏好设置现代化配置面板
    """
    def __init__(self, parent: tk.Tk, config_manager: ConfigManager):
        self.parent = parent
        self.config = config_manager
        self.window: Optional[tk.Toplevel] = None

    def show(self):
        """
        弹出设置窗口；若已打开则提升至最前
        """
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("偏好设置 - 防久坐与饮水提醒小工具")
        
        # 尺寸与最小限制（完美适配 1080P/2K/4K 屏幕缩放）
        self.window.geometry("620x560")
        self.window.minsize(580, 520)
        self.window.attributes("-topmost", True)

        # 设置独立窗口图标，告别 Python 默认图标
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "app_icon.ico"))
        if os.path.exists(icon_path):
            try:
                self.window.iconbitmap(icon_path)
            except Exception:
                pass

        # 配色规范
        self.c_bg = "#1e1e2e"
        self.c_fg = "#cdd6f4"
        self.c_sub = "#a6adc8"
        self.c_card = "#252538"
        self.c_accent = "#89b4fa"
        self.font_main = ("Microsoft YaHei UI", 11)
        self.font_bold = ("Microsoft YaHei UI", 11, "bold")

        self.window.configure(bg=self.c_bg)

        # ==========================================================
        # 核心修复点 1：底部操作栏必须【优先置底打包 (side=BOTTOM)】
        # 这样无论上方选项卡多大，底部的保存/取消/默认按钮都永远一眼可见！
        # ==========================================================
        self._build_bottom_bar()

        # ==========================================================
        # 核心修复点 2：中间区域采用 Tab 选项卡分页，告别拥挤
        # ==========================================================
        self._build_tabs()

    def _build_bottom_bar(self):
        """
        永久固定在窗口底部的操作按钮栏
        """
        bottom_bar = tk.Frame(self.window, bg=self.c_bg, padx=16, pady=12)
        bottom_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 分割线
        sep = tk.Frame(bottom_bar, bg="#313244", height=1)
        sep.pack(fill=tk.X, pady=(0, 10))

        btn_row = tk.Frame(bottom_bar, bg=self.c_bg)
        btn_row.pack(fill=tk.X)

        # 保存并应用按钮（显眼的高亮强调色）
        tk.Button(
            btn_row, text="💾 保存并应用", command=self._save_and_apply,
            bg=self.c_accent, fg="#11111b", font=self.font_bold,
            relief=tk.FLAT, padx=18, pady=6, cursor="hand2"
        ).pack(side=tk.RIGHT, padx=6)

        # 取消按钮
        tk.Button(
            btn_row, text="取消", command=self.window.destroy,
            bg="#313244", fg=self.c_sub, font=self.font_main,
            relief=tk.FLAT, padx=14, pady=6, cursor="hand2"
        ).pack(side=tk.RIGHT, padx=6)

        # 恢复默认值按钮
        tk.Button(
            btn_row, text="恢复默认设置", command=self._reset_defaults,
            bg="#313244", fg="#f38ba8", font=self.font_main,
            relief=tk.FLAT, padx=12, pady=6, cursor="hand2"
        ).pack(side=tk.LEFT)

    def _build_tabs(self):
        """
        构建选项卡容器与四大页面
        """
        # 配置 ttk 样式使其契合深色主题
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=self.c_bg, borderwidth=0)
        style.configure("TNotebook.Tab", background="#313244", foreground=self.c_sub,
                        padding=[14, 6], font=self.font_bold)
        style.map("TNotebook.Tab",
                  background=[("selected", self.c_accent)],
                  foreground=[("selected", "#11111b")])

        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=(12, 0))

        # Tab 1: ⏱ 计时节奏
        tab_timing = tk.Frame(notebook, bg=self.c_bg, padx=16, pady=16)
        notebook.add(tab_timing, text=" ⏱ 计时节奏 ")
        self._init_tab_timing(tab_timing)

        # Tab 2: 🎨 蒙版与壁纸
        tab_visual = tk.Frame(notebook, bg=self.c_bg, padx=16, pady=16)
        notebook.add(tab_visual, text=" 🎨 蒙版与外观 ")
        self._init_tab_visual(tab_visual)

        # Tab 3: ⚡ 快捷键与感知
        tab_sensor = tk.Frame(notebook, bg=self.c_bg, padx=16, pady=16)
        notebook.add(tab_sensor, text=" ⚡ 快捷键与防打扰 ")
        self._init_tab_sensor(tab_sensor)

        # Tab 4: 📝 关怀语录库
        tab_quotes = tk.Frame(notebook, bg=self.c_bg, padx=16, pady=16)
        notebook.add(tab_quotes, text=" 📝 关怀语录库 ")
        self._init_tab_quotes(tab_quotes)

    # ------------------ Tab 1: 计时设置 ------------------
    def _init_tab_timing(self, parent: tk.Frame):
        card = tk.LabelFrame(parent, text=" 专注与休息时长 ", font=self.font_bold,
                             bg=self.c_card, fg=self.c_accent, padx=16, pady=14)
        card.pack(fill=tk.X)

        # 工作时长
        r1 = tk.Frame(card, bg=self.c_card)
        r1.pack(fill=tk.X, pady=8)
        tk.Label(r1, text="专注工作时长 (分钟):", font=self.font_main, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_work_min = tk.IntVar(value=int(self.config.get("work_duration_minutes", 45)))
        tk.Spinbox(r1, from_=1, to=180, textvariable=self.var_work_min, width=8, font=self.font_main).pack(side=tk.RIGHT)

        # 休息时长
        r2 = tk.Frame(card, bg=self.c_card)
        r2.pack(fill=tk.X, pady=8)
        tk.Label(r2, text="每次休息时长 (分钟):", font=self.font_main, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_break_min = tk.IntVar(value=int(self.config.get("break_duration_minutes", 3)))
        tk.Spinbox(r2, from_=1, to=30, textvariable=self.var_break_min, width=8, font=self.font_main).pack(side=tk.RIGHT)

        # 预告提前量
        r3 = tk.Frame(card, bg=self.c_card)
        r3.pack(fill=tk.X, pady=8)
        tk.Label(r3, text="角落下预告提前量 (秒):", font=self.font_main, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_pre_sec = tk.IntVar(value=int(self.config.get("pre_break_seconds", 30)))
        tk.Spinbox(r3, from_=5, to=120, textvariable=self.var_pre_sec, width=8, font=self.font_main).pack(side=tk.RIGHT)

    # ------------------ Tab 2: 视觉与外观 ------------------
    def _init_tab_visual(self, parent: tk.Frame):
        # 1. 不透明度与背景色
        card1 = tk.LabelFrame(parent, text=" 蒙版背景与透明度 ", font=self.font_bold,
                              bg=self.c_card, fg=self.c_accent, padx=16, pady=12)
        card1.pack(fill=tk.X, pady=(0, 10))

        # 滑块
        r_alpha = tk.Frame(card1, bg=self.c_card)
        r_alpha.pack(fill=tk.X, pady=4)
        curr_op = int(float(self.config.get("overlay_opacity", 0.35)) * 100)
        self.lbl_opacity = tk.Label(r_alpha, text=f"蒙版背景不透明度 ({curr_op}%):", font=self.font_main, fg=self.c_fg, bg=self.c_card)
        self.lbl_opacity.pack(side=tk.LEFT)

        self.var_opacity = tk.IntVar(value=curr_op)
        scale = tk.Scale(
            r_alpha, from_=10, to=90, orient=tk.HORIZONTAL, variable=self.var_opacity,
            bg=self.c_card, fg=self.c_fg, highlightthickness=0, showvalue=False,
            command=lambda v: self.lbl_opacity.config(text=f"蒙版背景不透明度 ({v}%):")
        )
        scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(15, 0))

        # 背景颜色
        r_bg = tk.Frame(card1, bg=self.c_card)
        r_bg.pack(fill=tk.X, pady=6)
        tk.Label(r_bg, text="纯色背景色 (Hex):", font=self.font_main, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_bg_color = tk.StringVar(value=self.config.get("overlay_bg_color", "#181825"))
        tk.Button(r_bg, text="🎨 选取颜色", command=self._pick_bg_color, bg="#313244", fg=self.c_fg, font=self.font_main, relief=tk.FLAT).pack(side=tk.RIGHT, padx=(6, 0))
        tk.Entry(r_bg, textvariable=self.var_bg_color, width=10, font=self.font_main).pack(side=tk.RIGHT)

        # 自定义背景图路径
        r_img = tk.Frame(card1, bg=self.c_card)
        r_img.pack(fill=tk.X, pady=6)
        tk.Label(r_img, text="自定义背景图:", font=self.font_main, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_bg_image = tk.StringVar(value=self.config.get("bg_image_path", ""))
        tk.Button(r_img, text="清空", command=lambda: self.var_bg_image.set(""), bg="#313244", fg="#f38ba8", font=self.font_main, relief=tk.FLAT).pack(side=tk.RIGHT, padx=(4, 0))
        tk.Button(r_img, text="📁 浏览...", command=self._browse_bg_image, bg="#313244", fg=self.c_fg, font=self.font_main, relief=tk.FLAT).pack(side=tk.RIGHT, padx=(6, 0))
        tk.Entry(r_img, textvariable=self.var_bg_image, font=self.font_main).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))

        # 2. 字体与字号
        card2 = tk.LabelFrame(parent, text=" 字体与字号定制 ", font=self.font_bold,
                              bg=self.c_card, fg=self.c_accent, padx=16, pady=12)
        card2.pack(fill=tk.X)

        r_font = tk.Frame(card2, bg=self.c_card)
        r_font.pack(fill=tk.X, pady=4)
        tk.Label(r_font, text="字体族名称:", font=self.font_main, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_font = tk.StringVar(value=self.config.get("font_family", "Microsoft YaHei UI"))
        cb_font = ttk.Combobox(r_font, textvariable=self.var_font, values=["Microsoft YaHei UI", "Segoe UI", "SimHei", "KaiTi", "Consolas"], font=self.font_main, width=18)
        cb_font.pack(side=tk.RIGHT)

        r_size = tk.Frame(card2, bg=self.c_card)
        r_size.pack(fill=tk.X, pady=6)
        tk.Label(r_size, text="倒计时字号 / 语录字号:", font=self.font_main, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_quote_size = tk.IntVar(value=int(self.config.get("quote_font_size", 22)))
        self.var_time_size = tk.IntVar(value=int(self.config.get("time_font_size", 76)))
        tk.Spinbox(r_size, from_=14, to=40, textvariable=self.var_quote_size, width=5, font=self.font_main).pack(side=tk.RIGHT)
        tk.Label(r_size, text=" / ", font=self.font_main, fg=self.c_fg, bg=self.c_card).pack(side=tk.RIGHT)
        tk.Spinbox(r_size, from_=48, to=140, textvariable=self.var_time_size, width=5, font=self.font_main).pack(side=tk.RIGHT)

    def _pick_bg_color(self):
        color = colorchooser.askcolor(initialcolor=self.var_bg_color.get(), title="选取蒙版底色", parent=self.window)
        if color and color[1]:
            self.var_bg_color.set(color[1])

    def _browse_bg_image(self):
        path = filedialog.askopenfilename(
            title="选择背景图片",
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.webp"), ("所有文件", "*.*")],
            parent=self.window
        )
        if path:
            self.var_bg_image.set(path)

    # ------------------ Tab 3: 快捷键与感知 ------------------
    def _init_tab_sensor(self, parent: tk.Frame):
        card = tk.LabelFrame(parent, text=" 快捷键与防打扰策略 ", font=self.font_bold,
                             bg=self.c_card, fg=self.c_accent, padx=16, pady=14)
        card.pack(fill=tk.X)

        # 快捷键
        r_hk = tk.Frame(card, bg=self.c_card)
        r_hk.pack(fill=tk.X, pady=8)
        tk.Label(r_hk, text="紧急跳过快捷键:", font=self.font_main, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_hotkey = tk.StringVar(value=self.config.get("emergency_hotkey", "ctrl+shift+space"))
        tk.Entry(r_hk, textvariable=self.var_hotkey, width=18, font=self.font_main).pack(side=tk.RIGHT)

        # 闲置重置
        r_id = tk.Frame(card, bg=self.c_card)
        r_id.pack(fill=tk.X, pady=8)
        tk.Label(r_id, text="键鼠离开电脑重置 (分钟):", font=self.font_main, fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_idle = tk.IntVar(value=int(self.config.get("idle_threshold_minutes", 5)))
        tk.Spinbox(r_id, from_=0, to=60, textvariable=self.var_idle, width=8, font=self.font_main).pack(side=tk.RIGHT)

        # 全屏智能避让
        r_fs = tk.Frame(card, bg=self.c_card)
        r_fs.pack(fill=tk.X, pady=8)
        self.var_fs = tk.BooleanVar(value=bool(self.config.get("fullscreen_delay_enabled", True)))
        tk.Checkbutton(
            r_fs, text="前台处于独占全屏 (视频/演示/游戏) 时智能顺延蒙版",
            variable=self.var_fs, font=self.font_main,
            bg=self.c_card, fg=self.c_fg, selectcolor="#313244",
            activebackground=self.c_card, activeforeground=self.c_fg
        ).pack(side=tk.LEFT)

    # ------------------ Tab 4: 语录库 ------------------
    def _init_tab_quotes(self, parent: tk.Frame):
        list_box_frame = tk.Frame(parent, bg=self.c_card)
        list_box_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.quotes_listbox = tk.Listbox(
            list_box_frame, bg="#181825", fg=self.c_fg, font=self.font_main,
            selectbackground=self.c_accent, selectforeground="#11111b",
            relief=tk.FLAT, highlightthickness=0
        )
        self.quotes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=6)

        sb = tk.Scrollbar(list_box_frame, command=self.quotes_listbox.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.quotes_listbox.config(yscrollcommand=sb.set)

        for q in self.config.get("quotes", []):
            self.quotes_listbox.insert(tk.END, q)

        # 输入栏
        act_row = tk.Frame(parent, bg=self.c_bg)
        act_row.pack(fill=tk.X)

        self.entry_new_quote = tk.Entry(act_row, bg="#252538", fg=self.c_fg, font=self.font_main, insertbackground=self.c_fg)
        self.entry_new_quote.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        tk.Button(act_row, text="添加语录", command=self._add_quote, bg="#313244", fg=self.c_fg, font=self.font_main, relief=tk.FLAT).pack(side=tk.LEFT, padx=3)
        tk.Button(act_row, text="删除选中", command=self._delete_quote, bg="#313244", fg="#f38ba8", font=self.font_main, relief=tk.FLAT).pack(side=tk.LEFT, padx=3)

    def _add_quote(self):
        txt = self.entry_new_quote.get().strip()
        if txt:
            self.quotes_listbox.insert(tk.END, txt)
            self.entry_new_quote.delete(0, tk.END)

    def _delete_quote(self):
        sel = self.quotes_listbox.curselection()
        if sel:
            self.quotes_listbox.delete(sel[0])

    def _reset_defaults(self):
        """
        恢复系统初始配置
        """
        if messagebox.askyesno("确认恢复", "是否确定将所有参数重置为出厂默认设置？", parent=self.window):
            self.var_work_min.set(DEFAULT_CONFIG["work_duration_minutes"])
            self.var_break_min.set(DEFAULT_CONFIG["break_duration_minutes"])
            self.var_pre_sec.set(DEFAULT_CONFIG["pre_break_seconds"])
            self.var_opacity.set(int(DEFAULT_CONFIG["overlay_opacity"] * 100))
            self.lbl_opacity.config(text=f"蒙版背景不透明度 ({int(DEFAULT_CONFIG['overlay_opacity'] * 100)}%):")
            self.var_bg_color.set(DEFAULT_CONFIG["overlay_bg_color"])
            self.var_bg_image.set(DEFAULT_CONFIG.get("bg_image_path", ""))
            self.var_font.set(DEFAULT_CONFIG.get("font_family", "Microsoft YaHei UI"))
            self.var_time_size.set(DEFAULT_CONFIG.get("time_font_size", 76))
            self.var_quote_size.set(DEFAULT_CONFIG.get("quote_font_size", 22))
            self.var_hotkey.set(DEFAULT_CONFIG["emergency_hotkey"])
            self.var_idle.set(DEFAULT_CONFIG["idle_threshold_minutes"])
            self.var_fs.set(DEFAULT_CONFIG["fullscreen_delay_enabled"])
            self.quotes_listbox.delete(0, tk.END)
            for q in DEFAULT_CONFIG["quotes"]:
                self.quotes_listbox.insert(tk.END, q)

    def _save_and_apply(self):
        """
        验证并保存用户配置
        """
        quotes = list(self.quotes_listbox.get(0, tk.END))
        if not quotes:
            messagebox.showwarning("提示", "关怀语录库不能为空，请至少保留一条提醒文案！", parent=self.window)
            return

        new_settings = {
            "work_duration_minutes": max(1, self.var_work_min.get()),
            "break_duration_minutes": max(1, self.var_break_min.get()),
            "pre_break_seconds": max(5, self.var_pre_sec.get()),
            "overlay_opacity": round(self.var_opacity.get() / 100.0, 2),
            "overlay_bg_color": self.var_bg_color.get().strip() or "#181825",
            "bg_image_path": self.var_bg_image.get().strip(),
            "font_family": self.var_font.get().strip() or "Microsoft YaHei UI",
            "time_font_size": max(20, self.var_time_size.get()),
            "quote_font_size": max(12, self.var_quote_size.get()),
            "emergency_hotkey": self.var_hotkey.get().strip().lower() or "ctrl+shift+space",
            "idle_threshold_minutes": max(0, self.var_idle.get()),
            "fullscreen_delay_enabled": self.var_fs.get(),
            "quotes": quotes
        }

        self.config.update(new_settings, auto_save=True)
        messagebox.showinfo("成功", "偏好设置已成功保存并即时生效！", parent=self.window)
        self.window.destroy()
