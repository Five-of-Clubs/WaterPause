@echo off
chcp 65001 >nul
title 防久坐与饮水提醒小工具 - 一键安装与环境配置
cd /d "%~dp0"

echo ======================================================================
echo          防久坐与饮水提醒工具 - 一键安装向导 (GitHub 开源版)
echo ======================================================================
echo.

:: 1. 检查电脑是否安装了 Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo 【错误】未检测到 Python 环境！
    echo 请先前往 Python 官网 (https://www.python.org) 安装 Python 并勾选 "Add python.exe to PATH"。
    echo.
    pause
    exit /b 1
)

echo [1/3] 检测到 Python 环境，正在安装运行所需的依赖库...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo 【警告】依赖安装过程中出现网络问题，尝试使用清华镜像源重试...
    python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo.
echo [2/3] 正在生成带有专属图标的桌面快捷方式...
python create_desktop_shortcut.py

echo.
echo [3/3] 正在测试静默启动入口...
echo.
echo ======================================================================
echo   恭喜你！全部依赖与桌面图标已配置完成！
echo   现在你的桌面上已经有了【防久坐与饮水提醒】的小水滴图标。
echo   以后直接双击桌面图标即可在后台静默运行，享受健康专注时光！
echo ======================================================================
echo.
pause
