import os
import logging
from typing import Dict, List

from langchain_community.vectorstores import FAISS as LangChainFAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document

from RAG.config.constants import EMBEDDING_MODEL, EMBEDDING_DEVICE, persist_directory

logger = logging.getLogger(__name__)


def build_vector_index(documents: List[Dict], force_recreate: bool = False) -> LangChainFAISS:
    model_kwargs = {"device": EMBEDDING_DEVICE}
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL, model_kwargs=model_kwargs, encode_kwargs={"normalize_embeddings": True}
    )

    faiss_index_path = os.path.join(persist_directory, "faiss_index")
    if force_recreate or not (os.path.exists(faiss_index_path) and os.listdir(faiss_index_path)):
        logger.info(f"🔄 强制重建FAISS索引（embedding模型：{EMBEDDING_MODEL}）...")
        if os.path.exists(faiss_index_path):
            import shutil

            logger.info(f"🗑️ 删除旧索引：{faiss_index_path}")
            shutil.rmtree(faiss_index_path)
        os.makedirs(faiss_index_path, exist_ok=True)

        langchain_docs = [
            Document(page_content=doc["page_content"], metadata=doc["metadata"]) for doc in documents if doc["page_content"].strip()
        ]
        if not langchain_docs:
            raise ValueError("❌ 无有效文档内容，无法构建向量索引")

        vectordb = LangChainFAISS.from_documents(langchain_docs, embeddings)
        vectordb.save_local(faiss_index_path)
        logger.info(f"✅ 新建FAISS索引：{faiss_index_path}（共 {len(langchain_docs)} 个文档）")
    else:
        vectordb = LangChainFAISS.load_local(
            faiss_index_path, embeddings, allow_dangerous_deserialization=True
        )
        logger.info(f"✅ 加载已有FAISS索引：{faiss_index_path}")
    return vectordb
