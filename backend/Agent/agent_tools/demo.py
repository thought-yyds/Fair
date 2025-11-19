import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import logging
import numpy as np
from concurrent.futures import ThreadPoolExecutor  # 恢复并行依赖

# 向量存储 & 检索
import faiss
from langchain_community.vectorstores import FAISS as LangChainFAISS
from langchain_huggingface import HuggingFaceEmbeddings
from rank_bm25 import BM25Okapi
import jieba
from langchain.schema import Document

# 方舟API
from config.settings import get_settings
from API import LLMClient

# BERT 模型依赖（激活预测功能）
import torch
from transformers import BertTokenizer, BertForSequenceClassification

# ==============================================================================
# 配置区（适配环境+调试友好）
# ==============================================================================
MODEL_CACHE_DIR = "/home/grp/disk1/Huggface"
os.environ["TRANSFORMERS_CACHE"] = MODEL_CACHE_DIR
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

# 轻量 Embedding 模型
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DEVICE = "cuda:2" if torch.cuda.is_available() else "cpu"

# BERT 模型路径（激活预测）
BERT_MODEL_PATH = "/home/grp/disk1/Fair_detection/encapsulation/two_stage_model.pt"
BERT_TOKENIZER_PATH = "/home/grp/disk1/Agent/tokenizer"
BERT_CONFIDENCE_THRESHOLD = 0.05  # 降低阈值，保留更多结果（调试用）

