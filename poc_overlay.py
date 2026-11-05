"""
==============================================================================
模块名称: poc_overlay.py (概念验证原型 - 全屏穿透蒙版)
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    本脚本是“防久坐与饮水提醒工具”的阶段一核心概念验证 (PoC, Proof of Concept)。
    主要验证 Windows 平台下最核心的两大技术指标：
    1. 【全屏半透明覆盖】：支持高 DPI 缩放与多显示器，呈现 35% 不透明度的柔和暗色背景。
    2. 【鼠标完全穿透 (Click-Through)】：通过 Win32 API 注入 WS_EX_TRANSPARENT 样式，
       使得所有鼠标操作（点击、拖拽、滚动）直接穿透到底层程序，绝不阻断正常工作。
    3. 【全局键盘紧急退出】：注册全局快捷键 (Ctrl+Shift+Space)，按下后可立即关闭蒙版。
==============================================================================
"""

import sys
import ctypes
import tkinter as tk
import win32gui
import win32con
import win32api
import keyboard


def enable_dpi_awareness():
    """
    【高 DPI 感知设置】
    为什么需要这个：
        在现代 Windows 笔记本（如 125%、150% 缩放的屏幕）上，如果程序不声明 DPI 感知，
        操作系统会强制把窗口放大进行拉伸，导致窗口发虚且屏幕尺寸计算错误（无法完美覆盖所有边缘）。
    具体操作：
        调用 Windows 底层 shcore.dll 的 SetProcessDpiAwareness 接口，
        传入参数 2 (PROCESS_PER_MONITOR_DPI_AWARE_V2)，让程序能够按物理像素 1:1 完美贴合屏幕。
    """
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception as e:
        # 如果是较旧版本的 Windows，回退到普通 DPI 感知
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def get_virtual_screen_geometry():
    """
    【多显示器虚拟屏幕尺寸计算】
    为什么需要这个：
        很多同学会外接第二台显示器（扩展模式）。如果只用普通的 screenwidth，
        蒙版只能覆盖主屏幕，副屏幕依然亮着。
    具体操作：
        通过 win32api.GetSystemMetrics 获取整个虚拟桌面 (Virtual Screen) 的边界矩形：
        - SM_XVIRTUALSCREEN / SM_YVIRTUALSCREEN: 虚拟桌面左上角的起点坐标（可能是负数，取决于副屏摆放位置）
        - SM_CXVIRTUALSCREEN / SM_CYVIRTUALSCREEN: 虚拟桌面的总宽度和总高度
    """
    x = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
    y = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
    w = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    h = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    return x, y, w, h


def make_window_click_through(hwnd: int):
    """
    【核心技术点：让 Windows 窗口实现鼠标点击穿透】
    参数:
        hwnd (int): 目标窗口在 Windows 操作系统中的句柄（Handle to a Window，相当于窗口的身份证号）
        
    底层原理通俗解释:
        Windows 操作系统管理着屏幕上的每一个窗口。当我们点击鼠标时，系统会从上往下做“碰撞检测”，
        找到第一个落在该坐标下的窗口并把点击事件发给它。
        
        我们需要给我们的窗口打上三个特殊的 Windows 扩展样式标签（Extended Window Styles）：
        1. WS_EX_LAYERED (0x00080000): 告诉系统本窗口是“分层窗口”，支持半透明颜色混合。
        2. WS_EX_TRANSPARENT (0x00000020): 【最关键属性】告诉系统碰撞检测时直接忽略我！
           把所有鼠标点击、拖拽、滚轮直接顺延传给我下层的窗口。
        3. WS_EX_NOACTIVATE (0x08000000): 告诉系统当这个窗口显示时，不要抢夺底层窗口的输入焦点
           （这样你在写代码时弹出蒙版，你的光标依然在代码编辑器里，打字不中断）。
    """
    # 1. 获取当前窗口已有的扩展样式标志位
    extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    
    # 2. 通过按位或 (|) 运算，把穿透与不抢焦点的属性合并进去
    WS_EX_NOACTIVATE = 0x08000000
    target_style = (
        extended_style
        | win32con.WS_EX_LAYERED
        | win32con.WS_EX_TRANSPARENT
        | WS_EX_NOACTIVATE
    )
    
    # 3. 将新样式写回 Windows 操作系统
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, target_style)


