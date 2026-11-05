"""
==============================================================================
安装向导: setup.py (纯 Python 跨平台安装配置向导)
作    者: VibeCoder
描述: 
    替代脆弱且易报编码错误的 .bat 脚本。
    自动使用国内清华大学镜像源高速安装依赖，并在 Windows 桌面上生成专属水滴图标快捷方式。
==============================================================================
"""

import sys
import subprocess
import os


def main():
    print("==================================================================")
    print("  欢迎使用【轻量级防久坐与饮水提醒工具】环境配置与安装向导")
    print("==================================================================")
    print()

    # 1. 检查 Python 版本
    py_ver = sys.version_info
    print(f"[1/3] 检测到 Python 版本: {py_ver.major}.{py_ver.minor}.{py_ver.micro}")
    if py_ver.major < 3 or (py_ver.major == 3 and py_ver.minor < 8):
        print("[错误] Python 版本过低，推荐使用 Python 3.8 及以上版本。")
        input("按回车键退出...")
        return

    # 2. 高速安装依赖（自动使用清华镜像源加速）
    req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    print(f"[2/3] 正在通过高速镜像源安装必要依赖 (pywin32, pystray, pillow, keyboard)...")
    cmd = [
        sys.executable, "-m", "pip", "install",
        "-r", req_file,
        "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"
    ]
    try:
        ret = subprocess.call(cmd)
        if ret != 0:
            print("[警告] 镜像源安装返回非零状态，正在尝试使用官方源重试...")
            subprocess.call([sys.executable, "-m", "pip", "install", "-r", req_file])
    except Exception as e:
        print(f"[错误] 执行 pip 安装异常: {e}")
        input("按回车键退出...")
        return

    # 3. 创建带专属小水滴图标的桌面快捷方式
    print("[3/3] 正在自动为你生成带有小水滴图标的桌面快捷方式...")
    try:
        from create_desktop_shortcut import create_shortcut
        create_shortcut()
    except Exception as e:
        print(f"[提示] 快捷方式创建提示: {e}")

    print()
    print("==================================================================")
    print("  [大功告成] 所有依赖已就绪！")
    print("  你可以直接返回电脑桌面，双击【防久坐与饮水提醒】图标静默启动！")
    print("==================================================================")
    print()
    input("按回车键完成退出...")


if __name__ == "__main__":
    main()