# 违规规则映射（用于BERT结果解析）
RULE_MAPPING = {
    0: "不违规",
    1: "设置明显不必要或者超出实际需要的准入和退出条件，排斥或者限制经营者参与市场竞争",
    2: "没有法律、行政法规或者国务院规定依据，对不同所有制、地区、组织形式的经营者实施不合理的差别化待遇，设置不平等的市场准入和退出条件",
    3: "没有法律、行政法规或者国务院规定依据，以备案、登记、注册、目录、年检、年报、监制、认定、认证、认可、检验、监测、审定、指定、配号、复检、复审、换证、要求设立分支机构以及其他任何形式，设定或者变相设定市场准入障碍",
    4: "没有法律、行政法规或者国务院规定依据，对企业注销、破产、挂牌转让、搬迁转移等设定或者变相设定市场退出障碍",
    5: "以行政许可、行政检查、行政处罚、行政强制等方式，强制或者变相强制企业转让技术，设定或者变相设定市场准入和退出障碍",
    6: "在一般竞争性领域实施特许经营或者以特许经营为名增设行政许可",
    7: "未明确特许经营权期限或者未经法定程序延长特许经营权期限",
    8: "未依法采取招标、竞争性谈判等竞争方式，直接将特许经营权授予特定经营者",
    9: "设置歧视性条件，使经营者无法公平参与特许经营权竞争",
    10: "以明确要求、暗示、拒绝或者拖延行政审批、重复检查、不予接入平台或者网络、违法违规给予奖励补贴等方式，限定或者变相限定经营、购买、使用特定经营者提供的商品和服务",
    11: "在招标投标、政府采购中限定投标人所在地、所有制形式、组织形式，或者设定其他不合理的条件排斥或者限制经营者参与招标投标、政府采购活动",
    12: "没有法律、行政法规或者国务院规定依据，通过设置不合理的项目库、名录库、备选库、资格库等条件，排斥或限制潜在经营者提供商品和服务",
    13: "没有法律、行政法规或者国务院规定依据，增设行政审批事项，增加行政审批环节、条件和程序",
    14: "没有法律、行政法规或者国务院规定依据，设置具有行政审批性质的前置性备案程序",
    15: "不得对市场准入负面清单以外的行业、领域、业务等设置审批程序，主要指没有法律、行政法规或者国务院规定依据，采取禁止进入、限制市场主体资质、限制股权比例、限制经营范围和商业模式等方式，限制或者变相限制市场准入",
    16: "制定政府定价或者政府指导价时，对外地和进口同类商品、服务制定歧视性价格",
    17: "对相关商品、服务进行补贴时，对外地同类商品、服务，国际经贸协定允许外的进口同类商品以及我国作出国际承诺的进口同类服务不予补贴或者给予较低补贴",
    18: "对外地商品、服务规定与本地同类商品、服务不同的技术要求、检验标准，或者采取重复检验、重复认证等歧视性技术措施",
    19: "对进口商品规定与本地同类商品不同的技术要求、检验标准，或者采取重复检验、重复认证等歧视性技术措施",
    20: "没有法律、行政法规或者国务院规定依据，对进口服务规定与本地同类服务不同的技术要求、检验标准，或者采取重复检验、重复认证等歧视性技术措施",
    21: "设置专门针对外地和进口商品、服务的专营、专卖、审批、许可、备案，或者规定不同的条件、程序和期限等",
    22: "在道路、车站、港口、航空港或者本行政区域边界设置关卡，阻碍外地和进口商品、服务进入本地市场或者本地商品运出和服务输出",
    23: "通过软件或者互联网设置屏蔽以及采取其他手段，阻碍外地和进口商品、服务进入本地市场或者本地商品运出和服务输出",
    24: "不依法及时、有效、完整地发布招标信息",
    25: "直接规定外地经营者不能参与本地特定的招标投标活动",
    26: "对外地经营者设定歧视性的资质资格要求或者评标评审标准",
    27: "将经营者在本地区的业绩、所获得的奖项荣誉作为投标条件、加分条件、中标条件或者用于评价企业信用等级，限制或者变相限制外地经营者参加本地招标投标活动",
    28: "没有法律、行政法规或者国务院规定依据，要求经营者在本地注册设立分支机构，在本地拥有一定办公面积，在本地缴纳社会保险等，限制或者变相限制外地经营者参加本地招标投标活动",
    29: "通过设定与招标项目的具体特点和实际需要不相适应或者与合同履行无关的资格、技术和商务条件，限制或者变相限制外地经营者参加本地招标投标活动",
    30: "直接拒绝外地经营者在本地投资或者设立分支机构",
    31: "没有法律、行政法规或者国务院规定依据，对外地经营者在本地投资的规模、方式以及设立分支机构的地址、模式等进行限制",
    32: "没有法律、行政法规或者国务院规定依据，直接强制外地经营者在本地投资或者设立分支机构",
    33: "没有法律、行政法规或者国务院规定依据，将在本地投资或者设立分支机构作为参与本地招标投标、享受补贴和优惠政策等的必要条件，变相强制外地经营者在本地投资或者设立分支机构",
    34: "对外地经营者在本地的投资不给予与本地经营者同等的政策待遇",
    35: "对外地经营者在本地设立的分支机构在经营规模、经营方式、税费缴纳等方面规定与本地经营者不同的要求",
    36: "在节能环保、安全生产、健康卫生、工程质量、市场监管等方面，对外地经营者在本地设立的分支机构规定歧视性监管标准和要求",
    37: "没有法律、行政法规或者国务院规定依据，给予特定经营者财政奖励和补贴",
    38: "没有专门的税收法律、法规和国务院规定依据，给予特定经营者税收优惠政策",
    39: "没有法律、行政法规或者国务院规定依据，在土地、劳动力、资本、技术、数据等要素获取方面，给予特定经营者优惠政策",
    40: "没有法律、行政法规或者国务院规定依据，在环保标准、排污权限等方面给予特定经营者特殊待遇",
    41: "没有法律、行政法规或者国务院规定依据，对特定经营者减免、缓征或停征行政事业性收费、政府性基金、住房公积金等",
    42: "安排财政支出一般不得与特定经营者缴纳的税收或非税收入挂钩，主要指根据特定经营者缴纳的税收或者非税收入情况，采取列收列支或者违法违规采取先征后返、即征即退等形式，对特定经营者进行返还，或者给予特定经营者财政奖励或补贴、减免土地等自然资源有偿使用收入等优惠政策",
    43: "不得违法违规减免或者缓征特定经营者应当缴纳的社会保险费用，主要指没有法律、行政法规或者国务院规定依据，根据经营者规模、所有制形式、组织形式、地区等因素，减免或者缓征特定经营者需要缴纳的基本养老保险费、基本医疗保险费、失业保险费、工伤保险费、生育保险费等",
    44: "没有法律、行政法规依据或者经国务院批准，要求经营者交纳各类保证金",
    45: "限定只能以现金形式交纳投标保证金或履约保证金",
    46: "在经营者履行相关程序或者完成相关事项后，不依法退还经营者交纳的保证金及银行同期存款利息",
    47: "不得强制经营者从事《中华人民共和国反垄断法》禁止的垄断行为，主要指以行政命令、行政授权、行政指导等方式或者通过行业协会商会，强制、组织或者引导经营者达成垄断协议、滥用市场支配地位，以及实施具有或者可能具有排除、限制竞争效果的经营者集中等行为",
    48: "不得违法披露或者违法要求经营者披露生产经营敏感信息，为经营者实施垄断行为提供便利条件。生产经营敏感信息是指除依据法律、行政法规或者国务院规定需要公开之外，生产经营者未主动公开，通过公开渠道无法采集的生产经营数据。主要包括：拟定价格、成本、营业收入、利润、生产数量、销售数量、生产销售计划、进出口数量、经销商信息、终端客户信息等",
    49: "对实行政府指导价的商品、服务进行政府定价",
    50: "对不属于本级政府定价目录范围内的商品、服务制定政府定价或者政府指导价",
    51: "违反《中华人民共和国价格法》等法律法规采取价格干预措施",
    52: "制定公布商品和服务的统一执行价、参考价",
    53: "规定商品和服务的最高或者最低限价",
    54: "干预影响商品和服务价格水平的手续费、折扣或者其他费用"
}

# 文件路径（恢复结果保存路径）
input_path = "/home/grp/disk1/FCR-langchain/file"
persist_directory = "/home/grp/disk1/FCR-langchain/vectorstore"
STRUCTURED_CHUNKS_JSON_PATH = "/home/grp/disk1/FCR-langchain/structured_min_chunks_output.json"
VIOLATION_OUTPUT_DIR = "/home/grp/disk1/FCR-langchain/violation_results"  # 结果保存目录

