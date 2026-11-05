"""
==============================================================================
模块名称: os_layer/hotkey_manager.py
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    本模块封装全局键盘快捷键的管理，用于在全屏穿透蒙版激活期间，
    监听用户敲击的紧急跳过快捷键（例如 Ctrl+Shift+Space）。
==============================================================================
"""

from typing import Callable, Optional
import keyboard


class HotkeyManager:
    """
    全局快捷键管理器
    """
    def __init__(self):
        self._current_hotkey: Optional[str] = None
        self._callback: Optional[Callable[[], None]] = None

    def register(self, hotkey_str: str, callback: Callable[[], None]) -> bool:
        """
        注册或重新绑定全局快捷键
        :param hotkey_str: 类似 'ctrl+shift+space' 的快捷键字符串
        :param callback: 触发时执行的无参函数
        """
        self.unregister()
        try:
            self._current_hotkey = hotkey_str
            self._callback = callback
            keyboard.add_hotkey(hotkey_str, callback)
            return True
        except Exception as e:
            print(f"[HotkeyManager] 快捷键注册失败 ({hotkey_str}): {e}")
            return False

    def unregister(self):
        """
        注销当前已注册的全局快捷键，释放系统钩子
        """
        if self._current_hotkey:
            try:
                keyboard.remove_hotkey(self._current_hotkey)
            except Exception:
                pass
            self._current_hotkey = None
            self._callback = None
