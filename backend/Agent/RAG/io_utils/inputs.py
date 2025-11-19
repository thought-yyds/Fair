from datetime import datetime
from typing import Dict, List, Optional

from RAG.config.constants import TEST_DEMO


def extract_policy_type(text: str) -> str:
    if "奖励" in text or "补贴" in text:
        return "财政奖励"
    elif "准入" in text or "门槛" in text:
        return "市场准入"
    elif "竞争" in text or "审查" in text:
        return "公平竞争审查"
    else:
        return "用户输入内容"


def get_single_sentence_input(sentence: Optional[str] = None) -> List[Dict]:
    if sentence:
        user_input = sentence
    else:
        if TEST_DEMO:
            user_input = "投标保证金应以现金形式交纳，不接受保函或其他形式。"
        else:
            user_input = input("请输入要测试的单个句子：").strip()
            if not user_input:
                raise SystemExit("输入为空，程序终止")

    return [
        {
            "page_content": user_input,
            "metadata": {"source": "user_single_sentence"},
        }
    ]


def get_document_input() -> List[Dict]:
    if TEST_DEMO:
        user_input = "投标保证金应以现金形式交纳，不接受保函或其他形式。"
    else:
        user_input = input("请输入要分析的句子/段落：").strip()
        if not user_input:
            raise SystemExit("输入为空，程序终止")

    return [
        {
            "page_content": user_input,
            "metadata": {
                "file_name": "用户纯文本输入",
                "file_path": "无本地文件路径",
                "parent_chapter_title": "用户输入内容",
                "policy_type": extract_policy_type(user_input),
                "input_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        }
    ]
