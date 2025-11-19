import logging
from typing import List, Tuple, Dict, Any

import jieba
from rank_bm25 import BM25Okapi
from langchain.schema import Document

from RAG.config.constants import CHAPTER_BM25_THRESHOLD

logger = logging.getLogger(__name__)


class CustomBM25Retriever:
    def __init__(self, docs: List[Dict], bm25_model: BM25Okapi):
        self.bm25 = bm25_model
        self.docs = docs
        self._all_chapters = [doc["metadata"]["parent_chapter_title"] for doc in docs]
        self._chapter_bm25 = self._build_chapter_bm25()

    def _build_chapter_bm25(self) -> BM25Okapi:
        tokenized_chapters = [list(jieba.cut(chap)) for chap in self._all_chapters]
        return BM25Okapi(tokenized_chapters, k1=1.2, b=0.4)

    def retrieve(self, query: str, top_k: int = 50) -> List[Tuple[float, Document]]:
        tokenized_query = list(jieba.cut(query))
        scores = self.bm25.get_scores(tokenized_query)
        results = [
            (
                scores[i],
                Document(
                    page_content=self.docs[i]["page_content"],
                    metadata=self.docs[i]["metadata"],
                ),
            )
            for i in range(len(self.docs))
            if scores[i] > 0
        ]
        results.sort(key=lambda x: x[0], reverse=True)
        return results[:top_k]

    def retrieve_with_chapter_filter(
        self, query: str, target_chapters: List[str], top_k: int = 50
    ) -> List[Tuple[float, Document]]:
        tokenized_chap_query = list(jieba.cut(" ".join(target_chapters)))
        chap_scores = self._chapter_bm25.get_scores(tokenized_chap_query)
        relevant_indices = [i for i, score in enumerate(chap_scores) if score > CHAPTER_BM25_THRESHOLD]
        if not relevant_indices:
            logger.warning("⚠️ 无匹配章节，执行基础BM25检索")
            return self.retrieve(query, top_k)

        filtered_docs = [self.docs[i] for i in relevant_indices]
        filtered_texts = [doc["page_content"] for doc in filtered_docs]
        tokenized_texts = [list(jieba.cut(text)) for text in filtered_texts]
        content_bm25 = BM25Okapi(tokenized_texts)

        tokenized_content_query = list(jieba.cut(query))
        content_scores = content_bm25.get_scores(tokenized_content_query)

        results = [
            (
                content_scores[i],
                Document(
                    page_content=filtered_docs[i]["page_content"],
                    metadata=filtered_docs[i]["metadata"],
                ),
            )
            for i in range(len(filtered_docs))
            if content_scores[i] > 0
        ]
        results.sort(key=lambda x: x[0], reverse=True)
        return results[:top_k]


def build_bm25_retriever(documents: List[Dict]) -> CustomBM25Retriever:
    texts = [doc["page_content"] for doc in documents if doc["page_content"].strip()]
    if not texts:
        raise ValueError("❌ 无有效文本内容，无法构建BM25检索器")
    tokenized_corpus = [list(jieba.cut(text)) for text in texts]
    bm25_model = BM25Okapi(tokenized_corpus)
    return CustomBM25Retriever(docs=documents, bm25_model=bm25_model)
