import logging
from typing import Tuple, Optional

import torch
from transformers import BertTokenizer, BertForSequenceClassification  # type: ignore

from RAG.config.constants import (
    BERT_MODEL_PATH,
    BERT_TOKENIZER_PATH,
    BERT_CONFIDENCE_THRESHOLD,
)

logger = logging.getLogger(__name__)


class BertSentenceClassifier:
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        if not BERT_MODEL_PATH:
            logger.warning("⚠️ BERT_MODEL_PATH 未配置，无法执行BERT预测")
            return
        try:
            self.tokenizer = BertTokenizer.from_pretrained(BERT_TOKENIZER_PATH)
            try:
                self.model = torch.jit.load(BERT_MODEL_PATH, map_location="cpu")
            except Exception:
                self.model = torch.load(BERT_MODEL_PATH, map_location="cpu", weights_only=False)
            self.model.eval()
            logger.info(
                f"✅ BERT模型加载完成（设备：CPU，置信度阈值：{BERT_CONFIDENCE_THRESHOLD}）"
            )
        except Exception as e:
            logger.error(f"❌ BERT模型加载失败：{str(e)}", exc_info=True)

    def predict(self, sentence: str) -> Tuple[Optional[int], Optional[float]]:
        if not self.model or not self.tokenizer:
            logger.warning("⚠️ BERT模型未加载，跳过预测")
            return None, None
        try:
            inputs = self.tokenizer(
                sentence,
                return_tensors="pt",
                padding="max_length",
                truncation=True,
                max_length=512,
                return_token_type_ids=False,
            )
            inputs = {k: v.to("cpu") for k, v in inputs.items()}

            with torch.no_grad():
                predicted_label, final_probability = self.model(**inputs)

            if final_probability < BERT_CONFIDENCE_THRESHOLD:
                logger.debug(
                    f"⚠️ BERT低置信度跳过（句子：{sentence[:30]}...，置信度：{final_probability:.3f}）"
                )
                return None, None

            logger.debug(
                f"✅ BERT预测结果（句子：{sentence[:30]}...）：label={predicted_label}，置信度={final_probability:.3f}"
            )
            return predicted_label, final_probability
        except Exception as e:
            logger.error(
                f"❌ BERT预测失败（句子：{sentence[:30]}...）：{str(e)}", exc_info=True
            )
            return None, None


if __name__ == "__main__":
    # 配置日志（让测试时能看到详细输出）
    logging.basicConfig(
        level=logging.INFO,  # 日志级别：INFO（显示加载状态、预测结果）
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 1. 初始化分类器（自动加载模型）
    classifier = BertSentenceClassifier()

    # 2. 测试用例（根据你的模型分类任务调整，比如情感分类、意图识别等）
    test_sentences = [
        '今天天气真好',
        '申请享受本地政府补贴的公司需要在本地拥有独自分公司或在本地落户',
    ]

    # 3. 批量测试并输出结果
    print("\n" + "=" * 50 + " BERT分类测试开始 " + "=" * 50 + "\n")
    for idx, sentence in enumerate(test_sentences, 1):
        print(f"\n【测试用例 {idx}】：{sentence}")
        label, confidence = classifier.predict(sentence)
        if label is not None and confidence is not None:
            print(f"预测结果：标签={label}，置信度={confidence:.3f}")
        else:
            print(f"预测结果：无有效结果（模型未加载/置信度不足/输入异常）")

    print("\n" + "=" * 50 + " BERT分类测试结束 " + "=" * 50 + "\n")