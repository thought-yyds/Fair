import argparse
import os
import re
import string
from typing import List, Tuple, Dict, Any

import pandas as pd

from langchain.schema import Document
from RAG.classifiers.bert_classifier import BertSentenceClassifier
from RAG.config.constants import (
	RULE_MAPPING,
	EMBEDDING_MODEL,
	STRUCTURED_CHUNKS_JSON_PATH,
	input_path,
)
from RAG.doc_utils.JsonLoader import load_structured_chunks_from_json, load_and_process_documents
from RAG.retrieval.vectorstore import build_vector_index
from RAG.retrieval.bm25 import build_bm25_retriever
from RAG.retrieval.hybrid import hybrid_retrieval
from RAG.utils.llm_intent import intent_translate


def _to_half_width(s: str) -> str:
	"""
	Convert full-width characters to half-width to reduce formatting mismatches.
	"""
	result_chars: List[str] = []
	for ch in s:
		code = ord(ch)
		# Full-width space
		if code == 0x3000:
			code = 0x20
		# Full-width char range
		elif 0xFF01 <= code <= 0xFF5E:
			code -= 0xFEE0
		result_chars.append(chr(code))
	return "".join(result_chars)


_CN_PUNCTUATION = "，。、“”‘’：；！？”（）—-、《》…【】〔〕·"
_PUNCT_TABLE = str.maketrans("", "", string.punctuation + _CN_PUNCTUATION)


def normalize_text(s: str) -> str:
	"""
	Normalization for robust substring match:
	- Lowercase
	- Convert full-width to half-width
	- Remove all whitespace
	- Remove common ASCII and Chinese punctuation
	"""
	if not s:
		return ""
	half = _to_half_width(s).lower()
	# Remove whitespace
	half = re.sub(r"\s+", "", half)
	# Strip punctuation
	return half.translate(_PUNCT_TABLE)


def load_or_build_corpus() -> Tuple[Any, Any]:
	"""
	Load structured chunks (or rebuild), then create vectordb and bm25 retriever.
	Returns:
	    (vectordb, bm25_retriever)
	"""
	force_recreate = False
	try:
		doc_chunks = load_structured_chunks_from_json(STRUCTURED_CHUNKS_JSON_PATH)
	except (FileNotFoundError, ValueError):
		doc_chunks = load_and_process_documents(input_dir=input_path, save_json_path=STRUCTURED_CHUNKS_JSON_PATH)
		force_recreate = True

	if not doc_chunks:
		raise RuntimeError("No valid document chunks for retrieval.")

	vectordb = build_vector_index(doc_chunks, force_recreate=force_recreate)
	bm25_retriever = build_bm25_retriever(doc_chunks)
	return vectordb, bm25_retriever


def evaluate_row(
	text: str,
	label_id: int,
	vectordb: Any,
	bm25_retriever: Any,
	k: int,
	bert_classifier: Any = None,
) -> Tuple[int, float, Dict[str, Any]]:
	"""
	Run retrieval for a single row and compute hit@K and reciprocal rank against RULE_MAPPING[label_id].
	Returns:
	    hit (0/1), reciprocal_rank, debug_info
	"""
	true_statement = RULE_MAPPING.get(int(label_id))
	if true_statement is None:
		return 0, 0.0, {"reason": "unknown_label"}

	intent = intent_translate(text)
	query = intent.get("normalized_query", text) or text
	results = hybrid_retrieval(
		vectordb=vectordb,
		bm25_retriever=bm25_retriever,
		query=query,
		intent_dict=intent,
		candidate_size=max(20, k),
		final_k=k,
	)

	# Optional: merge BERT-predicted RULE statement as an extra candidate (complementary to BM25+Vector)
	merged_results = list(results)
	try:
		if bert_classifier is not None:
			pred_label, pred_conf = bert_classifier.predict(text)
			if pred_label is not None:
				bert_stmt = RULE_MAPPING.get(int(pred_label))
				if isinstance(bert_stmt, str) and bert_stmt.strip():
					# de-duplicate by normalized content
					existing_norms = {normalize_text(d.page_content or "") for _, d in merged_results}
					if normalize_text(bert_stmt) not in existing_norms:
						bert_doc = Document(page_content=bert_stmt, metadata={"file_name": "BERT", "parent_chapter_title": "模型预测"})
						# append with a neutral score; evaluation仅依赖内容是否包含true_statement
						merged_results.append((1.0, bert_doc))
	except Exception:
		# 保守降级：任何异常都不影响原有评估路径
		pass

	hit = 0
	rr = 0.0
	rank = None
	norm_true = normalize_text(true_statement)
	for idx, (score, doc) in enumerate(merged_results, start=1):
		content = doc.page_content or ""
		if norm_true and norm_true in normalize_text(content):
			hit = 1
			rank = idx
			rr = 1.0 / float(idx)
			break

	debug_info = {
		"query": query,
		"true_statement": true_statement,
		"rank": rank,
		"topk": [
			{
				"rank": i + 1,
				"score": float(s),
				"source": d.metadata.get("file_name", "未知文件"),
				"chapter": d.metadata.get("parent_chapter_title", "未知章节"),
				"preview": (d.page_content or "")[:160],
			}
			for i, (s, d) in enumerate(merged_results)
		],
	}
	return hit, rr, debug_info


