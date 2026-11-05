@echo off
chcp 65001 >nul
title 防久坐与饮水提醒小工具 - 一键安装配置

echo ==============================================================================
echo        欢迎使用【轻量级防久坐与饮水提醒工具】一键安装配置向导
echo ==============================================================================
echo.

:: 1. 检测是否安装了 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python 环境！
    echo 请先前往 https://www.python.org 下载安装 Python，
    echo 并在安装界面的第一步务必勾选【Add python.exe to PATH】。
    echo.
    pause
    exit /b
)

echo [1/3] Python 环境检测正常...
python --version
echo.

:: 2. 安装项目依赖库
echo [2/3] 正在通过 pip 安装/校验依赖库 (pywin32, pystray, pillow, keyboard)...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [警告] 依赖安装可能遇到网络问题，请检查网络或更换国内镜像源重试。
    pause
    exit /b
)
echo.

:: 3. 自动生成桌面快捷方式
echo [3/3] 正在为你的桌面创建专属图标的静默快捷方式...
python create_desktop_shortcut.py
echo.

echo ==============================================================================
echo [大功告成] 所有依赖安装完毕，桌面快捷方式已成功创建！
echo 现在你可以回到电脑桌面，双击【防久坐与饮水提醒】图标即可无黑框静默运行！
echo ==============================================================================
echo.
pause
