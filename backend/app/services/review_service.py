from sqlalchemy.orm import Session
from datetime import datetime
from app.models import db_models  # 统一导入数据库模型
from app.utils.helpers import calculate_risk_level
from app.config import settings
import torch
from transformers import BertTokenizer


# 全局加载AI模型和分词器（避免重复加载，节省资源）
def load_ai_model():
    """加载AI审查模型和分词器（首次调用时加载）"""
    global model, tokenizer, device
    try:
        # 设备配置（GPU优先）
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 加载模型（替换为你的模型路径）
        if not settings.MODEL_PATH.exists():
            raise Exception(f"模型文件不存在：{settings.MODEL_PATH}")
        model = torch.jit.load(str(settings.MODEL_PATH)).to(device)
        model.eval()  # 推理模式

        # 加载分词器（替换为你的分词器路径）
        if not settings.TOKENIZER_PATH.exists():
            raise Exception(f"分词器文件夹不存在：{settings.TOKENIZER_PATH}")
        tokenizer = BertTokenizer.from_pretrained(
            str(settings.TOKENIZER_PATH),
            clean_up_tokenization_spaces=True
        )

        print(f"AI模型加载成功（设备：{device}）")
    except Exception as e:
        raise Exception(f"AI模型加载失败：{str(e)}")


# 首次导入时加载模型
try:
    model = None
    tokenizer = None
    device = None
    load_ai_model()
except Exception as e:
    print(f"模型加载警告：{str(e)}，后续审查会失败，请检查模型路径")


def start_review_task(article_id: int, db: Session):
    """
    审查任务核心逻辑（后台运行）：
    1. 逐句调用AI模型判断是否违规（输出1~54标签，对应Annotation表id）
    2. 查数据库Annotation表获取对应违规内容，关联句子
    3. 按步骤更新审查进度（每句拆4步，进度更平滑）
    4. 计算风险等级并标记审查完成
    """
    global model, tokenizer, device
    try:
        # 1. 验证模型是否已加载
        if model is None or tokenizer is None:
            raise Exception("AI模型未加载，无法进行审查")

        # 2. 查询文档和句子
        article = db.query(db_models.Article).filter(db_models.Article.id == article_id).first()
        if not article:
            raise Exception(f"文档ID {article_id} 不存在")

        sentences = db.query(db_models.Sentence).filter(db_models.Sentence.article_id == article_id).all()
        if not sentences:
            # 无句子可审查：直接标记为无风险
            article.status = "已审查"
            article.review_progress = 100
            article.risk_level = "无风险"
            article.review_time = datetime.utcnow()
            db.commit()
            return

        total_sentences = len(sentences)
        violation_count = 0  # 违规句子数量

        # -------------------------- 关键：拆分步骤计算进度 --------------------------
        steps_per_sentence = 4  # 每句拆4步：分词→预测→关联标注→提交
        total_steps = total_sentences * steps_per_sentence  # 总步骤数（进度粒度=100/total_steps）
        current_step = 0  # 当前完成的总步骤数

        # 3. 逐句审查（拆分为4步，每步更新进度）
        for sentence in sentences:
            try:
                # -------------------------- 步骤1：分词处理（更新进度） --------------------------
                encoding = tokenizer(
                    sentence.content,
                    truncation=True,
                    max_length=512,
                    padding="max_length",
                    return_attention_mask=True,
                    return_tensors="pt"
                )
                input_ids = encoding["input_ids"].to(device)
                attention_mask = encoding["attention_mask"].to(device)

                # 进度=当前步骤/总步骤*100（取整数，最大99%避免提前显示完成）
                current_step += 1
                progress = min(int((current_step / total_steps) * 100), 99)
                article.review_progress = progress
                db.commit()  # 实时提交进度，SSE会自动推送更新

                # -------------------------- 步骤2：模型预测（更新进度） --------------------------
                with torch.no_grad():
                    outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                    predicted_label = outputs[0] if isinstance(outputs, tuple) else outputs

                    # 转换为整数标签（0=无问题，1~54=有问题）
                    if isinstance(predicted_label, torch.Tensor):
                        predicted_label = predicted_label.item()
                    predicted_label = int(predicted_label)

                current_step += 1
                progress = min(int((current_step / total_steps) * 100), 99)
                article.review_progress = progress
                db.commit()

                # -------------------------- 步骤3：关联Annotation（更新进度） --------------------------
                sentence.annotation_id = None
                sentence.has_problem = False  # 默认无问题

                # 模型输出1~54：关联数据库已有Annotation
                if 1 <= predicted_label <= 54:
                    annotation = db.query(db_models.Annotation).filter(
                        db_models.Annotation.id == predicted_label
                    ).first()
                    if annotation:
                        sentence.annotation_id = annotation.id
                        sentence.has_problem = True
                        violation_count += 1
                        print(f"句子ID {sentence.id} 关联违规类型：{annotation.content}")
                    else:
                        print(f"警告：Annotation表缺少id={predicted_label}的记录")
                        sentence.has_problem = True
                        violation_count += 1
                # 模型输出0：无问题
                elif predicted_label == 0:
                    sentence.has_problem = False
                # 其他标签：标记为未知违规
                else:
                    print(f"警告：模型输出无效标签{predicted_label}")
                    sentence.has_problem = True
                    violation_count += 1

                current_step += 1
                progress = min(int((current_step / total_steps) * 100), 99)
                article.review_progress = progress
                db.commit()

                # -------------------------- 步骤4：提交句子数据（更新进度） --------------------------
                db.add(sentence)
                db.commit()

                current_step += 1
                progress = min(int((current_step / total_steps) * 100), 99)
                article.review_progress = progress
                db.commit()

            except Exception as e:
                # 单个句子处理失败：跳过该句，但推进对应步骤的进度（避免卡住）
                print(f"句子ID {sentence.id} 审查失败：{str(e)}")
                current_step += steps_per_sentence  # 直接跳过该句的所有步骤
                progress = min(int((current_step / total_steps) * 100), 99)
                article.review_progress = progress
                db.commit()
                continue

        # 4. 审查完成：强制进度为100%
        violation_rate = violation_count / total_sentences if total_sentences > 0 else 0
        article.risk_level = calculate_risk_level(violation_rate)
        article.status = "已审查"
        article.review_progress = 100  # 最终确保100%
        article.review_time = datetime.utcnow()
        db.commit()
        print(f"文档ID {article_id} 审查完成，风险等级：{article.risk_level}")

    except Exception as e:
        # 审查失败：重置进度和状态
        article = db.query(db_models.Article).filter(db_models.Article.id == article_id).first()
        if article:
            article.status = "待审查"
            article.review_progress = 0
            db.commit()
        print(f"文档ID {article_id} 审查失败：{str(e)}")