# 检索/并行相关配置
LONG_CHAPTER_WARN_THRESHOLD = 3000
CHAPTER_BM25_THRESHOLD = 0.7
RETRIEVAL_CANDIDATE_SIZE = 20
RETRIEVAL_FINAL_K = 5
MAX_THREAD_WORKERS = 2  # 并行线程数（BERT+LLM各1个）

# 日志配置（显示更多细节）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 测试模式（纯文本输入测试）
TEST_DEMO = True


# ==============================================================================
# 1. BERT 分类器（激活预测，降低过滤阈值）
# ==============================================================================
class BertSentenceClassifier:
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self._load_model()

    def _load_model(self):
        if not BERT_MODEL_PATH:
            logger.warning("⚠️ BERT_MODEL_PATH 未配置，无法执行BERT预测")
            return
        try:
            # 加载Tokenizer
            self.tokenizer = BertTokenizer.from_pretrained(BERT_TOKENIZER_PATH)
            # 加载模型（CPU）
            try:
                self.model = torch.jit.load(BERT_MODEL_PATH, map_location="cpu")
            except Exception:
                self.model = torch.load(BERT_MODEL_PATH, map_location="cpu", weights_only=False)
            self.model.eval()
            logger.info(f"✅ BERT模型加载完成（设备：CPU，置信度阈值：{BERT_CONFIDENCE_THRESHOLD}）")
        except Exception as e:
            logger.error(f"❌ BERT模型加载失败：{str(e)}", exc_info=True)

    def predict(self, sentence: str) -> Tuple[Optional[int], Optional[float]]:
        """激活预测：保留label=0（不违规），降低置信度阈值"""
        if not self.model or not self.tokenizer:
            logger.warning("⚠️ BERT模型未加载，跳过预测")
            return None, None
        try:
            # Tokenize
            inputs = self.tokenizer(
                sentence,
                return_tensors="pt",
                padding="max_length",
                truncation=True,
                max_length=512,
                return_token_type_ids=False
            )
            inputs = {k: v.to("cpu") for k, v in inputs.items()}

            # 预测（禁用梯度）
            with torch.no_grad():
                predicted_label, final_probability = self.model(**inputs)  # 适配TwoStageModel输出

            # 过滤极低置信度（保留label=0）
            if final_probability < BERT_CONFIDENCE_THRESHOLD:
                logger.debug(f"⚠️ BERT低置信度跳过（句子：{sentence[:30]}...，置信度：{final_probability:.3f}）")
                return None, None

            logger.debug(
                f"✅ BERT预测结果（句子：{sentence[:30]}...）：label={predicted_label}，置信度={final_probability:.3f}")
            return predicted_label, final_probability

        except Exception as e:
            logger.error(f"❌ BERT预测失败（句子：{sentence[:30]}...）：{str(e)}", exc_info=True)
            return None, None


# ==============================================================================
# 2. LLM 核心：意图转译+段落级判断（恢复完整功能）
# ==============================================================================
def simple_llm_call(prompt: str) -> str:
    """LLM API调用（支持意图转译+段落判断）"""
    try:
        client = LLMClient()
        response = client.simple_chat(prompt)
        logger.debug(f"LLM调用结果：{response[:100]}...")
        return response or ""
    except Exception as e:
        logger.error(f"❌ LLM API调用失败：{str(e)}", exc_info=True)
        return ""


def intent_translate(user_query: str) -> dict:
    """意图转译：保留is_violation_related字段，用于检索判断"""
    prompt = f"""
                用户查询：{user_query}
                作为“公平竞争审查RAG系统”意图助手，仅输出JSON（无其他文字，无注释）：
                {{
                  "need_retrieval": "是/否",  // 无关问题填“否”，需查条款填“是”
                  "is_violation_related": "是/否",  // 涉及违规判断填“是”，仅查定义填“否”
                  "retrieval_type": "内容检索/违规审查/无",  // 查条款=内容检索；判违规=违规审查
                  "retrieval_query": "检索指令（无需检索则填空）",  // 精准检索语句
                  "need_chapter_filter": "是/否",  // 能明确章节（如“审查标准”）填“是”
                  "target_chapters": ["章节名1"]  // 无需过滤则填空列表
                }}
                // 规则：
                // 1. 问“某行为是否违规”→ is_violation_related=是
                // 2. 问“审查标准定义”→ is_violation_related=否
                """
    prompt = prompt.strip()

    try:
        response = simple_llm_call(prompt)
        parsed = json.loads(response.strip())
        # 格式容错
        if not isinstance(parsed, dict):
            parsed = {
                "need_retrieval": "是",
                "is_violation_related": "否",
                "retrieval_type": "内容检索",
                "retrieval_query": user_query,
                "need_chapter_filter": "否",
                "target_chapters": []
            }
        # 补全缺失字段
        intent_dict = {
            "need_retrieval": parsed.get("need_retrieval", "是"),
            "is_violation_related": parsed.get("is_violation_related", "否"),
            "retrieval_type": parsed.get("retrieval_type", "内容检索"),
            "retrieval_query": parsed.get("retrieval_query", user_query).strip() or user_query,
            "need_chapter_filter": parsed.get("need_chapter_filter", "否"),
            "target_chapters": parsed.get("target_chapters", []) if isinstance(parsed.get("target_chapters"),
                                                                               list) else []
        }
        logger.info(f"✅ 意图转译结果：{json.dumps(intent_dict, ensure_ascii=False)}")
        return intent_dict
    except json.JSONDecodeError as e:
        logger.error(f"❌ 意图输出非JSON（响应：{response[:100]}...）：{str(e)}")
        return {
            "need_retrieval": "是",
            "is_violation_related": "否",
            "retrieval_type": "内容检索",
            "retrieval_query": user_query,
            "need_chapter_filter": "否",
            "target_chapters": []
        }
    except Exception as e:
        logger.error(f"❌ 意图转译失败：{str(e)}", exc_info=True)
        return {
            "need_retrieval": "是",
            "is_violation_related": "否",
            "retrieval_type": "内容检索",
            "retrieval_query": user_query,
            "need_chapter_filter": "否",
            "target_chapters": []
        }

