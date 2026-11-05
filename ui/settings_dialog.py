"""
==============================================================================
模块名称: ui/settings_dialog.py
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    本模块实现“偏好设置图形化配置面板 (Settings Dialog)”。
    
用户交互功能:
    1. 调节专注工作时长（分钟）、休息时长（分钟）与预告时长（秒）。
    2. 调节全屏蒙版的不透明度滑块（10% ~ 90% 实时预览百分比）。
    3. 支持颜色选择器（Color Chooser）自由定制蒙版背景色与文字颜色。
    4. 自定义紧急跳过全局快捷键。
    5. 自定义增删休息关怀语录库。
    6. 所有修改点击“保存并应用”后即时写入 config.json 并生效。
==============================================================================
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
from typing import Optional, List
from core.config_manager import ConfigManager, DEFAULT_CONFIG


class SettingsDialog:
    """
    偏好设置窗口管理器
    """
    def __init__(self, parent: tk.Tk, config_manager: ConfigManager):
        self.parent = parent
        self.config = config_manager
        self.window: Optional[tk.Toplevel] = None

    def show(self):
        """
        弹出设置窗口；如果已打开则将其提到最前
        """
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("偏好设置 - 防久坐与饮水提醒小工具")
        self.window.geometry("560x680")
        self.window.minsize(520, 600)
        self.window.attributes("-topmost", True)

        # 优雅暗夜主题色彩定义
        self.c_bg = "#1e1e2e"
        self.c_fg = "#cdd6f4"
        self.c_sub = "#a6adc8"
        self.c_card = "#252538"
        self.c_accent = "#89b4fa"

        self.window.configure(bg=self.c_bg)

        # 滚动外层容器构建
        main_frame = tk.Frame(self.window, bg=self.c_bg)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # 1. 区域一：计时时长设置
        self._build_timing_section(main_frame)

        # 2. 区域二：蒙版视觉与个性化外观
        self._build_visual_section(main_frame)

        # 3. 区域三：快捷键与智能感知
        self._build_behavior_section(main_frame)

        # 4. 区域四：关怀提醒语录管理
        self._build_quotes_section(main_frame)

        # 5. 底部操作按钮栏
        self._build_action_buttons(main_frame)

    def _build_timing_section(self, parent: tk.Frame):
        """
        构建工作/休息时长调节区
        """
        sec = tk.LabelFrame(parent, text=" ⏱ 时间与节奏设置 ", font=("Microsoft YaHei UI", 10, "bold"),
                            bg=self.c_card, fg=self.c_accent, padx=12, pady=10)
        sec.pack(fill=tk.X, pady=(0, 12))

        # 工作时长
        row1 = tk.Frame(sec, bg=self.c_card)
        row1.pack(fill=tk.X, pady=3)
        tk.Label(row1, text="专注工作时长 (分钟):", fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_work_min = tk.IntVar(value=int(self.config.get("work_duration_minutes", 45)))
        tk.Spinbox(row1, from_=1, to=180, textvariable=self.var_work_min, width=8).pack(side=tk.RIGHT)

        # 休息时长
        row2 = tk.Frame(sec, bg=self.c_card)
        row2.pack(fill=tk.X, pady=3)
        tk.Label(row2, text="每次休息时长 (分钟):", fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_break_min = tk.IntVar(value=int(self.config.get("break_duration_minutes", 3)))
        tk.Spinbox(row2, from_=1, to=30, textvariable=self.var_break_min, width=8).pack(side=tk.RIGHT)

        # 预告提前量
        row3 = tk.Frame(sec, bg=self.c_card)
        row3.pack(fill=tk.X, pady=3)
        tk.Label(row3, text="角落下预告提前量 (秒):", fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_pre_sec = tk.IntVar(value=int(self.config.get("pre_break_seconds", 30)))
        tk.Spinbox(row3, from_=5, to=120, textvariable=self.var_pre_sec, width=8).pack(side=tk.RIGHT)

    def _build_visual_section(self, parent: tk.Frame):
        """
        构建蒙版视觉外观定制区（不透明度滑块 + 颜色选择器）
        """
        sec = tk.LabelFrame(parent, text=" 🎨 蒙版外观与不透明度 ", font=("Microsoft YaHei UI", 10, "bold"),
                            bg=self.c_card, fg=self.c_accent, padx=12, pady=10)
        sec.pack(fill=tk.X, pady=(0, 12))

        # 不透明度滑块
        row_alpha = tk.Frame(sec, bg=self.c_card)
        row_alpha.pack(fill=tk.X, pady=4)
        curr_opacity = int(float(self.config.get("overlay_opacity", 0.35)) * 100)
        
        self.lbl_opacity = tk.Label(row_alpha, text=f"蒙版不透明度 ({curr_opacity}%):", fg=self.c_fg, bg=self.c_card)
        self.lbl_opacity.pack(side=tk.LEFT)

        self.var_opacity = tk.IntVar(value=curr_opacity)
        scale = tk.Scale(
            row_alpha, from_=10, to=90, orient=tk.HORIZONTAL, variable=self.var_opacity,
            bg=self.c_card, fg=self.c_fg, highlightthickness=0, showvalue=False,
            command=self._on_opacity_change
        )
        scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(15, 0))

        # 蒙版背景色
        row_bg = tk.Frame(sec, bg=self.c_card)
        row_bg.pack(fill=tk.X, pady=4)
        tk.Label(row_bg, text="蒙版背景色 (Hex):", fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_bg_color = tk.StringVar(value=self.config.get("overlay_bg_color", "#181825"))
        
        btn_pick_bg = tk.Button(row_bg, text="🎨 选取颜色", command=self._pick_bg_color, bg="#313244", fg=self.c_fg, relief=tk.FLAT)
        btn_pick_bg.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.entry_bg_color = tk.Entry(row_bg, textvariable=self.var_bg_color, width=10)
        self.entry_bg_color.pack(side=tk.RIGHT)

    def _on_opacity_change(self, val):
        """
        滑块变动实时刷新文字
        """
        self.lbl_opacity.config(text=f"蒙版不透明度 ({val}%):")

    def _pick_bg_color(self):
        """
        唤起系统调色板选择颜色
        """
        color = colorchooser.askcolor(initialcolor=self.var_bg_color.get(), title="选择蒙版背景色")
        if color and color[1]:
            self.var_bg_color.set(color[1])

    def _build_behavior_section(self, parent: tk.Frame):
        """
        快捷键与智能防呆配置
        """
        sec = tk.LabelFrame(parent, text=" ⚡ 快捷键与智能感知 ", font=("Microsoft YaHei UI", 10, "bold"),
                            bg=self.c_card, fg=self.c_accent, padx=12, pady=10)
        sec.pack(fill=tk.X, pady=(0, 12))

        # 紧急跳过快捷键
        row_hk = tk.Frame(sec, bg=self.c_card)
        row_hk.pack(fill=tk.X, pady=3)
        tk.Label(row_hk, text="紧急跳过快捷键:", fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_hotkey = tk.StringVar(value=self.config.get("emergency_hotkey", "ctrl+shift+space"))
        tk.Entry(row_hk, textvariable=self.var_hotkey, width=18).pack(side=tk.RIGHT)

        # 空闲离开检测
        row_idle = tk.Frame(sec, bg=self.c_card)
        row_idle.pack(fill=tk.X, pady=3)
        tk.Label(row_idle, text="键鼠离开电脑重置 (分钟):", fg=self.c_fg, bg=self.c_card).pack(side=tk.LEFT)
        self.var_idle = tk.IntVar(value=int(self.config.get("idle_threshold_minutes", 5)))
        tk.Spinbox(row_idle, from_=0, to=60, textvariable=self.var_idle, width=8).pack(side=tk.RIGHT)

        # 全屏应用智能顺延
        row_fs = tk.Frame(sec, bg=self.c_card)
        row_fs.pack(fill=tk.X, pady=3)
        self.var_fs = tk.BooleanVar(value=bool(self.config.get("fullscreen_delay_enabled", True)))
        tk.Checkbutton(row_fs, text="前台处于独占全屏 (视频/演示/游戏) 时顺延蒙版",
                       variable=self.var_fs, bg=self.c_card, fg=self.c_fg, selectcolor="#313244",
                       activebackground=self.c_card, activeforeground=self.c_fg).pack(side=tk.LEFT)

    def _build_quotes_section(self, parent: tk.Frame):
        """
        关怀语录库管理（列表增删）
        """
        sec = tk.LabelFrame(parent, text=" 📝 休息关怀语录库 ", font=("Microsoft YaHei UI", 10, "bold"),
                            bg=self.c_card, fg=self.c_accent, padx=12, pady=8)
        sec.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        # 列表框
        list_frame = tk.Frame(sec, bg=self.c_card)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=4)

        self.quotes_listbox = tk.Listbox(list_frame, bg="#181825", fg=self.c_fg, selectbackground=self.c_accent,
                                         selectforeground="#11111b", height=4, relief=tk.FLAT)
        self.quotes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame, command=self.quotes_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.quotes_listbox.config(yscrollcommand=scrollbar.set)

        # 填充现有语录
        quotes: List[str] = self.config.get("quotes", [])
        for q in quotes:
            self.quotes_listbox.insert(tk.END, q)

        # 增删输入条
        entry_frame = tk.Frame(sec, bg=self.c_card)
        entry_frame.pack(fill=tk.X, pady=4)

        self.entry_new_quote = tk.Entry(entry_frame, bg="#181825", fg=self.c_fg, insertbackground=self.c_fg)
        self.entry_new_quote.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        tk.Button(entry_frame, text="添加语录", command=self._add_quote, bg="#313244", fg=self.c_fg, relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(entry_frame, text="删除选中", command=self._delete_quote, bg="#313244", fg="#f38ba8", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)

    def _add_quote(self):
        text = self.entry_new_quote.get().strip()
        if text:
            self.quotes_listbox.insert(tk.END, text)
            self.entry_new_quote.delete(0, tk.END)

    def _delete_quote(self):
        sel = self.quotes_listbox.curselection()
        if sel:
            self.quotes_listbox.delete(sel[0])

    def _build_action_buttons(self, parent: tk.Frame):
        """
        底部按钮栏：保存应用 / 取消 / 恢复默认
        """
        btn_bar = tk.Frame(parent, bg=self.c_bg)
        btn_bar.pack(fill=tk.X, pady=(5, 0))

        tk.Button(
            btn_bar, text="💾 保存并应用", command=self._save_and_apply,
            bg=self.c_accent, fg="#11111b", font=("Microsoft YaHei UI", 10, "bold"),
            relief=tk.FLAT, padx=18, pady=6
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            btn_bar, text="取消", command=self.window.destroy,
            bg="#313244", fg=self.c_sub, font=("Microsoft YaHei UI", 10),
            relief=tk.FLAT, padx=12, pady=6
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            btn_bar, text="恢复默认值", command=self._reset_defaults,
            bg="#313244", fg="#f38ba8", font=("Microsoft YaHei UI", 9),
            relief=tk.FLAT, padx=10, pady=6
        ).pack(side=tk.LEFT)

    def _reset_defaults(self):
        """
        重置为系统默认配置模板
        """
        if messagebox.askyesno("恢复默认确认", "是否确定将所有参数重置为出厂默认设置？", parent=self.window):
            self.var_work_min.set(DEFAULT_CONFIG["work_duration_minutes"])
            self.var_break_min.set(DEFAULT_CONFIG["break_duration_minutes"])
            self.var_pre_sec.set(DEFAULT_CONFIG["pre_break_seconds"])
            self.var_opacity.set(int(DEFAULT_CONFIG["overlay_opacity"] * 100))
            self.lbl_opacity.config(text=f"蒙版不透明度 ({int(DEFAULT_CONFIG['overlay_opacity'] * 100)}%):")
            self.var_bg_color.set(DEFAULT_CONFIG["overlay_bg_color"])
            self.var_hotkey.set(DEFAULT_CONFIG["emergency_hotkey"])
            self.var_idle.set(DEFAULT_CONFIG["idle_threshold_minutes"])
            self.var_fs.set(DEFAULT_CONFIG["fullscreen_delay_enabled"])
            self.quotes_listbox.delete(0, tk.END)
            for q in DEFAULT_CONFIG["quotes"]:
                self.quotes_listbox.insert(tk.END, q)

    def _save_and_apply(self):
        """
        校验并保存配置
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
            "emergency_hotkey": self.var_hotkey.get().strip().lower() or "ctrl+shift+space",
            "idle_threshold_minutes": max(0, self.var_idle.get()),
            "fullscreen_delay_enabled": self.var_fs.get(),
            "quotes": quotes
        }

        self.config.update(new_settings, auto_save=True)
        messagebox.showinfo("成功", "偏好设置已成功保存并即时生效！", parent=self.window)
        self.window.destroy()
