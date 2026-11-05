# 💧 WaterPause - 轻量级Windows桌面防久坐与饮水提醒工具

**作者的话**：大家好，这是本人的第一个VibeCoding项目！作为一个技术恐惧人士且非信息类学生，由于自身的需要，第一次产生了VibeCoding的需求，也是第一次用高科技（对我而言Agent确实是高科技了）写了一个很小的项目。如果有人看到了这个小项目，并且发现有不太好用的地方，欢迎提Issue和提供PR！下面是AI帮忙写的项目介绍。

> **WaterPause**: 如水般清澈透明，护你身心健康。
> 
> *A featherweight, click-through desktop break & hydration companion that never locks your workflow.*
> 
> **设计哲学**：“强视觉提醒，零操作阻断” —— 通过全屏半透明穿透蒙版打破盯屏惯性，但鼠标 100% 穿透操作，绝不抢焦点、绝不锁死电脑！

---

## ✨ 核心特色功能

1. **鼠标完全穿透 (Click-Through) 全屏蒙版**：
   - 采用 Windows 底层 `WS_EX_TRANSPARENT` 与 `WS_EX_LAYERED` 属性。
   - 休息时间到达时，平滑弹出全屏半透明暗色遮罩；但鼠标可以直接穿透蒙版点击下方的网页、编辑器或办公软件，完全不耽误紧急保存或交作业！
2. **背景与文字透明度解绑 (双层协同架构)**：
   - 底层背景支持 5% ~ 95% 自由不透明度，支持任意比例全屏壁纸（等比例居中填充裁剪 Cover，绝不变形）。
   - 顶层中央倒计时大字与关怀语录保持 100% 纯正清晰不透明，彻底避免低透明度下看不清文字的问题。
3. **高自由度排版与个性化**：
   - 自动枚举系统内全部 400+ 款字体（楷体、黑体、宋体、仿宋、Segoe UI、Consolas 等）。
   - 支持免安装动态导入本地 `.ttf` / `.otf` 艺术字体。
   - 倒计时与提示词均支持独立的字体、字号、加粗、颜色自由调节，并支持卡片边框定制。
4. **无损实时效果预览 (Live Preview)**：
   - 在设置面板中即可一键无损预览当前正在调试的样式，随时按 `ESC` 退出，绝不打乱后台正常的专注计时。
5. **智能环境感知**：
   - **离席自动归位**：基于 Windows 原生 `GetLastInputInfo` 检测键鼠闲置，离开电脑超时自动将工作计时器归位。
   - **全屏智能避让**：前台处于独占全屏（看视频、放映 PPT、打游戏）时智能顺延休息提醒。
6. **静默轻量与开机自启**：
   - 静默常驻右下角系统托盘，静默运行内存仅约 **15 MB**，后台 CPU 占用绝对为 **0.0%**！
   - 支持一键开启开机自启动（基于用户注册表，无需管理员权限）。

---

## 🚀 快速上手与使用指南

### 方式一：绿色免安装版（强烈推荐，小白首选）
> **电脑里压根不需要安装 Python，开箱即用！**

1. 直接前往本项目的 **[Releases 发布页面](../../releases)**。
2. 下载单个独立文件：**`WaterPause.exe`**。
3. 双击直接在后台静默运行！你可以直接把它发送到桌面快捷方式或在设置中开启开机自启。

---

### 方式二：源码安装与运行（开发者推荐，需要安装Python解释器）

```bash
# 1. 克隆本仓库到本地
git clone <your-repo-url>
cd <repo-folder>

# 2. 运行纯 Python 一键配置向导（自动采用国内清华源高速安装依赖，并在桌面生成水滴图标快捷方式）
python setup.py

# 3. 日常静默启动
pythonw main.pyw
```

---

## 📁 模块架构说明

本软件严格遵循现代桌面客户端分层架构规范进行解耦设计：

```text
├── main.pyw                 # GUI 无黑框静默运行主入口
├── main.py                  # 应用程序总控制器与生命周期调度
├── setup.py                 # 纯 Python 跨平台一键安装向导（自动镜像源加速）
├── create_desktop_shortcut.py # 自动在桌面生成带专属水滴图标的快捷方式
├── requirements.txt         # 开源依赖清单 (pywin32, pystray, pillow, keyboard)
├── app_icon.ico / png       # 原创设计专属高分辨率小水滴时钟图标
├── core/                    # 【核心业务逻辑层】
│   ├── config_manager.py    # 配置管理与 JSON 本地落盘
│   └── state_machine.py     # 四态有限状态机 (WORKING / PRE_BREAK / BREAKING / PAUSED)
├── os_layer/                # 【操作系统适配层】
│   ├── win_api.py           # 高 DPI、多显示器虚拟屏幕、鼠标穿透样式注入
│   ├── font_manager.py      # 系统 400+ 字体枚举与外部 TTF/OTF 动态加载器
│   ├── idle_detector.py     # 键鼠空闲时间探测
│   ├── session_listener.py  # 全屏窗口感知
│   ├── autostart.py         # Windows 注册表开机自启管理
│   └── hotkey_manager.py    # 全局紧急跳过快捷键监听管理
└── ui/                      # 【视觉呈现层】
    ├── overlay_window.py    # 双层协同全屏穿透蒙版 (带无损预览)
    ├── settings_dialog.py   # 选项卡现代化偏好设置面板
    ├── toast_window.py      # 提前 30 秒右下角微提醒卡片
    └── tray_icon.py         # 系统托盘管理
```

---

## ⌨ 快捷键说明

* **`Ctrl + Shift + Space`**（默认）：休息期间遇到紧急情况，按下可立即退出蒙版并重置新一轮工作计时（支持在偏好设置中自定义）。
* **`ESC`**：在偏好设置面板点击“预览效果”时，按下可立即退出预览返回设置。

---

## 🤖 结对编程伙伴 (AI Pair Programmer)

本项目是作者人生中的第一次 **VibeCoding** 实践，全程由作者与 **Google DeepMind - Gemini (Antigravity Agent)** 沉浸式结对设计与开发：
* 💡 **产品定义与交互哲学**：由作者提出“强视觉提醒，零操作阻断”的核心构想与状态机流转需求；
* 🛠 **底层架构与算法落地**：由 Gemini 协助攻克 Windows 原生 `WS_EX_TRANSPARENT` 穿透、双层协同解绑机制、GDI 字体动态解析与事件循环驱动；
* 🎨 **设计与体验调优**：共同打磨了图形化选项卡配置面板、多显示器自适应与无损实时预览功能。