class CustomBM25Retriever:
    """BM25检索器（支持章节过滤）"""

    def __init__(self, docs: List[Dict], bm25_model: BM25Okapi):
        self.bm25 = bm25_model
        self.docs = docs
        self._all_chapters = [doc["metadata"]["parent_chapter_title"] for doc in docs]
        self._chapter_bm25 = self._build_chapter_bm25()

    def _build_chapter_bm25(self) -> BM25Okapi:
        """构建章节级BM25"""
        tokenized_chapters = [list(jieba.cut(chap)) for chap in self._all_chapters]
        return BM25Okapi(tokenized_chapters, k1=1.2, b=0.4)

    def retrieve(self, query: str, top_k: int = 50) -> List[Tuple[float, Document]]:
        """基础BM25检索"""
        tokenized_query = list(jieba.cut(query))
        scores = self.bm25.get_scores(tokenized_query)
        results = [
            (scores[i], Document(
                page_content=self.docs[i]["page_content"],
                metadata=self.docs[i]["metadata"]
            )) for i in range(len(self.docs)) if scores[i] > 0
        ]
        results.sort(key=lambda x: x[0], reverse=True)
        return results[:top_k]

    def retrieve_with_chapter_filter(self, query: str, target_chapters: List[str], top_k: int = 50) -> List[
        Tuple[float, Document]]:
        """带章节过滤的BM25检索"""
        # 匹配相关章节
        tokenized_chap_query = list(jieba.cut(" ".join(target_chapters)))
        chap_scores = self._chapter_bm25.get_scores(tokenized_chap_query)
        relevant_indices = [i for i, score in enumerate(chap_scores) if score > CHAPTER_BM25_THRESHOLD]
        if not relevant_indices:
            logger.warning("⚠️ 无匹配章节，执行基础BM25检索")
            return self.retrieve(query, top_k)

        # 过滤文档并检索
        filtered_docs = [self.docs[i] for i in relevant_indices]
        filtered_texts = [doc["page_content"] for doc in filtered_docs]
        tokenized_texts = [list(jieba.cut(text)) for text in filtered_texts]
        content_bm25 = BM25Okapi(tokenized_texts)

        tokenized_content_query = list(jieba.cut(query))
        content_scores = content_bm25.get_scores(tokenized_content_query)

        results = [
            (content_scores[i], Document(
                page_content=filtered_docs[i]["page_content"],
                metadata=filtered_docs[i]["metadata"]
            )) for i in range(len(filtered_docs)) if content_scores[i] > 0
        ]
        results.sort(key=lambda x: x[0], reverse=True)
        return results[:top_k]


def build_bm25_retriever(documents: List[Dict]) -> CustomBM25Retriever:
    """构建BM25检索器"""
    texts = [doc["page_content"] for doc in documents if doc["page_content"].strip()]
    if not texts:
        raise ValueError("❌ 无有效文本内容，无法构建BM25检索器")
    tokenized_corpus = [list(jieba.cut(text)) for text in texts]
    bm25_model = BM25Okapi(tokenized_corpus)
    return CustomBM25Retriever(docs=documents, bm25_model=bm25_model)


