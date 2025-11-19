import logging

from RAG.classifiers.bert_classifier import BertSentenceClassifier
from RAG.retrieval.vectorstore import build_vector_index
from RAG.retrieval.bm25 import build_bm25_retriever
from RAG.retrieval.hybrid import hybrid_retrieval
from RAG.utils.llm_intent import intent_translate, simple_llm_call
from RAG.io_utils.inputs import get_single_sentence_input
from RAG.pipeline.analysis import parallel_process_document, save_violation_results
from RAG.config.constants import (
    EMBEDDING_MODEL,
    STRUCTURED_CHUNKS_JSON_PATH,
    input_path,
    VIOLATION_OUTPUT_DIR,
)
from RAG.doc_utils.JsonLoader import load_structured_chunks_from_json, load_and_process_documents

logger = logging.getLogger(__name__)


def run():
    FORCE_RECREATE_VECTOR_INDEX = True

    logger.info("=" * 60)
    logger.info("公平竞争审查全流程（纯文本输入+并行分析+结果保存）")
    logger.info("=" * 60)

    logger.info("[1/6] 初始化LLM客户端...")
    test_response = simple_llm_call("测试连接：返回'LLM_OK'")
    if "LLM_OK" not in test_response:
        logger.warning("⚠️ LLM连接测试异常，可能影响后续分析")
    else:
        logger.info("✅ LLM客户端初始化完成")



    logger.info("[2/6] 初始化BERT分类器...")

    bert_classifier = BertSentenceClassifier()

    logger.info("[3/6] 加载检索库文档分块...")


    try:
        doc_chunks = load_structured_chunks_from_json(STRUCTURED_CHUNKS_JSON_PATH)
    except (FileNotFoundError, ValueError) as e:
        logger.warning(f"⚠️ 从JSON加载失败：{str(e)}，将重新处理本地文档")
        doc_chunks = load_and_process_documents(input_dir=input_path, save_json_path=STRUCTURED_CHUNKS_JSON_PATH)
        FORCE_RECREATE_VECTOR_INDEX = True

    if not doc_chunks:
        logger.error("❌ 无有效文档分块，程序终止")
        return
    logger.info(f"✅ 加载文档分块 {len(doc_chunks)} 个")

    logger.info("[4/6] 构建检索组件...")

    logger.info(f"🔧 使用embedding模型：{EMBEDDING_MODEL}，强制重建：{FORCE_RECREATE_VECTOR_INDEX}")

    vectordb = build_vector_index(doc_chunks, force_recreate=FORCE_RECREATE_VECTOR_INDEX)

    bm25_retriever = build_bm25_retriever(doc_chunks)

    logger.info("✅ 检索组件（FAISS+BM25）构建完成")

    text = "参与评优评奖企业需要在本地落户"
    logger.info("[5/6] 接收用户输入并执行并行分析...")
    user_input_chunks = get_single_sentence_input(text)
    user_text = user_input_chunks[0]["page_content"]

    intent_dict = intent_translate(user_text)
    retrieval_query = intent_dict.get("normalized_query", user_text) or user_text

    logger.info(f"🔍 执行检索（检索指令：{retrieval_query}）")
    retrieval_results = hybrid_retrieval(
        vectordb=vectordb,
        bm25_retriever=bm25_retriever,
        query=retrieval_query,
        intent_dict=intent_dict,
    )
    logger.info("\n" + "=" * 80)
    logger.info(f"📌 检索结果参考（用户输入：{user_text[:50]}...）")
    logger.info("=" * 80)
    for i, (score, doc) in enumerate(retrieval_results, 1):
        source = doc.metadata.get("file_name", "未知文件")
        chapter = doc.metadata.get("parent_chapter_title", "未知章节")
        content = doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
        logger.info(f"\n【第{i}条】- 相似度：{score:.3f}")
        logger.info(f"来源：{source} > {chapter}")
        logger.info(f"内容：{content}")
    logger.info("=" * 80 + "\n")

    logger.info("🚀 启动BERT+LLM并行分析...")


    violation_results = parallel_process_document(
        document_chunks=user_input_chunks,
        bert_classifier=bert_classifier,
        vectordb=vectordb,
        bm25_retriever=bm25_retriever,
    )

    if violation_results:
        save_violation_results(violation_results)
        logger.info(f"🎉 全流程完成！共发现 {len(violation_results)} 条结果，已保存至 {VIOLATION_OUTPUT_DIR}")
    else:
        logger.info("🎉 全流程完成！未发现违规结果")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    run()
