import logging
from typing import List, Tuple, Dict

from langchain.schema import Document
from langchain_community.vectorstores import FAISS as LangChainFAISS

logger = logging.getLogger(__name__)


def hybrid_retrieval(
    vectordb: LangChainFAISS,
    bm25_retriever,
    query: str,
    intent_dict: dict,
    candidate_size: int = 20,
    final_k: int = 10,
    vector_weight: float = 0.5,
    bm25_weight: float = 0.5,
) -> List[Tuple[float, Document]]:
    candidate_docs: Dict[int, Dict] = {}

    try:
        vector_results = vectordb.similarity_search_with_score(query, k=candidate_size)
        for doc, distance in vector_results:
            similarity_score = 1.0 / (1.0 + distance)
            doc_id = hash(doc.page_content)
            candidate_docs[doc_id] = {"doc": doc, "vector_score": similarity_score, "bm25_score": 0}
        logger.debug(f"✅ FAISS检索到 {len(vector_results)} 条候选结果")
    except Exception as e:
        logger.error(f"❌ FAISS检索失败：{str(e)}", exc_info=True)

    try:
        need_chapter_filter = intent_dict.get("need_chapter_filter") == "是"
        target_chapters = intent_dict.get("target_chapters", [])

        # Prefer using keywords from intent translation for BM25 if provided
        bm25_query = query
        try:
            keywords = intent_dict.get("keywords")
            if isinstance(keywords, list) and len(keywords) > 0:
                bm25_query = " ".join([str(k) for k in keywords if str(k).strip()])
                logger.debug(f"🔎 使用intent keywords作为BM25查询：{bm25_query}")
        except Exception as kw_e:
            logger.warning(f"⚠️ 解析intent keywords失败，回退使用原始查询：{str(kw_e)}")

        if need_chapter_filter and target_chapters:
            bm25_results = bm25_retriever.retrieve_with_chapter_filter(
                query=bm25_query, target_chapters=target_chapters, top_k=candidate_size
            )
        else:
            bm25_results = bm25_retriever.retrieve(query=bm25_query, top_k=candidate_size)

        for score, doc in bm25_results:
            doc_id = hash(doc.page_content)
            if doc_id in candidate_docs:
                candidate_docs[doc_id]["bm25_score"] = score
            else:
                if score > 0:
                    candidate_docs[doc_id] = {"doc": doc, "vector_score": 0, "bm25_score": score}
        logger.debug(f"✅ BM25检索到 {len(bm25_results)} 条候选结果")
    except Exception as e:
        logger.error(f"❌ BM25检索失败：{str(e)}", exc_info=True)

    if not candidate_docs:
        logger.warning("❌ 混合检索无候选结果")
        return []

    max_vector = max([d["vector_score"] for d in candidate_docs.values()], default=1)
    max_bm25 = max([d["bm25_score"] for d in candidate_docs.values()], default=1)

    reranked: List[Tuple[float, Document]] = []
    for doc_item in candidate_docs.values():
        norm_vector = doc_item["vector_score"] / max_vector if max_vector != 0 else 0
        norm_bm25 = doc_item["bm25_score"] / max_bm25 if max_bm25 != 0 else 0
        combined_score = (norm_vector * vector_weight) + (norm_bm25 * bm25_weight)
        reranked.append((combined_score, doc_item["doc"]))

    reranked.sort(key=lambda x: x[0], reverse=True)
    final_results = reranked[:final_k]
    logger.info(f"✅ 混合检索完成，返回Top {len(final_results)} 结果")
    return final_results
