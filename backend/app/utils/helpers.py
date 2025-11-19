# app/utils/helpers.py
import re
import platform
from pathlib import Path
from typing import Optional


def calculate_risk_level(violation_rate: float) -> str:
    """
    根据违规率计算风险等级
    :param violation_rate: 违规句子占比（0-1）
    :return: 风险等级（无风险/低风险/中风险/高风险）
    """
    if violation_rate == 0:
        return "无风险"
    elif violation_rate <= 0.2:
        return "低风险"
    elif violation_rate <= 0.5:
        return "中风险"
    else:
        return "高风险"


def clean_text(text: Optional[str]) -> str:
    """
    文本清洗：去除特殊字符、多余空格，解决乱码问题
    :param text: 原始文本
    :return: 清洗后的文本
    """
    if not text:
        return ""
    # 去除开头的特殊符号（如■、空格、冒号）
    text = re.sub(r'^[■•\s:]+', '', text.strip())
    # 去除所有■、•符号
    text = re.sub(r'[■•]', '', text)
    # 只保留中英文、数字和常见标点
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9.,，。、；;！!？?：:“”‘’""\'\(\)\[\]\{\}《》<>/+=\-*&^%$#@!~` ]', '', text)
    # 多个空格合并为一个
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_system_font_path() -> tuple[Path, str]:
    """
    获取系统中文字体路径（解决PDF生成中文乱码问题）
    :return: (字体路径, 字体名称)
    """
    system = platform.system()
    font_search_paths = []

    if system == "Windows":
        font_search_paths = [
            Path("C:/Windows/Fonts"),
            Path("C:/WINNT/Fonts")
        ]
        font_names = ["simhei.ttf", "simsun.ttc", "microsoftyahei.ttf"]
    elif system == "Linux":
        font_search_paths = [
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path.home() / ".fonts"
        ]
        font_names = ["simhei.ttf", "wqy-microhei.ttc", "simsun.ttc"]
    elif system == "Darwin":  # macOS
        font_search_paths = [
            Path("/System/Library/Fonts"),
            Path("/Library/Fonts"),
            Path.home() / "Library/Fonts"
        ]
        font_names = ["PingFang.ttc", "Heiti TC.ttc", "SimHei.ttf"]
    else:
        raise Exception(f"不支持的操作系统：{system}")

    # 查找可用字体
    for font_dir in font_search_paths:
        if not font_dir.exists():
            continue
        for font_name in font_names:
            font_path = font_dir / font_name
            if font_path.exists():
                return font_path, font_name.split('.')[0]  # 返回路径和无后缀的名称

    raise Exception("未找到可用中文字体，请安装SimHei（黑体）或PingFang（苹方）字体")