class BreakOverlayPoC:
    """
    全屏休息提醒蒙版原型类
    """
    def __init__(self):
        # 1. 开启高 DPI 支持，确保多显示器尺寸无缝对齐
        enable_dpi_awareness()
        
        # 2. 初始化 Tkinter 根窗口
        self.root = tk.Tk()
        self.root.title("BreakReminder_Overlay_PoC")
        
        # 3. 基础窗口属性设置
        # - overrideredirect(True): 移除所有 Windows 默认边框、标题栏、最大化/最小化按钮
        self.root.overrideredirect(True)
        # - attributes('-topmost', True): 强制窗口置顶，浮于所有普通软件之上
        self.root.attributes('-topmost', True)
        # - attributes('-alpha', 0.35): 设置全窗口 35% 的不透明度（65% 透视，柔和降低盯屏欲望）
        self.root.attributes('-alpha', 0.35)
        
        # 4. 获取跨显示器虚拟全屏尺寸并铺满整个屏幕
        x, y, w, h = get_virtual_screen_geometry()
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        
        # 5. 颜色配置（优雅沉稳的深色暗夜蓝灰色背景）
        self.bg_color = "#181825"
        self.root.configure(bg=self.bg_color)
        
        # 6. 构建界面元素（居中排版）
        self._build_ui()
        
        # 7. 强制刷新窗口事件，确保 Windows 为窗口生成底层的真实句柄 (HWND)
        self.root.update_idletasks()
        
        # 8. 获取真正的顶层窗口句柄并开启“鼠标穿透”
        # 注意: Tkinter 在 Windows 下的 wm_frame() 返回的是顶层 OS 窗口句柄的十六进制字符串
        hwnd = int(self.root.wm_frame(), 16)
        make_window_click_through(hwnd)
        
        # 9. 注册全局快捷键 (Ctrl + Shift + Space)，用于测试紧急跳过退出
        keyboard.add_hotkey('ctrl+shift+space', self.emergency_exit)
        
        # 10. 绑定内部倒计时测试（这里先做个 180 秒倒计时的演示）
        self.remaining_seconds = 180
        self._tick_countdown()

    def _build_ui(self):
        """
        构建蒙版中央的文字内容（休息倒计时 + 温暖提醒文案 + 快捷键指引）
        """
        # 主容器居中
        container = tk.Frame(self.root, bg=self.bg_color)
        container.place(relx=0.5, rely=0.45, anchor="center")
        
        # 1. 顶部大字：剩余休息时间
        self.time_label = tk.Label(
            container,
            text="03:00",
            font=("Segoe UI", 68, "bold"),
            fg="#cdd6f4",
            bg=self.bg_color
        )
        self.time_label.pack(pady=(0, 15))
        
        # 2. 居中文案：提醒语录
        self.quote_label = tk.Label(
            container,
            text="站起来活动一下，去喝杯温水，保护好你的专注力与身体状态。",
            font=("Microsoft YaHei UI", 18),
            fg="#bac2de",
            bg=self.bg_color
        )
        self.quote_label.pack(pady=(0, 25))
        
        # 3. 底部小字：紧急跳过按键提示
        self.tip_label = tk.Label(
            container,
            text="[ 鼠标操作已完全穿透，你可以照常点击下方软件 | 紧急跳过蒙版请按：Ctrl + Shift + Space ]",
            font=("Microsoft YaHei UI", 11),
            fg="#a6adc8",
            bg=self.bg_color
        )
        self.tip_label.pack()

    def _tick_countdown(self):
        """
        每秒跳动一次倒计时
        """
        if self.remaining_seconds > 0:
            minutes = self.remaining_seconds // 60
            seconds = self.remaining_seconds % 60
            self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")
            self.remaining_seconds -= 1
            # 1000 毫秒后再次调用本函数（事件驱动，0 CPU 占用）
            self.root.after(1000, self._tick_countdown)
        else:
            # 倒计时结束自动关闭
            self.emergency_exit()

    def emergency_exit(self):
        """
        紧急退出蒙版
        """
        try:
            keyboard.remove_hotkey('ctrl+shift+space')
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        """
        启动 Tkinter 消息循环
        """
        print(">>> 休息蒙版 PoC 启动成功！")
        print(">>> 测试重点：")
        print("    1. 请尝试用鼠标点击屏幕上的任何软件（如浏览器、任务栏、代码），感受是否能够自由点击穿透！")
        print("    2. 按键盘快捷键【Ctrl + Shift + Space】即可立刻安全退出蒙版。")
        self.root.mainloop()


if __name__ == "__main__":
    app = BreakOverlayPoC()
    app.run()
