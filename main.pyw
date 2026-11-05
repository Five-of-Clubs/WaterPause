"""
==============================================================================
入口脚本: main.pyw
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    这是轻量级防久坐提醒工具的【GUI 无黑框静默运行入口】。
    
为什么需要 .pyw 后缀？
    在 Windows 操作系统中：
    - .py  后缀默认调用 python.exe  (附带黑色 cmd 控制台窗口，用户误关会直接杀死程序)
    - .pyw 后缀默认调用 pythonw.exe (GUI 纯静默子系统，绝对不弹任何黑框控制台)
==============================================================================
"""

import os
import sys

# 确保脚本所在目录加入模块搜索路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from main import BreakReminderApplication

if __name__ == "__main__":
    app = BreakReminderApplication()
    app.run()
