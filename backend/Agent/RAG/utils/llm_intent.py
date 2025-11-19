import json
import logging

from ..API import LLMClient

logger = logging.getLogger(__name__)


def simple_llm_call(prompt: str) -> str:
    try:
        client = LLMClient()
        response = client.simple_chat(prompt)
        logger.debug(f"LLM调用结果：{response[:100]}...")
        return response or ""
    except Exception as e:
        logger.error(f"❌ LLM API调用失败：{str(e)}", exc_info=True)
        return ""


def intent_translate(user_query: str) -> dict:
    prompt = f"""
        任务：将输入句子转为“与54条市场准入审查标准精准对齐的条款化表达”，仅输出JSON（无多余文字、无注释）。
    
        核心依据：需严格贴合以下54条审查标准的核心违规类型、高频术语（重点关注加粗术语）：
        1. 违规类型分类及核心术语：
           - 准入/退出条件类：设置不必要准入条件、排斥/限制经营者、歧视性准入条件、市场退出障碍
           - 差别化待遇类：不同所有制/地区/组织形式 差别化待遇、不平等准入条件
           - 市场壁垒类：备案/登记/注册 作为准入要求、要求设立分支机构、限定特定经营者、项目库/名录库 排斥
           - 招标投标/政府采购类：限定投标人所在地/所有制、歧视性资质要求、本地业绩/奖项作为投标条件、要求本地缴纳社保
           - 财政补贴/优惠类：无依据 财政奖励/补贴、税收优惠、要素获取优惠、减免社保费用
           - 地域/商品限制类：外地/进口商品 歧视性价格/补贴/技术标准、阻碍外地商品进入、限定本地采购
           - 其他类：强制转让技术、违法设定特许经营、无依据增设行政审批、保证金违规要求
    
        2. 高频必须复用术语（转译时优先使用）：
        准入条件、退出条件、排斥经营者、限制经营者、歧视性待遇、备案要求、注册要求、分支机构、财政补贴、税收优惠、限定经营、招标投标、政府采购、本地业绩、社保缴纳、项目库、名录库、地域限制、技术标准、特许经营
    
        输入：{user_query}
        输出格式（严格遵循，字段不可缺）：
        {{
          "normalized_query": "【用审查标准术语重述核心行为】，【明确可能涉及的违规逻辑】",
          "keywords": ["【从normalized_query提取，且必须是上述高频术语/违规类型核心词】", "..."],
          "chapter_hints": ["【对应审查标准的具体违规类型（如“设置不必要准入条件”）】", "..."],
          "possible_matched_rules": ["【推测可能匹配的审查标准序号（如“28”“10”）】", "..."]
        }}
    
        强制要求（未满足则视为无效输出）：
        1. normalized_query 要求：
           - 完全抛弃原句具体名称（如“李尔汽车”“康恒企业”“某平台”“2024年第一季度”），仅保留核心行为+审查标准术语；
           - 必须体现“行为+可能违规点”（例：输入“项目经理需近三个月社保”→ 转译为“将缴纳本地近三个月社保作为投标准入条件，限制外地经营者参与招标投标活动”）；
           - 每句转译都要对应至少1个上述违规类型，复用至少2个高频术语。
    
        2. keywords 要求：
           - 仅从 normalized_query 中提取，数量3-5个；
           - 必须是上述“高频必须复用术语”或“违规类型核心词”，禁止出现具体名称、时间、金额。
    
        3. chapter_hints 要求：
           - 直接引用上述“违规类型分类”中的完整表述（如“限定特定经营者”“设置不必要准入条件”）；
           - 数量1-3个，需与 normalized_query 逻辑完全一致。
        """
    prompt = prompt.strip()

    try:
        response = simple_llm_call(prompt)
        parsed = json.loads(response.strip())
        if not isinstance(parsed, dict):
            parsed = {}
        normalized_query = (parsed.get("normalized_query") or "").strip() or user_query
        keywords = parsed.get("keywords", [])
        keywords = keywords if isinstance(keywords, list) else []
        chapter_hints = parsed.get("chapter_hints", [])
        chapter_hints = chapter_hints if isinstance(chapter_hints, list) else []
        result = {
            "normalized_query": normalized_query,
            "keywords": keywords,
            "chapter_hints": chapter_hints,
        }
        logger.info(f"✅ 意图转译结果：{json.dumps(result, ensure_ascii=False)}")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"❌ 意图输出非JSON（响应：{response[:100]}...）：{str(e)}")
        return {
            "normalized_query": user_query,
            "keywords": [],
            "chapter_hints": [],
        }
    except Exception as e:
        logger.error(f"❌ 意图转译失败：{str(e)}", exc_info=True)
        return {
            "normalized_query": user_query,
            "keywords": [],
            "chapter_hints": [],
        }
