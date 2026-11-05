"""
==============================================================================
模块名称: core/config_manager.py
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    本模块负责程序全局配置项的管理与本地持久化（基于 JSON 格式存储）。
    
设计范式与原则:
    1. 【单一职责原则 (SRP)】: 只专注于配置的加载、合法性校验、默认值回退与落盘保存。
    2. 【防呆容错机制】: 若本地配置文件不存在、格式损坏或字段缺失，自动使用严谨的默认值，
       绝不让软件因配置文件异常而闪退。
    3. 【响应式观察者 (Observer Pattern)】: 提供配置更新事件回调，界面修改设置后能实时生效。
==============================================================================
"""

import json
import os
import re
from typing import Any, Dict, List, Callable


def sanitize_color(color_val: Any, fallback: str = "#003153") -> str:
    """
    【颜色防呆清洗器 (Color Sanitizer)】
    智能兼容各种用户误填场景：
    1. 自动剔除首尾误敲的空格、多余的 '#'（如 '##003153'）。
    2. 自动补全 '#'：若用户漏填了 '#'（例如填成了 '003153' 或 'fff'），自动纠正为 '#003153'。
    3. 支持剪切板误带 Alpha 的 8 位色（如 '003153ff'），自动截取前 6 位 RGB。
    4. 合法性严谨校验：必须是标准 3 位或 6 位 Hex 颜色。
    5. 兜底容错：若完全乱填（如 'abcxyz' 或乱码），自动平滑回退到安全默认色，绝不让界面卡住或变灰！
    """
    if not color_val:
        return fallback
    c = str(color_val).strip()
    # 剔除开头可能多打的 #（如 ##003153）
    c_hex = c.lstrip("#")
    # 如果纯十六进制部分符合 3 位或 6 位
    if re.match(r"^[0-9a-fA-F]{3}$", c_hex) or re.match(r"^[0-9a-fA-F]{6}$", c_hex):
        return f"#{c_hex}".lower()
    # 容错：如果用户从设计软件复制了带 Alpha 通道的 8 位 Hex（如 003153ff），自动截取前 6 位 RGB
    if re.match(r"^[0-9a-fA-F]{8}$", c_hex):
        return f"#{c_hex[:6]}".lower()
    # 严格匹配 #RGB 或 #RRGGBB
    if re.match(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$", c):
        return c.lower()
    return fallback


# 默认系统配置模板
DEFAULT_CONFIG: Dict[str, Any] = {
    # 1. 核心计时时长配置
    "work_duration_minutes": 45,       # 专注工作时长（分钟）
    "break_duration_minutes": 3,        # 休息时长（分钟）
    "pre_break_seconds": 30,            # 休息预告提前量（秒）
    
    # 2. 蒙版视觉样式配置（背景与文字解绑，支持高度自由定制）
    "overlay_opacity": 0.60,            # 蒙版背景不透明度（默认 60%，提供更沉浸护眼的遮罩感）
    "text_opacity": 1.0,                # 中间计时与文字不透明度（0.2 ~ 1.0，默认 100% 纯正清晰）
    "overlay_bg_color": "#003153",      # 蒙版暗色背景色（经典优雅深沉的普鲁士蓝）
    
    # 3. 字体、字号、颜色与卡片边框定制
    "timer_font_family": "Segoe UI",    # 倒计时字体（Segoe UI / Arial / Consolas / 微软雅黑 等）
    "timer_font_size": 68,              # 倒计时字号
    "timer_font_color": "#ffffff",      # 倒计时文字颜色（纯白）
    "timer_font_bold": True,            # 倒计时加粗开关
    
    "quote_font_family": "Microsoft YaHei UI", # 语录字体
    "quote_font_size": 18,              # 语录字号
    "quote_font_color": "#cdd6f4",      # 语录文字颜色
    "quote_font_bold": False,           # 语录加粗开关
    "custom_font_path": "",             # 自主导入的外部字体文件 (.ttf/.otf) 路径
    
    "card_bg_color": "",                # 居中内容卡片背景色（留空表示纯透明）
    "card_border_color": "#89b4fa",     # 卡片边框颜色
    "card_border_width": 0,             # 卡片边框厚度（0 表示无边框，1~8 表示加线框）
    
    # 4. 自定义背景图片支持
    "bg_image_path": "",                # 自定义背景图片绝对路径（支持 png/jpg/jpeg/bmp）
    "bg_image_opacity": 0.35,           # 背景图片不透明度
    
    # 5. 交互与快捷键
    "emergency_hotkey": "ctrl+shift+space",  # 紧急跳过蒙版全局快捷键
    
    # 6. 智能感知策略与系统开机自启
    "idle_threshold_minutes": 5,        # 键鼠无操作超过此阈值，自动判定为人已离开并归位计时（分钟）
    "fullscreen_delay_enabled": True,   # 当检测到全屏应用（如全屏游戏/看视频）时，顺延蒙版
    "autostart": False,                 # 开机自启动开关
    "settings_font_scale": "标准 (11pt)", # 设置界面字号偏好

    # 7. 自定义提醒语录库（支持增删改）
    "quotes": [
        "站起来活动一下，去喝杯温水，保护好你的专注力与身体状态。",
        "望向窗外远眺 20 秒，让睫状肌彻底放松一下吧。",
        "转动颈椎，伸个懒腰，喝口水，深呼吸。",
        "水是思维的润滑剂，倒杯温水，稍微活动下腰椎与双腿。",
        "久坐伤身，给疲倦的肌肉两分钟舒展时间。"
    ]
}


class ConfigManager:
    """
    配置管理核心类
    """
    def __init__(self, config_path: str = "config.json"):
        """
        初始化配置管理器
        :param config_path: 本地配置文件存储路径
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []
        
        # 启动时立即加载配置
        self.load()

    def load(self) -> Dict[str, Any]:
        """
        从本地文件读取配置；如果文件损坏或不存在，则加载默认值并自动保存。
        """
        if not os.path.exists(self.config_path):
            self._config = DEFAULT_CONFIG.copy()
            self.save()
            return self._config

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                
            # 增量补充：如果本地 json 里缺失了新版本增加的配置字段，用默认值填补
            merged_config = DEFAULT_CONFIG.copy()
            merged_config.update(loaded_data)

            # 核心颜色字段自动防呆清洗，防止用户在 config.json 误删 '#' 或乱填导致渲染异常
            merged_config["overlay_bg_color"] = sanitize_color(merged_config.get("overlay_bg_color"), "#003153")
            merged_config["timer_font_color"] = sanitize_color(merged_config.get("timer_font_color"), "#ffffff")
            merged_config["quote_font_color"] = sanitize_color(merged_config.get("quote_font_color"), "#cdd6f4")
            merged_config["card_border_color"] = sanitize_color(merged_config.get("card_border_color"), "#89b4fa")

            self._config = merged_config
        except Exception as e:
            print(f"[ConfigManager] 读取配置文件异常，回退至默认配置: {e}")
            self._config = DEFAULT_CONFIG.copy()
            self.save()

        return self._config

    def save(self) -> bool:
        """
        将当前内存中的配置保存到磁盘本地 json 文件中
        """
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"[ConfigManager] 保存配置文件失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        安全获取单个配置项
        """
        return self._config.get(key, default if default is not None else DEFAULT_CONFIG.get(key))

    def set(self, key: str, value: Any, auto_save: bool = True):
        """
        修改配置项并触发监听器通知
        """
        self._config[key] = value
        if auto_save:
            self.save()
        self._notify_listeners()

    def update(self, new_data: Dict[str, Any], auto_save: bool = True):
        """
        批量更新配置项
        """
        self._config.update(new_data)
        if auto_save:
            self.save()
        self._notify_listeners()

    def add_listener(self, listener: Callable[[Dict[str, Any]], None]):
        """
        注册配置变更监听器（观察者模式）：当设置更改时通知界面层即时刷新
        """
        if listener not in self._listeners:
            self._listeners.append(listener)

    def _notify_listeners(self):
        """
        广播配置变动
        """
        for listener in self._listeners:
            try:
                listener(self._config)
            except Exception as e:
                print(f"[ConfigManager] 通知监听器异常: {e}")