def main():
	parser = argparse.ArgumentParser(description="Retrieval evaluation on grp_test_54.xlsx")
	parser.add_argument("--file", type=str, default="/home/grp/disk1/Agent/grp_test_54.xlsx", help="Path to the Excel test file")
	parser.add_argument("--text_col", type=str, default="text", help="Column name for input text")
	parser.add_argument("--label_col", type=str, default="label", help="Column name for label id")
	parser.add_argument("--k", type=int, default=3, help="Top-K for retrieval")
	parser.add_argument("--limit", type=int, default=0, help="Limit number of rows (0 for all)")
	parser.add_argument("--show_errors", action="store_true", help="Print cases without hits")
	parser.add_argument("--disable_merge_bert", action="store_true", help="Disable merging BERT-predicted RULE statement into candidates")
	parser.add_argument("--hide_results", action="store_false", dest="show_results", default=False, help="Hide Top-K candidates output (default: show results)")
	args = parser.parse_args()

	if not os.path.exists(args.file):
		raise FileNotFoundError(f"Test file not found: {args.file}")

	df = pd.read_excel(args.file)
	if args.text_col not in df.columns or args.label_col not in df.columns:
		raise ValueError(f"Excel must contain columns: {args.text_col}, {args.label_col}")

	if args.limit and args.limit > 0:
		df = df.head(args.limit)

	vectordb, bm25_retriever = load_or_build_corpus()
	bert_classifier = BertSentenceClassifier() if not args.disable_merge_bert else None

	total = 0
	hits = 0
	sum_rr = 0.0
	errors: List[Dict[str, Any]] = []

	for _, row in df.iterrows():
		text = str(row[args.text_col]).strip()
		label_id = int(row[args.label_col])
		if not text:
			continue
		total += 1
		hit, rr, dbg = evaluate_row(text, label_id, vectordb, bm25_retriever, args.k, bert_classifier=bert_classifier)
		hits += hit
		sum_rr += rr

		if args.show_results:
			print("\nQuery result:")
			print(f"- text: {text[:120]}")
			print(f"  true: {dbg.get('true_statement')}")
			print(f"  query: {dbg.get('query')}")
			print(f"  rank: {dbg.get('rank')}")
			topk = dbg.get("topk") or []
			max_show = min(args.k, len(topk))
			if max_show:
				print(f"  top{max_show} candidates:")
				for i in range(max_show):
					item = topk[i]
					print(f"    #{item.get('rank')}: score={item.get('score'):.4f} source={item.get('source')} chapter={item.get('chapter')}")
					prev = item.get("preview") or ""
					if prev:
						prev_clean = prev.replace("\n", " ")[:200]
						print(f"      preview: {prev_clean}")

		if hit == 0:
			errors.append({"text": text[:120], **dbg})

	if total == 0:
		print("No valid rows to evaluate.")
		return

	hit_at_k = hits / total
	mrr = sum_rr / total
	accuracy = hit_at_k  # under single relevant-statement assumption, treat Hit@K as accuracy

	print(f"Samples: {total}")
	print(f"Top-K: {args.k}")
	print(f"Hit@K (Recall@K): {hit_at_k:.4f}")
	print(f"MRR: {mrr:.4f}")
	print(f"Accuracy: {accuracy:.4f}")

	if args.show_errors and errors:
		print("\nMissed cases (first 10):")
		for e in errors[:10]:
			print(f"- text: {e.get('text')}")
			print(f"  true: {e.get('true_statement')}")
			print(f"  query: {e.get('query')}")
			print(f"  rank: {e.get('rank')}")
			# Show top-K previews to understand near-misses
			topk = e.get("topk") or []
			max_show = min(5, len(topk))
			if max_show:
				print(f"  top{max_show} candidates:")
				for i in range(max_show):
					item = topk[i]
					print(f"    #{item.get('rank')}: score={item.get('score'):.4f} source={item.get('source')} chapter={item.get('chapter')}")
					prev = item.get("preview") or ""
					if prev:
						prev_clean = prev.replace("\n", " ")[:200]
						print(f"      preview: {prev_clean}")
			print("")


if __name__ == "__main__":
	main()


