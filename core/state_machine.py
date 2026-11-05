"""
==============================================================================
模块名称: core/state_machine.py
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    本模块实现防久坐与饮水工具的【核心有限状态机 (Finite State Machine, FSM)】。
    
设计范式与原则:
    1. 【核心逻辑与界面完全解耦】: 
       状态机只负责计算“当前是什么状态”、“还剩几分几秒”以及“何时发生状态跃迁”，
       绝不包含任何界面绘制代码。它通过回调函数（Callbacks）将事件通知给外部界面层。
    2. 【严谨的四态流转模型】:
       - WORKING: 专注工作态（默认 45 分钟）
       - PRE_BREAK: 休息预告态（最后 30 秒）
       - BREAKING: 休息蒙版态（默认 3 分钟）
       - PAUSED: 挂起/暂停态（手动暂停或闲置离开）
==============================================================================
"""

from enum import Enum
from typing import Callable, Optional, Dict, Any
from core.config_manager import ConfigManager
from os_layer.idle_detector import IdleDetector
from os_layer.session_listener import is_foreground_window_fullscreen


class AppStatus(str, Enum):
    """
    软件四大核心状态枚举
    """
    WORKING = "WORKING"        # 专注工作态
    PRE_BREAK = "PRE_BREAK"    # 休息预告态（倒计时最后 30 秒）
    BREAKING = "BREAKING"      # 全屏休息蒙版态
    PAUSED = "PAUSED"          # 暂停态（用户手动暂停）


class BreakStateMachine:
    """
    防久坐状态机调度引擎
    """
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.idle_detector = IdleDetector()

        # 初始状态为工作态
        self.state: AppStatus = AppStatus.WORKING
        
        # 计时器数值（以秒为单位）
        self.remaining_seconds: int = 0
        self.total_phase_seconds: int = 0
        
        # 暂停恢复倒计时（如果设置了暂停 30 分钟等）
        self.pause_remaining_seconds: Optional[int] = None

        # 事件回调插槽（通过观察者模式连接界面）
        self.on_state_change: Optional[Callable[[AppStatus, AppStatus], None]] = None
        self.on_tick: Optional[Callable[[int, AppStatus], None]] = None

        # 初始化计时数据
        self._init_working_state()

    def _init_working_state(self):
        """
        进入/重置工作态计时
        """
        work_minutes = self.config.get("work_duration_minutes", 45)
        self.total_phase_seconds = int(work_minutes * 60)
        self.remaining_seconds = self.total_phase_seconds

    def _init_breaking_state(self):
        """
        进入休息态计时
        """
        break_minutes = self.config.get("break_duration_minutes", 3)
        self.total_phase_seconds = int(break_minutes * 60)
        self.remaining_seconds = self.total_phase_seconds

    def _transition_to(self, new_state: AppStatus):
        """
        执行状态跃迁并通知观察者
        """
        if self.state == new_state:
            return
        old_state = self.state
        self.state = new_state
        print(f"[StateMachine] 状态流转: {old_state.value} -> {new_state.value}")
        if self.on_state_change:
            self.on_state_change(old_state, new_state)

    def tick(self):
        """
        【心跳脉冲函数】：由系统定时器每秒精准驱动调用一次。
        负责执行时间递减、空闲防呆检测与状态切换判断。
        """
        # 1. 处于暂停状态
        if self.state == AppStatus.PAUSED:
            if self.pause_remaining_seconds is not None:
                self.pause_remaining_seconds -= 1
                if self.pause_remaining_seconds <= 0:
                    self.resume()
            if self.on_tick:
                self.on_tick(self.remaining_seconds, self.state)
            return

        # 2. 智能防呆：检测用户是否已离开电脑（键鼠空闲）
        idle_threshold_minutes = self.config.get("idle_threshold_minutes", 5)
        if idle_threshold_minutes > 0 and self.state in (AppStatus.WORKING, AppStatus.PRE_BREAK):
            if self.idle_detector.is_user_idle(idle_threshold_minutes * 60):
                # 如果用户离开电脑超过了阈值，自动把工作计时器重新归满，避免一回来就弹窗
                self._init_working_state()
                if self.state == AppStatus.PRE_BREAK:
                    self._transition_to(AppStatus.WORKING)
                if self.on_tick:
                    self.on_tick(self.remaining_seconds, self.state)
                return

        # 3. 正常倒计时递减
        self.remaining_seconds -= 1

        # 4. 根据当前状态进行流转决策
        if self.state == AppStatus.WORKING:
            pre_break_sec = self.config.get("pre_break_seconds", 30)
            if self.remaining_seconds <= pre_break_sec:
                # 倒计时进入最后预告阈值
                self._transition_to(AppStatus.PRE_BREAK)

        elif self.state == AppStatus.PRE_BREAK:
            if self.remaining_seconds <= 0:
                # 预告结束，检查是否有全屏应用程序需要顺延
                fullscreen_delay = self.config.get("fullscreen_delay_enabled", True)
                if fullscreen_delay and is_foreground_window_fullscreen():
                    # 前台正在全屏看视频/打游戏，暂缓 10 秒再检查
                    self.remaining_seconds = 10
                else:
                    # 倒计时归零，正式进入全屏休息蒙版态
                    self._init_breaking_state()
                    self._transition_to(AppStatus.BREAKING)

        elif self.state == AppStatus.BREAKING:
            if self.remaining_seconds <= 0:
                # 休息结束，自动流转回新一轮工作态
                self._init_working_state()
                self._transition_to(AppStatus.WORKING)

        # 5. 向界面通知当前的剩余时间
        if self.on_tick:
            self.on_tick(self.remaining_seconds, self.state)

    def trigger_break_now(self):
        """
        用户通过托盘菜单主动点击“立即休息”
        """
        self._init_breaking_state()
        self._transition_to(AppStatus.BREAKING)

    def skip_break(self):
        """
        用户按下紧急快捷键跳过本次休息
        """
        if self.state == AppStatus.BREAKING:
            self._init_working_state()
            self._transition_to(AppStatus.WORKING)

    def pause(self, duration_seconds: Optional[int] = None):
        """
        暂停计时
        :param duration_seconds: 暂停多少秒（None 表示无限期暂停直至手动恢复）
        """
        self.pause_remaining_seconds = duration_seconds
        self._transition_to(AppStatus.PAUSED)

    def resume(self):
        """
        恢复计时
        """
        if self.state == AppStatus.PAUSED:
            self.pause_remaining_seconds = None
            self._transition_to(AppStatus.WORKING)

    def reset_timer(self):
        """
        重置当前工作计时
        """
        self._init_working_state()
        self._transition_to(AppStatus.WORKING)