def llm_paragraph_judge(
        paragraph: str,
        doc_metadata: Dict[str, Any],
        vectordb: LangChainFAISS,
        bm25_retriever: CustomBM25Retriever
) -> List[Dict[str, Any]]:
    """恢复LLM段落级判断：结合检索结果分析违规"""
    results = []
    try:
        # 步骤1：生成检索意图
        intent_query = f"分析段落是否存在公平竞争违规：{paragraph[:200]}..."
        intent_dict = intent_translate(intent_query)
        if intent_dict.get("need_retrieval") == "否":
            retrieval_query = intent_query
            logger.debug(f"⚠️ LLM判断无需检索，直接分析段落：{paragraph[:50]}...")
        else:
            retrieval_query = intent_dict["retrieval_query"]
            logger.debug(f"✅ LLM生成检索指令：{retrieval_query}")

        # 步骤2：检索相关条款
        basis_list = hybrid_retrieval(
            vectordb=vectordb,
            bm25_retriever=bm25_retriever,
            query=retrieval_query,
            intent_dict=intent_dict,
            candidate_size=RETRIEVAL_CANDIDATE_SIZE,
            final_k=RETRIEVAL_FINAL_K
        )

        # 步骤3：构建LLM Prompt
        basis_text = ""
        for i, (score, doc) in enumerate(basis_list, 1):
            source = doc.metadata.get("file_name", "未知文件")
            chapter = doc.metadata.get("parent_chapter_title", "未知章节")
            content = doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
            basis_text += f"条款{i}（来源：{source} - {chapter}，相似度：{score:.3f}）：{content}\n"

        llm_prompt = f"""
                    你是公平竞争审查专家，基于以下信息分析段落违规情况，仅输出JSON数组（无多余文字）：
                    1. 提取段落中违规句子（无违规则返回空数组）；
                    2. 违规类型匹配RULE_MAPPING（如“限定只能以现金形式交纳投标保证金”）；
                    3. 依据必须引用参考条款；
                    4. 建议需具体可落地。

                    【待分析段落】
                    {paragraph}

                    【参考条款】
                    {basis_text if basis_text else "无相关条款"}

                    【输出格式】
                    [
                        {{
                            "violation_sentence": "完整违规句子",
                            "violation_type": "违规类型名称",
                            "confidence": 0.0-1.0,
                            "basis": "引用条款内容",
                            "suggestion": "修改建议",
                            "source": "LLM段落级分析（火山引擎Ark）"
                        }}
                    ]
                    """
        llm_prompt = llm_prompt.strip()

        # 步骤4：调用LLM并解析结果
        response = simple_llm_call(llm_prompt)
        parsed = json.loads(response.strip())
        llm_results = parsed if isinstance(parsed, list) else [parsed] if isinstance(parsed, dict) else []

        # 步骤5：补充元数据
        for res in llm_results:
            results.append({
                "violation_sentence": res.get("violation_sentence", ""),
                "violation_type": res.get("violation_type", "未明确违规类型"),
                "confidence": round(res.get("confidence", 0.0), 3),
                "basis": res.get("basis", "无明确依据"),
                "suggestion": res.get("suggestion", "无具体建议"),
                "source": res.get("source", "LLM段落级分析（火山引擎Ark）"),
                "file_name": doc_metadata.get("file_name", "未知文件"),
                "file_path": doc_metadata.get("file_path", "未知路径"),
                "parent_chapter": doc_metadata.get("parent_chapter_title", "未知章节"),
                "paragraph_context": paragraph[:100] + "..."
            })
        logger.info(f"✅ LLM段落分析完成（段落：{paragraph[:50]}...），发现 {len(results)} 条违规")
    except Exception as e:
        logger.error(f"❌ LLM段落分析失败（段落：{paragraph[:50]}...）：{str(e)}", exc_info=True)
    return results


# ==============================================================================
# 3. 并行处理（恢复BERT+LLM双线程，确保等待完成）
# ==============================================================================
def parallel_process_document(
        document_chunks: List[Dict],
        bert_classifier: BertSentenceClassifier,
        vectordb: LangChainFAISS,
        bm25_retriever: CustomBM25Retriever
) -> List[Dict[str, Any]]:
    """并行执行BERT句子级+LLM段落级分析，等待双线程完成"""
    all_bert_results = []
    all_llm_results = []

    # 预处理输入：拆分句子+整理元数据
    task_data = []
    for chunk in document_chunks:
        paragraph = chunk.get("page_content", "").strip()
        if not paragraph:
            logger.warning("⚠️ 空段落跳过")
            continue
        # 拆分句子（过滤短句）
        sentences = [s.strip() for s in re.split(r'[。；;！!？?]', paragraph) if len(s.strip()) > 5]
        task_data.append({
            "paragraph": paragraph,
            "sentences": sentences,
            "metadata": chunk.get("metadata", {})
        })
    if not task_data:
        logger.warning("❌ 无有效任务数据，并行处理终止")
        return []

    # 定义BERT处理函数
    def process_bert():
        nonlocal all_bert_results
        logger.info(f"✅ BERT处理启动，共 {len(task_data)} 个段落")
        for data in task_data:
            for sent in data["sentences"]:
                pred_id, confidence = bert_classifier.predict(sent)
                if pred_id is None or confidence is None:
                    continue
                # 解析违规类型
                violation_type = RULE_MAPPING.get(pred_id, f"未知类型（ID：{pred_id}）")
                all_bert_results.append({
                    "violation_sentence": sent + "。" if not sent.endswith(("。", "！", "？")) else sent,
                    "violation_type": violation_type,
                    "confidence": round(confidence, 3),
                    "basis": f"BERT模型预测（类别ID：{pred_id}，置信度：{confidence:.3f}）",
                    "suggestion": f"参考「{violation_type}」相关条款进一步核查",
                    "source": "BERT句子级分析",
                    "file_name": data["metadata"].get("file_name", "未知文件"),
                    "file_path": data["metadata"].get("file_path", "未知路径"),
                    "parent_chapter": data["metadata"].get("parent_chapter_title", "未知章节")
                })
        logger.info(f"✅ BERT处理完成，共发现 {len(all_bert_results)} 条结果")

    # 定义LLM处理函数
    def process_llm():
        nonlocal all_llm_results
        logger.info(f"✅ LLM处理启动，共 {len(task_data)} 个段落")
        for data in task_data:
            llm_res = llm_paragraph_judge(
                paragraph=data["paragraph"],
                doc_metadata=data["metadata"],
                vectordb=vectordb,
                bm25_retriever=bm25_retriever
            )
            all_llm_results.extend(llm_res)
        logger.info(f"✅ LLM处理完成，共发现 {len(all_llm_results)} 条结果")

    # 启动并行线程，等待完成
    with ThreadPoolExecutor(max_workers=MAX_THREAD_WORKERS) as executor:
        futures = [
            executor.submit(process_bert),
            executor.submit(process_llm)
        ]
        # 等待两个任务都完成（避免主线程提前退出）
        for future in futures:
            future.result()

    # 结果去重（按“句子+违规类型”去重）
    merged_results = []
    seen_keys = set()
    for res in all_bert_results + all_llm_results:
        clean_sent = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', res["violation_sentence"])
        clean_type = res["violation_type"].strip()
        key = (clean_sent, clean_type)
        if key not in seen_keys:
            seen_keys.add(key)
            merged_results.append(res)

    logger.info(f"✅ 并行处理结果融合完成，最终保留 {len(merged_results)} 条不重复结果")
    return merged_results


