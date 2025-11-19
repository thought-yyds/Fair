import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor

from langchain_community.vectorstores import FAISS as LangChainFAISS

from RAG.classifiers.bert_classifier import BertSentenceClassifier
from RAG.retrieval.bm25 import CustomBM25Retriever
from RAG.utils.llm_intent import intent_translate, simple_llm_call
from RAG.config.constants import (
    RULE_MAPPING,
    MAX_THREAD_WORKERS,
    VIOLATION_OUTPUT_DIR,
)

logger = logging.getLogger(__name__)


def llm_paragraph_judge(
    paragraph: str,
    doc_metadata: Dict[str, Any],
    vectordb: LangChainFAISS,
    bm25_retriever: CustomBM25Retriever,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    try:
        intent_query = f"分析段落是否存在公平竞争违规：{paragraph[:200]}..."
        intent_dict = intent_translate(intent_query)
        retrieval_query = intent_dict.get("normalized_query", intent_query) or intent_query
        logger.debug(f"✅ 使用检索指令：{retrieval_query}")

        from RAG.retrieval.hybrid import hybrid_retrieval

        basis_list = hybrid_retrieval(
            vectordb=vectordb,
            bm25_retriever=bm25_retriever,
            query=retrieval_query,
            intent_dict=intent_dict,
            candidate_size=20,
            final_k=5,
        )

        basis_text = ""
        for i, (score, doc) in enumerate(basis_list, 1):
            source = doc.metadata.get("file_name", "未知文件")
            chapter = doc.metadata.get("parent_chapter_title", "未知章节")
            content = doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
            basis_text += f"条款{i}（来源：{source} - {chapter}，相似度：{score:.3f}）：{content}\n"

        llm_prompt = f"""
                你是公平竞争审查专家，基于以下信息分析段落违规情况，仅输出JSON数组（无多余文字）：
                1. 【核心逻辑优先】：若条款禁止“将‘本地投资/落户/设立分支机构’作为‘参与某类活动’的必要条件”，无论活动是政府采购、招标投标、评优评奖、补贴申请还是其他类似活动，均属同类违规；
                2. 【违规类型灵活】：若RULE_MAPPING无完全匹配类型，可按核心逻辑自定义类型（如“将本地落户作为评优评奖必要条件，排斥外地经营者”）；
                3. 【依据引用宽松】：依据可引用条款的核心禁止逻辑，无需严格匹配条款字面场景；
                4. 【无违规的唯一条件】：仅当输入场景与所有条款的核心逻辑无关时，才返回空数组。
    
                【待分析段落】
                {paragraph}
    
                【参考条款】
                {basis_text if basis_text else "无相关条款"}
    
                【输出格式】
                [
                    {{
                        "violation_sentence": "完整违规句子",
                        "violation_type": "按核心逻辑定义的违规类型",
                        "confidence": 0.0-1.0（逻辑越接近，置信度越高）,
                        "basis": "引用条款核心逻辑+原文片段",
                        "suggestion": "删除‘本地落户’要求，允许所有符合条件的企业参与",
                        "source": "LLM段落级分析（火山引擎Ark）"
                    }}
                ]
            """
        llm_prompt = llm_prompt.strip()

        response = simple_llm_call(llm_prompt)
        import json

        parsed = json.loads(response.strip())
        llm_results = parsed if isinstance(parsed, list) else [parsed] if isinstance(parsed, dict) else []

        for res in llm_results:
            results.append(
                {
                    "violation_sentence": res.get("violation_sentence", ""),
                    "violation_type": res.get("violation_type", "未明确违规类型"),
                    "confidence": round(res.get("confidence", 0.0), 3),
                    "basis": res.get("basis", "无明确依据"),
                    "suggestion": res.get("suggestion", "无具体建议"),
                    "source": res.get("source", "LLM段落级分析（火山引擎Ark）"),
                    "file_name": doc_metadata.get("file_name", "未知文件"),
                    "file_path": doc_metadata.get("file_path", "未知路径"),
                    "parent_chapter": doc_metadata.get("parent_chapter_title", "未知章节"),
                    "paragraph_context": paragraph[:100] + "...",
                }
            )
        logger.info(f"✅ LLM段落分析完成（段落：{paragraph[:50]}...），发现 {len(results)} 条违规")
    except Exception as e:
        logger.error(f"❌ LLM段落分析失败（段落：{paragraph[:50]}...）：{str(e)}", exc_info=True)
    return results


def parallel_process_document(
    document_chunks: List[Dict],
    bert_classifier: BertSentenceClassifier,
    vectordb: LangChainFAISS,
    bm25_retriever: CustomBM25Retriever,
) -> List[Dict[str, Any]]:
    all_bert_results: List[Dict[str, Any]] = []
    all_llm_results: List[Dict[str, Any]] = []

    task_data = []
    for chunk in document_chunks:
        paragraph = chunk.get("page_content", "").strip()
        if not paragraph:
            logger.warning("⚠️ 空段落跳过")
            continue
        sentences = [s.strip() for s in re.split(r"[。；;！!?？]", paragraph) if len(s.strip()) > 5]
        task_data.append({"paragraph": paragraph, "sentences": sentences, "metadata": chunk.get("metadata", {})})
    if not task_data:
        logger.warning("❌ 无有效任务数据，并行处理终止")
        return []

    def process_bert() -> None:
        nonlocal all_bert_results
        logger.info(f"✅ BERT处理启动，共 {len(task_data)} 个段落")
        for data in task_data:
            for sent in data["sentences"]:
                pred_id, confidence = bert_classifier.predict(sent)
                if pred_id is None or confidence is None:
                    continue
                violation_type = RULE_MAPPING.get(pred_id, f"未知类型（ID：{pred_id}）")
                all_bert_results.append(
                    {
                        "violation_sentence": sent + "。" if not sent.endswith(("。", "！", "？")) else sent,
                        "violation_type": violation_type,
                        "confidence": round(confidence, 3),
                        "basis": f"BERT模型预测（类别ID：{pred_id}，置信度：{confidence:.3f}）",
                        "suggestion": f"参考「{violation_type}」相关条款进一步核查",
                        "source": "BERT句子级分析",
                        "file_name": data["metadata"].get("file_name", "未知文件"),
                        "file_path": data["metadata"].get("file_path", "未知路径"),
                        "parent_chapter": data["metadata"].get("parent_chapter_title", "未知章节"),
                    }
                )
        logger.info(f"✅ BERT处理完成，共发现 {len(all_bert_results)} 条结果")

    def process_llm() -> None:
        nonlocal all_llm_results
        logger.info(f"✅ LLM处理启动，共 {len(task_data)} 个段落")
        for data in task_data:
            llm_res = llm_paragraph_judge(
                paragraph=data["paragraph"],
                doc_metadata=data["metadata"],
                vectordb=vectordb,
                bm25_retriever=bm25_retriever,
            )
            all_llm_results.extend(llm_res)
        logger.info(f"✅ LLM处理完成，共发现 {len(all_llm_results)} 条结果")

    with ThreadPoolExecutor(max_workers=MAX_THREAD_WORKERS) as executor:
        futures = [executor.submit(process_bert), executor.submit(process_llm)]
        for future in futures:
            future.result()

    merged_results: List[Dict[str, Any]] = []
    seen_keys = set()
    for res in all_bert_results + all_llm_results:
        clean_sent = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]", "", res["violation_sentence"])  # type: ignore[index]
        clean_type = res["violation_type"].strip()  # type: ignore[index]
        key = (clean_sent, clean_type)
        if key not in seen_keys:
            seen_keys.add(key)
            merged_results.append(res)

    logger.info(f"✅ 并行处理结果融合完成，最终保留 {len(merged_results)} 条不重复结果")
    return merged_results


