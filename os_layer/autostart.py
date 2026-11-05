"""
==============================================================================
模块名称: os_layer/autostart.py
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    本模块负责 Windows 操作系统的“开机自启动”注册与管理。
    
底层原理:
    通过 Python 内置的 winreg 模块，读写 Windows 注册表的当前用户自启项：
    路径: HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
    键名: BreakHydrationReminder
    
    优势:
    1. 属于 HKCU (Current User)，【绝不需要管理员提权 UAC 弹窗】，安全无害。
    2. 自动绑定 pythonw.exe 与 main.pyw，实现开机完全静默无控制台黑框启动。
==============================================================================
"""

import os
import sys
import winreg

REG_SUBKEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "BreakHydrationReminder"


def is_autostart_enabled() -> bool:
    """
    检查当前是否已启用开机自启
    """
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_SUBKEY, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            return bool(value)
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"[Autostart] 查询自启注册表异常: {e}")
        return False


def set_autostart(enable: bool, target_script_path: str) -> bool:
    """
    设置或注销开机自启动项
    :param enable: True 为开启自启，False 为关闭
    :param target_script_path: main.pyw 的绝对路径（如果处于 exe 打包态则直接绑定 exe）
    """
    try:
        if getattr(sys, 'frozen', False):
            # 打包态直接绑定 .exe 自身
            command = f'"{sys.executable}"'
        else:
            # 获取 pythonw.exe 路径（如果当前是 python.exe，自动转换为 pythonw.exe）
            python_exe = sys.executable
            python_dir = os.path.dirname(python_exe)
            pythonw_exe = os.path.join(python_dir, "pythonw.exe")
            if not os.path.exists(pythonw_exe):
                pythonw_exe = python_exe

            abs_script = os.path.abspath(target_script_path)
            command = f'"{pythonw_exe}" "{abs_script}"'

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_SUBKEY, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
                print(f"[Autostart] 已成功注册自启: {command}")
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                    print("[Autostart] 已成功注销开机自启")
                except FileNotFoundError:
                    pass
        return True
    except Exception as e:
        print(f"[Autostart] 设置开机自启失败: {e}")
        return False
