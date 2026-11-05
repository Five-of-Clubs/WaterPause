"""
==============================================================================
脚本名称: create_desktop_shortcut.py
描述: 利用 pywin32 在 Windows 桌面上自动生成带专属图标的快捷方式
==============================================================================
"""

import os
import sys
import win32com.client


def create_shortcut():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    target_script = os.path.join(project_dir, "main.pyw")
    icon_path = os.path.join(project_dir, "app_icon.ico")

    # 寻找 pythonw.exe 路径（无黑框 GUI 运行版）
    python_dir = os.path.dirname(sys.executable)
    pythonw_exe = os.path.join(python_dir, "pythonw.exe")
    if not os.path.exists(pythonw_exe):
        pythonw_exe = sys.executable

    shell = win32com.client.Dispatch("WScript.Shell")
    desktop = shell.SpecialFolders("Desktop")
    shortcut_path = os.path.join(desktop, "防久坐与饮水提醒.lnk")

    shortcut = shell.CreateShortcut(shortcut_path)
    shortcut.TargetPath = pythonw_exe
    shortcut.Arguments = f'"{target_script}"'
    shortcut.WorkingDirectory = project_dir
    shortcut.IconLocation = f"{icon_path},0"
    shortcut.Description = "轻量级桌面防久坐与饮水提醒小工具"
    shortcut.Save()

    print("[OK] 桌面快捷方式已成功生成！")
    print(f"[OK] 快捷方式目标: {shortcut_path}")
    print(f"[OK] 专属图标路径: {icon_path}")


if __name__ == "__main__":
    create_shortcut()