def save_violation_results(results: List[Dict[str, Any]], output_dir: str = VIOLATION_OUTPUT_DIR) -> None:
    import os
    import json

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    json_path = os.path.join(output_dir, f"violation_results_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ 违规结果JSON已保存：{json_path}")

    report_path = os.path.join(output_dir, f"violation_report_{timestamp}.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# 公平竞争审查违规分析报告\n")
        f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总结果条数：{len(results)}\n")
        f.write(f"分析来源：BERT句子级分析 + LLM段落级分析\n\n")

        file_groups: Dict[str, List[Dict[str, Any]]] = {}
        for res in results:
            file_name = res["file_name"]
            if file_name not in file_groups:
                file_groups[file_name] = []
            file_groups[file_name].append(res)

        for file_name, file_res in file_groups.items():
            f.write(f"## 文件：{file_name}\n")
            f.write(f"文件路径：{file_res[0]['file_path']}\n")
            f.write(f"章节：{file_res[0]['parent_chapter']}\n")
            f.write(f"结果条数：{len(file_res)}\n\n")

            for i, res in enumerate(file_res, 1):
                f.write(f"### 结果 {i}\n")
                f.write(f"- 违规句子：{res['violation_sentence']}\n")
                f.write(f"- 违规类型：{res['violation_type']}\n")
                f.write(f"- 置信度：{res['confidence']}\n")
                f.write(f"- 依据：{res['basis']}\n")
                f.write(f"- 修改建议：{res['suggestion']}\n")
                f.write(f"- 分析来源：{res['source']}\n\n")
    logger.info(f"✅ 违规报告TXT已保存：{report_path}")
