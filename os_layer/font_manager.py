"""
==============================================================================
模块名称: os_layer/font_manager.py
作    者: VibeCoder
创建时间: 2026-11-05
模块描述:
    本模块负责 Windows 系统字体枚举与动态加载外部字体文件 (.ttf / .otf)。
    
底层原理:
    1. 【免安装动态加载】: 
       使用 Windows GDI 底层 API AddFontResourceExW (带 FR_PRIVATE 标志)。
       用户导入本地下载的任意 .ttf / .otf 字体文件时，程序可在不修改系统 Fonts 目录、
       不需要管理员 UAC 提权的情况下，让本应用立刻识别并渲染该字体！
    2. 【免第三方库解析 TTF 字体名称】:
       内建基于二进制 struct 的 TrueType / OpenType 'name' 命名表轻量解析器，
       毫秒级提取字体的英文与中文 FontFamily 名称。
    3. 【系统全部字体枚举】:
       提取用户电脑上安装的全部 500+ 款字体，过滤掉竖排符号字体，智能置顶常用精品字体。
==============================================================================
"""

import os
import struct
import ctypes
import tkinter.font as tkfont
from typing import List, Optional

FR_PRIVATE = 0x10  # 仅当前进程私有可见，不污染操作系统全局字体库


def load_font_resource(font_path: str) -> bool:
    """
    向 Windows 操作系统 GDI 引擎动态注册一个外部字体文件
    :param font_path: .ttf 或 .otf 字体文件的绝对路径
    """
    if not os.path.exists(font_path):
        return False
    try:
        ret = ctypes.windll.gdi32.AddFontResourceExW(font_path, FR_PRIVATE, 0)
        return ret > 0
    except Exception as e:
        print(f"[FontManager] 加载外部字体文件失败: {e}")
        return False


def get_font_family_from_file(font_path: str) -> Optional[str]:
    """
    纯 Python 二进制解析 TTF/OTF 文件头中的 'name' 表，提取字体家族名称 (Font Family)
    """
    if not os.path.exists(font_path):
        return None
    try:
        with open(font_path, "rb") as f:
            data = f.read(4096)
        if len(data) < 12:
            return None

        # 读取表数量
        num_tables = struct.unpack(">H", data[4:6])[0]
        name_offset = None

        # 遍历表目录寻找 'name' 标签
        for i in range(num_tables):
            entry = data[12 + i * 16 : 28 + i * 16]
            tag = entry[0:4]
            if tag == b"name":
                name_offset = struct.unpack(">I", entry[8:12])[0]
                break

        if name_offset is not None:
            with open(font_path, "rb") as f:
                f.seek(name_offset)
                name_data = f.read(8192)

            if len(name_data) > 6:
                count, string_offset = struct.unpack(">HH", name_data[2:6])
                for i in range(count):
                    rec = name_data[6 + i * 12 : 18 + i * 12]
                    platform_id, encoding_id, lang_id, name_id, length, offset = struct.unpack(
                        ">HHHHHH", rec
                    )
                    # name_id == 1 表示 Font Family Name; name_id == 4 表示 Full Font Name
                    if name_id in (1, 4):
                        str_bytes = name_data[
                            string_offset + offset : string_offset + offset + length
                        ]
                        try:
                            # Windows/Unicode 编码通常是 utf-16-be
                            encoding = "utf-16-be" if platform_id in (0, 3) else "utf-8"
                            name = str_bytes.decode(encoding, errors="ignore").strip("\x00").strip()
                            if name:
                                return name
                        except Exception:
                            pass
    except Exception as e:
        print(f"[FontManager] 解析字体名称异常: {e}")

    # 回退：使用去除扩展名的文件名作为字体名
    base_name = os.path.splitext(os.path.basename(font_path))[0]
    return base_name


# 推荐置顶的精品中英文字体列表
RECOMMENDED_FONTS = [
    "Microsoft YaHei UI",     # 微软雅黑 UI（清晰现代）
    "Segoe UI",               # Windows 默认西文字体
    "SimHei",                 # 黑体（醒目厚重）
    "KaiTi",                  # 楷体（优雅书卷书法感）
    "SimSun",                 # 宋体（传统衬线端庄）
    "FangSong",               # 仿宋（典雅规整）
    "Consolas",               # 经典等宽极客代码体
    "Arial",                  # 经典无衬线体
    "Georgia",                # 经典优雅报刊衬线体
    "Impact"                  # 粗重视觉冲击体
]


def get_available_fonts() -> List[str]:
    """
    获取全部可用字体列表：
    置顶推荐字体 + 系统内安装的所有干净字体（自动过滤以 @ 开头的竖排字符集）
    """
    try:
        all_fams = sorted(list(set(tkfont.families())))
        # 过滤竖排字体（以 @ 开头，不适合水平居中排版）
        clean_fams = [f for f in all_fams if not f.startswith("@")]
    except Exception:
        clean_fams = RECOMMENDED_FONTS.copy()

    result = []
    # 1. 优先加入推荐列表（若系统支持）
    for rec in RECOMMENDED_FONTS:
        if rec in clean_fams and rec not in result:
            result.append(rec)
    
    # 2. 补充系统内其他字体
    for f in clean_fams:
        if f not in result:
            result.append(f)

    return result
