import os
import json
from pathlib import Path
from typing import List, Dict
import logging


from RAG.config.constants import (
    LONG_CHAPTER_WARN_THRESHOLD,

)


from RAG.io_utils.inputs import (
    extract_policy_type,
)


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_and_process_documents(input_dir: str, save_json_path: str) -> List[Dict]:
    from doc2json import PolicyStructurizeAPI
    logger.info(f"📄 开始处理本地文档：{input_dir}")
    struct_api = PolicyStructurizeAPI(long_chapter_warn_threshold=LONG_CHAPTER_WARN_THRESHOLD)

    doc_paths = list(Path(input_dir).glob("*.docx"))
    if not doc_paths:
        raise FileNotFoundError(f"❌ 目录 {input_dir} 下无docx文档")

    all_chunks: List[Dict] = []
    for doc_path in doc_paths:
        doc_name = doc_path.name
        logger.info(f"🔍 处理文档：{doc_name}")
        doc_chunks = struct_api.process_document(str(doc_path), doc_name)
        if not doc_chunks:
            logger.warning(f"⚠️ 文档 {doc_name} 无有效分块，跳过")
            continue
        for chunk in doc_chunks:
            chunk["metadata"]["file_path"] = str(doc_path)
            chunk["metadata"]["file_name"] = doc_name
            chunk["metadata"]["policy_type"] = extract_policy_type(chunk["page_content"])
        all_chunks.extend(doc_chunks)

    with open(save_json_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ 本地文档分块保存至：{save_json_path}（共 {len(all_chunks)} 个分块）")
    return all_chunks


def load_structured_chunks_from_json(json_path: str) -> List[Dict]:
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"❌ JSON文件不存在：{json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    for chunk in chunks:
        chunk.setdefault("page_content", "")
        chunk.setdefault("metadata", {})
        chunk["metadata"].setdefault("file_name", "未知文件")
        chunk["metadata"].setdefault("file_path", "未知路径")
        chunk["metadata"].setdefault("parent_chapter_title", "未知章节")
        chunk["metadata"].setdefault("policy_type", "其他政策")
    return chunks
