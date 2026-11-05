"""
==============================================================================
文件名称: main.pyw (Windows 静默启动无控制台专用入口)
作    者: VibeCoder
说明:
    在 Windows 系统中，以 .pyw 结尾的脚本默认由 pythonw.exe 执行，
    从源头上不会产生任何黑色的 CMD / 控制台窗口，实现真正的开机静默常驻。
==============================================================================
"""

from main import BreakReminderApplication

if __name__ == "__main__":
    app = BreakReminderApplication()
    app.run()
