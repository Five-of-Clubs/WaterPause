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
from typing import Any, Dict, List, Callable


# 默认系统配置模板
DEFAULT_CONFIG: Dict[str, Any] = {
    # 1. 核心计时时长配置
    "work_duration_minutes": 45,       # 专注工作时长（分钟）
    "break_duration_minutes": 3,        # 休息时长（分钟）
    "pre_break_seconds": 30,            # 休息预告提前量（秒）
    
    # 2. 蒙版视觉样式配置（支持用户自由调节）
    "overlay_opacity": 0.35,            # 蒙版不透明度（0.1 ~ 0.9，默认 35%）
    "overlay_bg_color": "#181825",      # 蒙版暗色背景色（优雅深灰蓝）
    "overlay_text_color": "#cdd6f4",    # 倒计时大字颜色（柔和暖白灰）
    "overlay_quote_color": "#bac2de",   # 语录文字颜色（次级白）
    
    # 3. 交互与快捷键
    "emergency_hotkey": "ctrl+shift+space",  # 紧急跳过蒙版全局快捷键
    
    # 4. 智能感知策略
    "idle_threshold_minutes": 5,        # 键鼠无操作超过此阈值，自动判定为人已离开并归位计时（分钟）
    "fullscreen_delay_enabled": True,   # 当检测到全屏应用（如全屏游戏/看视频）时，顺延蒙版
    
    # 5. 自定义提醒语录库（支持增删改）
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
