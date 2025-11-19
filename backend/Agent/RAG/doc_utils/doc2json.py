import os
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
import logging
from llama_index.core import SimpleDirectoryReader
from volcenginesdkarkruntime import Ark
from config.settings import get_settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolicyStructurizeAPI:
    """基于火山引擎API的政策文档结构化处理类（双层拆分：章节→LLM最小块）"""

    def __init__(
            self,
            model_name: str = "doubao-seed-1.6-250615",
            long_chapter_warn_threshold: int = 3000,  # 章节超长提醒阈值
            min_chunk_prompt_example: str = """示例：
            章节文本："第一条 为规范公平竞争审查，制定本办法。第二条 本办法适用于行政机关。"
            拆分结果：
            ["第一条 为规范公平竞争审查，制定本办法。", "第二条 本办法适用于行政机关。"]
            """
    ):
        """
        初始化：新增LLM拆分最小块的配置
        min_chunk_prompt_example：给LLM的拆分示例，确保拆分逻辑符合政策文档习惯
        """
        self.model_name = model_name
        settings = get_settings()
        self.client = Ark(api_key=settings.llm.volc_ark_api_key, timeout=1800)
        self.long_chapter_warn_threshold = long_chapter_warn_threshold
        self.chapter_pattern = re.compile(r"第[一二三四五六七八九十百\d]+章(?:\s+[\u4e00-\u9fa5]+)?", re.UNICODE)
        self.min_chunk_prompt_example = min_chunk_prompt_example  # LLM拆分的示例模板

    # --------------------------
    # 原有逻辑：提取章节边界（无修改）
    # --------------------------
    def _extract_chapter_boundaries(self, full_text: str) -> List[Dict]:
        chapter_matches = list(self.chapter_pattern.finditer(full_text))
        if not chapter_matches:
            logger.warning("未识别到章节标题，按“双换行”分割为段落分块")
            para_boundaries = []
            para_splits = [0] + [m.start() + 2 for m in re.finditer(r"\n\n", full_text)] + [len(full_text)]
            for i in range(len(para_splits) - 1):
                start = para_splits[i]
                end = para_splits[i + 1]
                para_text = full_text[start:end].strip()
                if para_text:
                    para_boundaries.append({
                        "chapter_title": f"段落{i + 1}",
                        "chapter_text": para_text
                    })
            return para_boundaries

        chapter_boundaries = []
        for i in range(len(chapter_matches)):
            current_match = chapter_matches[i]
            chapter_title = current_match.group().strip()
            start_idx = current_match.start()
            end_idx = chapter_matches[i + 1].start() if i + 1 < len(chapter_matches) else len(full_text)
            chapter_text = full_text[start_idx:end_idx].strip()

            if len(chapter_text) > self.long_chapter_warn_threshold:
                logger.warning(
                    f"章节【{chapter_title}】过长（{len(chapter_text)}字），将调用LLM拆分为最小块"
                )

            chapter_boundaries.append({
                "chapter_title": chapter_title,
                "chapter_text": chapter_text
            })
        return chapter_boundaries

    # --------------------------
    # 新增逻辑1：让LLM将章节拆分为最小逻辑块（核心修改）
    # --------------------------
    def _llm_split_chapter_to_min_chunks(self, chapter_text: str, chapter_title: str) -> List[str]:
        """
        调用LLM将章节拆分为最小逻辑块（如单条条款），仅返回纯文本列表（无冗余元信息）
        """
        # 构建拆分Prompt：明确要求“最小逻辑单位”+“纯文本列表”+“示例引导”
        split_prompt = [
            {
                "role": "system",
                "content": f"""你是政策文档拆分专家，需将章节文本拆分为最小逻辑单位（如一条条款、一个独立规定），遵循以下规则：
                    1. 拆分标准：每个块必须是“完整的最小逻辑单元”（如“第一条xxx”“（一）xxx”，不可拆分到句子级）；
                    2. 输出格式：仅返回拆分后的纯文本列表（JSON数组），无任何解释文字、标题或格式标记；
                    3. 内容要求：完全保留原文内容，不增删、不修改任何文字；
                    4. 参考示例：{self.min_chunk_prompt_example}

                    若章节已为最小单位（如仅1条条款），直接返回含该文本的列表。
                    """
            },
            {
                "role": "user",
                "content": f"章节标题：{chapter_title}\n需拆分的章节文本：{chapter_text}"
            }
        ]

        try:
            # 调用LLM执行拆分
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=split_prompt
            )
            content = response.choices[0].message.content.strip()
            # 清理LLM可能输出的代码块标记（如```json）
            content = content.replace("```json", "").replace("```", "").strip()
            # 解析为纯文本列表
            min_chunks = json.loads(content)
            # 过滤空字符串，确保每个块有效
            min_chunks = [chunk.strip() for chunk in min_chunks if chunk.strip()]
            logger.info(f"章节【{chapter_title}】拆分为 {len(min_chunks)} 个最小块")
            return min_chunks
        except Exception as e:
            logger.error(f"LLM拆分章节【{chapter_title}】失败：{str(e)}，将降级按条款号机械拆分")
            # 降级方案：若LLM拆分失败，按“条款号”机械拆分（保证流程不中断）
            clause_pattern = re.compile(r"第[一二三四五六七八九十百\d]+条", re.UNICODE)
            clause_matches = list(clause_pattern.finditer(chapter_text))
            if not clause_matches:
                # 无条款号时按双换行拆分
                return [para.strip() for para in chapter_text.split("\n\n") if para.strip()]
            # 有条款号时按条款拆分
            split_points = [0] + [match.start() for match in clause_matches] + [len(chapter_text)]
            min_chunks = []
            for i in range(1, len(split_points) - 1):
                chunk = chapter_text[split_points[i]:split_points[i + 1]].strip()
                if chunk:
                    min_chunks.append(chunk)
            return min_chunks

    # --------------------------
    # 原有逻辑：章节级结构化（保留，用于章节元数据提取）
    # --------------------------
    def _build_structurize_prompt(self, chapter_text: str, chapter_title: str) -> List[Dict]:
        system_prompt = """你是公平竞争审查领域的政策结构化专家，需提取章节核心元数据：
                            - document_type：文档类型（如部门规章、地方性法规）
                            - chapter：章节标题（严格使用输入的章节标题）
                            - clause：章节内所有条款号（用逗号分隔）
                            - effective_date：章节内生效日期（无则填“无”）
                            - authority：制定部门（无则填“无”）
                            - exception：例外情况（无则填“无”）
                            仅返回JSON格式，无其他文字，缺失字段填“无”。
                            """
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"章节标题：{chapter_title}\n章节文本：{chapter_text}"}
        ]

    def _llm_structurize_chapter(self, chapter_text: str, chapter_title: str) -> Dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self._build_structurize_prompt(chapter_text, chapter_title)
            )
            content = response.choices[0].message.content.strip()
            content = content.replace("```json", "").replace("```", "").strip()
            struct_dict = json.loads(content)
            required_fields = ["document_type", "chapter", "clause",
                               "effective_date", "authority", "exception"]
            for field in required_fields:
                struct_dict.setdefault(field, "无")
            struct_dict["chapter"] = chapter_title
            return struct_dict
        except Exception as e:
            logger.error(f"章节【{chapter_title}】结构化失败：{str(e)}")
            return {
                "document_type": "无",
                "chapter": chapter_title,
                "clause": "无",
                "effective_date": "无",
                "authority": "无",
                "exception": "无"
            }

    # --------------------------
    # 核心修改：process_document（双层拆分+最小块组装）
    # --------------------------
    def process_document(self, doc_path: str) -> List[Dict]:
        if not os.path.exists(doc_path):
            logger.error(f"文档不存在：{doc_path}")
            return []

        # 1. 加载整篇文档
        reader = SimpleDirectoryReader(input_files=[doc_path])
        raw_docs = reader.load_data()
        if not raw_docs:
            logger.error(f"文档加载失败：{doc_path}")
            return []
        full_text = raw_docs[0].text
        doc_name = os.path.basename(doc_path)
        logger.info(f"处理文档：{doc_name}（全文长度：{len(full_text)}字）")

        # 2. 第一层拆分：按章节分块
        chapter_boundaries = self._extract_chapter_boundaries(full_text)
        if not chapter_boundaries:
            logger.warning("未生成任何章节分块")
            return []
        logger.info(f"第一层拆分完成：{len(chapter_boundaries)} 个章节")

        # 3. 第二层拆分：对每个章节→LLM拆分为最小块（核心步骤）
        final_min_chunks = []  # 最终输出的最小块列表
        global_min_chunk_id = 1  # 全局最小块ID（唯一标识）

        for chapter_idx, chapter in enumerate(chapter_boundaries, 1):
            chapter_title = chapter["chapter_title"]
            chapter_text = chapter["chapter_text"]
            logger.info(f"\n处理章节 {chapter_idx}/{len(chapter_boundaries)}：【{chapter_title}】")

            # 3.1 提取章节级元数据（用于关联最小块）
            chapter_struct_meta = self._llm_structurize_chapter(chapter_text, chapter_title)

            # 3.2 LLM拆分章节为最小块
            min_chunks = self._llm_split_chapter_to_min_chunks(chapter_text, chapter_title)
            if not min_chunks:
                logger.warning(f"章节【{chapter_title}】未拆分出有效最小块，跳过")
                continue

            # 3.3 组装最小块：仅保留“必要元数据+原始内容”（无冗余）
            for min_chunk_idx, min_chunk_text in enumerate(min_chunks, 1):
                final_min_chunks.append({
                    "page_content": min_chunk_text,  # 最小块仅保留文档原始内容
                    "metadata": {
                        # 必要元数据：仅保留归属关联（便于追溯）和核心标识
                        "file_name": doc_name,
                        "file_path": doc_path,
                        "min_chunk_id": global_min_chunk_id,  # 全局唯一ID
                        "parent_chapter_title": chapter_title,  # 所属章节（关键关联）
                        "parent_chapter_id": chapter_idx,  # 所属章节ID
                        # 章节级核心元数据（复用，避免重复计算）
                        "document_type": chapter_struct_meta["document_type"],
                        "authority": chapter_struct_meta["authority"]
                    }
                })
                global_min_chunk_id += 1

        logger.info(f"\n文档{doc_name}处理完成：共生成 {len(final_min_chunks)} 个最小逻辑块")
        return final_min_chunks

    # --------------------------
    # 批量处理：逻辑不变（自动适配最小块输出）
    # --------------------------
    def process_documents_batch(self, doc_dir: str) -> List[Dict]:
        all_min_chunks = []
        for doc_path in Path(doc_dir).glob("*.docx"):
            min_chunks = self.process_document(str(doc_path))
            all_min_chunks.extend(min_chunks)
        logger.info(f"批量处理完成，累计生成 {len(all_min_chunks)} 个最小逻辑块")
        return all_min_chunks