#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文档转结构化JSON脚本
直接调用 doc2json 的方法，将指定文件夹中的文档转换为结构化 JSON
"""

import os
import json
import argparse
from pathlib import Path
from typing import List, Dict
import logging

from RAG.doc_utils.doc2json import PolicyStructurizeAPI

# ==================== 配置区域：直接修改这里即可 ====================
# 输入路径：可以是文件或文件夹
INPUT_PATH = "/home/grp/disk1/Agent/实施细则.docx"  # 相对于项目根目录
# 输出路径：JSON文件保存位置
OUTPUT_PATH = "/home/grp/disk1/Agent/new_policy.json"  # 相对于项目根目录
# LLM模型名称
MODEL_NAME = "doubao-seed-1.6-250615"
# 章节超长提醒阈值
LONG_CHAPTER_THRESHOLD = 3000
# =================================================================

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def convert_file_to_json(
    file_path: str,
    output_path: str = None,
    model_name: str = "doubao-seed-1.6-250615",
    long_chapter_warn_threshold: int = 3000
) -> List[Dict]:
    """
    将单个文档转换为结构化JSON
    
    Args:
        file_path: docx文档文件路径
        output_path: 输出JSON文件路径（可选）
        model_name: LLM模型名称
        long_chapter_warn_threshold: 章节超长提醒阈值
    
    Returns:
        文档的结构化块列表
    """
    file = Path(file_path)
    if not file.exists():
        raise FileNotFoundError(f"文件不存在：{file_path}")
    
    if not file.suffix.lower() == ".docx":
        raise ValueError(f"文件必须是 .docx 格式：{file_path}")
    
    # 初始化API
    struct_api = PolicyStructurizeAPI(
        model_name=model_name,
        long_chapter_warn_threshold=long_chapter_warn_threshold
    )
    
    # 处理单个文档
    logger.info(f"开始处理文档：{file_path}")
    all_chunks = struct_api.process_document(str(file))
    
    if not all_chunks:
        logger.warning("未生成任何分块")
        return []
    
    # 确定输出路径
    if output_path is None:
        output_path = str(file.parent / f"{file.stem}.json")
    
    # 保存JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ 处理完成！")
    logger.info(f"📦 生成分块数：{len(all_chunks)}")
    logger.info(f"💾 保存路径：{output_path}")
    logger.info(f"{'='*60}")
    
    return all_chunks


def convert_folder_to_json(
    folder_path: str,
    output_path: str = None,
    model_name: str = "doubao-seed-1.6-250615",
    long_chapter_warn_threshold: int = 3000
) -> List[Dict]:
    """
    将指定文件夹中的文档转换为结构化JSON
    
    Args:
        folder_path: 包含docx文档的文件夹路径
        output_path: 输出JSON文件路径（可选，默认为 folder_path/knowledge_base.json）
        model_name: LLM模型名称
        long_chapter_warn_threshold: 章节超长提醒阈值
    
    Returns:
        所有文档的结构化块列表
    """
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"文件夹不存在：{folder_path}")
    
    # 初始化API
    struct_api = PolicyStructurizeAPI(
        model_name=model_name,
        long_chapter_warn_threshold=long_chapter_warn_threshold
    )
    
    # 调用批量处理方法
    logger.info(f"开始处理文件夹：{folder_path}")
    all_chunks = struct_api.process_documents_batch(str(folder))
    
    if not all_chunks:
        logger.warning("未生成任何分块")
        return []
    
    # 确定输出路径
    if output_path is None:
        output_path = str(folder / "knowledge_base.json")
    
    # 保存JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ 处理完成！")
    logger.info(f"📦 生成分块数：{len(all_chunks)}")
    logger.info(f"💾 保存路径：{output_path}")
    logger.info(f"{'='*60}")
    
    return all_chunks


def main():
    # 获取项目根目录（脚本所在目录的父目录的父目录）
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    parser = argparse.ArgumentParser(
        description="将文档或文件夹中的文档转换为结构化JSON格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 直接运行（使用脚本顶部配置的路径）
  python RAG/doc_utils/convert_to_json.py
  
  # 转换单个文件
  python RAG/doc_utils/convert_to_json.py -i 公平竞争审查条例.docx -o output.json
  
  # 转换文件夹中的所有文档
  python RAG/doc_utils/convert_to_json.py -i ./documents -o output.json
  
  # 使用自定义模型和阈值
  python RAG/doc_utils/convert_to_json.py -i ./documents --model doubao-seed-1.6-250615 --threshold 5000
        """
    )
    
    parser.add_argument(
        "-i", "--input",
        type=str,
        default=None,
        help="输入文件或文件夹路径（可选，默认使用脚本顶部配置的 INPUT_PATH）"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="输出JSON文件路径（可选，默认使用脚本顶部配置的 OUTPUT_PATH）"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="LLM模型名称（可选，默认使用脚本顶部配置的 MODEL_NAME）"
    )
    
    parser.add_argument(
        "--threshold",
        type=int,
        default=None,
        help="章节超长提醒阈值（可选，默认使用脚本顶部配置的 LONG_CHAPTER_THRESHOLD）"
    )
    
    args = parser.parse_args()
    
    # 使用命令行参数或默认配置
    input_path = args.input if args.input else INPUT_PATH
    output_path = args.output if args.output else OUTPUT_PATH
    model_name = args.model if args.model else MODEL_NAME
    threshold = args.threshold if args.threshold else LONG_CHAPTER_THRESHOLD
    
    # 转换为绝对路径（相对于项目根目录）
    input_path_abs = project_root / input_path if not Path(input_path).is_absolute() else Path(input_path)
    output_path_abs = project_root / output_path if not Path(output_path).is_absolute() else Path(output_path)
    
    try:
        # 判断是文件还是文件夹
        if input_path_abs.is_file():
            logger.info(f"📄 处理单个文件：{input_path_abs}")
            convert_file_to_json(
                file_path=str(input_path_abs),
                output_path=str(output_path_abs),
                model_name=model_name,
                long_chapter_warn_threshold=threshold
            )
        elif input_path_abs.is_dir():
            logger.info(f"📁 处理文件夹：{input_path_abs}")
            convert_folder_to_json(
                folder_path=str(input_path_abs),
                output_path=str(output_path_abs),
                model_name=model_name,
                long_chapter_warn_threshold=threshold
            )
        else:
            raise FileNotFoundError(f"输入路径不存在：{input_path_abs}")
    except Exception as e:
        logger.error(f"❌ 处理失败：{str(e)}")
        raise


if __name__ == "__main__":
    main()