# ==============================================================================
# 4. 结果保存（恢复完整保存功能）
# ==============================================================================
def save_violation_results(results: List[Dict[str, Any]], output_dir: str = VIOLATION_OUTPUT_DIR):
    """保存违规结果为JSON和TXT报告"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # 保存JSON（结构化数据）
    json_path = os.path.join(output_dir, f"violation_results_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ 违规结果JSON已保存：{json_path}")

    # 保存TXT报告（人类可读）
    report_path = os.path.join(output_dir, f"violation_report_{timestamp}.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# 公平竞争审查违规分析报告\n")
        f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总结果条数：{len(results)}\n")
        f.write(f"分析来源：BERT句子级分析 + LLM段落级分析\n\n")

        # 按文件分组
        file_groups = {}
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


# ==============================================================================
# 5. 文档处理：适配纯文本输入（自动补元数据）
# ==============================================================================
def extract_policy_type(text: str) -> str:
    """政策类型判断（用于元数据）"""
    if "奖励" in text or "补贴" in text:
        return "财政奖励"
    elif "准入" in text or "门槛" in text:
        return "市场准入"
    elif "竞争" in text or "审查" in text:
        return "公平竞争审查"
    else:
        return "用户输入内容"

def get_single_sentence_input(sentence: Optional[str] = None) -> List[Dict]:
    """
    单句测试专用：只接收一个句子，元数据极简
    sentence: 可选参数，便于测试时直接传入句子
    """
    if sentence:
        user_input = sentence
    else:
        if TEST_DEMO:
            user_input = "投标保证金应以现金形式交纳，不接受保函或其他形式。"
            logger.info(f"🧪 单句测试模式：使用预设输入：{user_input}")
        else:
            user_input = input("请输入要测试的单个句子：").strip()
            if not user_input:
                logger.error("❌ 输入为空，程序终止")
                exit()

    # 元数据极简：只保留来源标记
    return [
        {
            "page_content": user_input,
            "metadata": {
                "source": "user_single_sentence"  # 明确标记这是单句输入
            }
        }
    ]

def get_document_input() -> List[Dict]:
    """接收纯文本输入，自动填充元数据"""
    if TEST_DEMO:
        # 测试模式：预设输入
        user_input = "投标保证金应以现金形式交纳，不接受保函或其他形式。"
        logger.info(f"🧪 测试模式：使用预设输入：{user_input}")
    else:
        # 正常模式：命令行输入
        user_input = input("请输入要分析的句子/段落：").strip()
        if not user_input:
            logger.error("❌ 输入为空，程序终止")
            exit()

    # 自动补元数据
    return [
        {
            "page_content": user_input,
            "metadata": {
                "file_name": "用户纯文本输入",
                "file_path": "无本地文件路径",
                "parent_chapter_title": "用户输入内容",
                "policy_type": extract_policy_type(user_input),
                "input_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    ]


def load_and_process_documents(input_dir: str, save_json_path: str) -> List[Dict]:
    """加载本地文档（用于构建检索库）"""
    from data_process.process_document import PolicyStructurizeAPI  # 延迟导入
    logger.info(f"📄 开始处理本地文档：{input_dir}")
    struct_api = PolicyStructurizeAPI(long_chapter_warn_threshold=LONG_CHAPTER_WARN_THRESHOLD)

    doc_paths = list(Path(input_dir).glob("*.docx"))
    if not doc_paths:
        raise FileNotFoundError(f"❌ 目录 {input_dir} 下无docx文档")

    all_chunks = []
    for doc_path in doc_paths:
        doc_name = doc_path.name
        logger.info(f"🔍 处理文档：{doc_name}")
        doc_chunks = struct_api.process_document(str(doc_path), doc_name)
        if not doc_chunks:
            logger.warning(f"⚠️ 文档 {doc_name} 无有效分块，跳过")
            continue
        # 补充元数据
        for chunk in doc_chunks:
            chunk["metadata"]["file_path"] = str(doc_path)
            chunk["metadata"]["file_name"] = doc_name
            chunk["metadata"]["policy_type"] = extract_policy_type(chunk["page_content"])
        all_chunks.extend(doc_chunks)

    # 保存分块到JSON
    with open(save_json_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ 本地文档分块保存至：{save_json_path}（共 {len(all_chunks)} 个分块）")
    return all_chunks


def load_structured_chunks_from_json(json_path: str) -> List[Dict]:
    """从JSON加载文档分块（构建检索库用）"""
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"❌ JSON文件不存在：{json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    # 元数据容错
    for chunk in chunks:
        chunk.setdefault("page_content", "")
        chunk.setdefault("metadata", {})
        chunk["metadata"].setdefault("file_name", "未知文件")
        chunk["metadata"].setdefault("file_path", "未知路径")
        chunk["metadata"].setdefault("parent_chapter_title", "未知章节")
        chunk["metadata"].setdefault("policy_type", "其他政策")
    return chunks


# ==============================================================================
# 6. 检索核心：FAISS+BM25混合检索（保留完整功能）
# ==============================================================================
def build_vector_index(documents: List[Dict], force_recreate=False) -> LangChainFAISS:
    """构建FAISS向量检索库"""
    model_kwargs = {"device": EMBEDDING_DEVICE}
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs=model_kwargs,
        encode_kwargs={"normalize_embeddings": True}
    )

    faiss_index_path = os.path.join(persist_directory, "faiss_index")
    # 重建索引（如果需要）
    if force_recreate or not (os.path.exists(faiss_index_path) and os.listdir(faiss_index_path)):
        logger.info(f"🔄 强制重建FAISS索引（embedding模型：{EMBEDDING_MODEL}）...")
        if os.path.exists(faiss_index_path):
            import shutil
            logger.info(f"🗑️ 删除旧索引：{faiss_index_path}")
            shutil.rmtree(faiss_index_path)
        os.makedirs(faiss_index_path, exist_ok=True)

        # 转换为LangChain Document
        langchain_docs = [
            Document(page_content=doc["page_content"], metadata=doc["metadata"])
            for doc in documents if doc["page_content"].strip()
        ]
        if not langchain_docs:
            raise ValueError("❌ 无有效文档内容，无法构建向量索引")

        vectordb = LangChainFAISS.from_documents(langchain_docs, embeddings)
        vectordb.save_local(faiss_index_path)
        logger.info(f"✅ 新建FAISS索引：{faiss_index_path}（共 {len(langchain_docs)} 个文档）")
    else:
        vectordb = LangChainFAISS.load_local(
            faiss_index_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
        logger.info(f"✅ 加载已有FAISS索引：{faiss_index_path}")
    return vectordb

def hybrid_retrieval(
        vectordb: LangChainFAISS,
        bm25_retriever: CustomBM25Retriever,
        query: str,
        intent_dict: dict,
        candidate_size: int = 20,
        final_k: int = 10,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5
) -> List[Tuple[float, Document]]:
    """混合检索（FAISS+BM25）"""
    candidate_docs = {}

    # 1. FAISS向量检索
    try:
        vector_results = vectordb.similarity_search_with_score(query, k=candidate_size)
        for doc, distance in vector_results:
            similarity_score = 1.0 / (1.0 + distance)  # 距离转相似度
            doc_id = hash(doc.page_content)
            candidate_docs[doc_id] = {
                "doc": doc,
                "vector_score": similarity_score,
                "bm25_score": 0
            }
        logger.debug(f"✅ FAISS检索到 {len(vector_results)} 条候选结果")
    except Exception as e:
        logger.error(f"❌ FAISS检索失败：{str(e)}", exc_info=True)

    # 2. BM25检索（支持章节过滤）
    try:
        need_chapter_filter = intent_dict.get("need_chapter_filter") == "是"
        target_chapters = intent_dict.get("target_chapters", [])
        if need_chapter_filter and target_chapters:
            bm25_results = bm25_retriever.retrieve_with_chapter_filter(
                query=query, target_chapters=target_chapters, top_k=candidate_size
            )
        else:
            bm25_results = bm25_retriever.retrieve(query=query, top_k=candidate_size)

        for score, doc in bm25_results:
            doc_id = hash(doc.page_content)
            if doc_id in candidate_docs:
                candidate_docs[doc_id]["bm25_score"] = score
            else:
                if score > 0:
                    candidate_docs[doc_id] = {
                        "doc": doc,
                        "vector_score": 0,
                        "bm25_score": score
                    }
        logger.debug(f"✅ BM25检索到 {len(bm25_results)} 条候选结果")
    except Exception as e:
        logger.error(f"❌ BM25检索失败：{str(e)}", exc_info=True)

    # 3. 综合得分排序
    if not candidate_docs:
        logger.warning("❌ 混合检索无候选结果")
        return []

    # 得分归一化
    max_vector = max([d["vector_score"] for d in candidate_docs.values()], default=1)
    max_bm25 = max([d["bm25_score"] for d in candidate_docs.values()], default=1)

    reranked = []
    for doc_item in candidate_docs.values():
        norm_vector = doc_item["vector_score"] / max_vector if max_vector != 0 else 0
        norm_bm25 = doc_item["bm25_score"] / max_bm25 if max_bm25 != 0 else 0
        combined_score = (norm_vector * vector_weight) + (norm_bm25 * bm25_weight)
        reranked.append((combined_score, doc_item["doc"]))

    # 取Top N
    reranked.sort(key=lambda x: x[0], reverse=True)
    final_results = reranked[:final_k]
    logger.info(f"✅ 混合检索完成，返回Top {len(final_results)} 结果")
    return final_results


# ==============================================================================
# 7. 主函数（完整流程：输入→意图→检索→并行→保存）
# ==============================================================================
def main():
    FORCE_RECREATE_VECTOR_INDEX = True  # 强制重建索引，解决维度不匹配问题

    try:
        logger.info("=" * 60)
        logger.info("公平竞争审查全流程（纯文本输入+并行分析+结果保存）")
        logger.info("=" * 60)

        # 步骤1：初始化核心组件
        logger.info("[1/6] 初始化LLM客户端...")
        # 测试LLM连接
        test_response = simple_llm_call("测试连接：返回'LLM_OK'")
        if "LLM_OK" not in test_response:
            logger.warning("⚠️ LLM连接测试异常，可能影响后续分析")
        else:
            logger.info("✅ LLM客户端初始化完成")

        logger.info("[2/6] 初始化BERT分类器...")
        bert_classifier = BertSentenceClassifier()

        # 步骤2：加载检索库（本地文档分块）
        logger.info("[3/6] 加载检索库文档分块...")
        try:
            doc_chunks = load_structured_chunks_from_json(STRUCTURED_CHUNKS_JSON_PATH)
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"⚠️ 从JSON加载失败：{str(e)}，将重新处理本地文档")
            doc_chunks = load_and_process_documents(
                input_dir=input_path,
                save_json_path=STRUCTURED_CHUNKS_JSON_PATH
            )
            FORCE_RECREATE_VECTOR_INDEX = True

        if not doc_chunks:
            logger.error("❌ 无有效文档分块，程序终止")
            return
        logger.info(f"✅ 加载文档分块 {len(doc_chunks)} 个")


        # 步骤3：构建检索组件（FAISS+BM25）
        logger.info("[4/6] 构建检索组件...")
        logger.info(f"🔧 使用embedding模型：{EMBEDDING_MODEL}，强制重建：{FORCE_RECREATE_VECTOR_INDEX}")
        vectordb = build_vector_index(doc_chunks, force_recreate=FORCE_RECREATE_VECTOR_INDEX)
        bm25_retriever = build_bm25_retriever(doc_chunks)
        logger.info("✅ 检索组件（FAISS+BM25）构建完成")

        text = "参与评优评奖企业需要在本地落户"
        # 步骤4：接收用户纯文本输入
        logger.info("[5/6] 接收用户输入并执行并行分析...")
        user_input_chunks = get_single_sentence_input(text)
        user_text = user_input_chunks[0]["page_content"]

        # 步骤5：意图判断+检索（可选，用于LLM分析依据）
        intent_dict = intent_translate(user_text)
        if intent_dict.get("need_retrieval") == "是" and intent_dict.get("is_violation_related") == "是":
            logger.info(f"🔍 执行违规相关检索（检索指令：{intent_dict['retrieval_query']}）")
            retrieval_results = hybrid_retrieval(
                vectordb=vectordb,
                bm25_retriever=bm25_retriever,
                query=intent_dict["retrieval_query"],
                intent_dict=intent_dict
            )
            # 打印检索结果（参考用）
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



        # 步骤6：并行分析（BERT+LLM）+ 结果保存
        logger.info("🚀 启动BERT+LLM并行分析...")
        violation_results = parallel_process_document(
            document_chunks=user_input_chunks,
            bert_classifier=bert_classifier,
            vectordb=vectordb,
            bm25_retriever=bm25_retriever
        )

        # 保存结果
        if violation_results:
            save_violation_results(violation_results)
            logger.info(f"🎉 全流程完成！共发现 {len(violation_results)} 条结果，已保存至 {VIOLATION_OUTPUT_DIR}")
        else:
            logger.info("🎉 全流程完成！未发现违规结果")

    except Exception as e:
        logger.error(f"❌ 程序执行失败：{str(e)}", exc_info=True)



if __name__ == "__main__":
    main()