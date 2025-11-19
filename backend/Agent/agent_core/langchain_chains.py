"""
基于LangChain的链式处理系统
提供多种处理链和组合链，统一配置管理
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional, Union

# LangChain链式组件
from langchain.chains import LLMChain, SequentialChain, TransformChain
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.chains.summarize import load_summarize_chain
from langchain.chains.question_answering import load_qa_chain

# LangChain提示词
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage

# LangChain LLM
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatTongyi

# LangChain文档处理
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 自定义组件
from agent_tools.langchain_tools import FairCompetitionRetrievalTool

# 统一配置
from config.settings import get_settings
from config.settings import ChainConfig

logger = logging.getLogger(__name__)


class FairCompetitionChain:
    """公平竞争审查处理链"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.settings = get_settings()
        self.config = config or self.settings.get_chain_config()
        self.llm = self._initialize_llm()
        self.text_splitter = self._initialize_text_splitter()
        self.retrieval_tool = FairCompetitionRetrievalTool()

        logger.info(f"公平竞争审查链初始化完成 - 模型: {self.settings.llm.model}")

    def _initialize_llm(self):
        """初始化LLM，优先支持火山引擎"""
        try:
            if self.config.llm_provider == "volcengine_ark":
                # 火山引擎通过OpenAI兼容接口调用
                return ChatOpenAI(
                    model=self.config.llm_model,
                    api_key=self.config.volc_ark_api_key,
                    base_url=self.config.volc_ark_base_url,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
            elif self.config.llm_provider == "openai":
                return ChatOpenAI(
                    model=self.config.llm_model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
            elif self.config.llm_provider == "tongyi":
                return ChatTongyi(
                    model_name=self.config.llm_model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
            else:
                # 默认为火山引擎
                logger.warning(f"不支持的LLM提供商 {self.config.llm_provider}，默认使用火山引擎")
                return ChatOpenAI(
                    model=self.config.llm_model,
                    api_key=self.config.volc_ark_api_key,
                    base_url=self.config.volc_ark_base_url,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
        except Exception as e:
            logger.error(f"LLM初始化失败: {str(e)}")
            return None

    def _initialize_text_splitter(self):
        """初始化文本分割器"""
        return RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )

    def create_qa_chain(self) -> LLMChain:
        """创建问答链，指定输出键为'answer'"""
        try:
            prompt_template = """你是公平竞争审查领域的专业AI助手。请基于以下上下文信息回答问题：

上下文信息：
{context}

问题：{question}

请提供准确、专业的回答。如果上下文中没有相关信息，请说明并建议用户提供更具体的问题。

回答："""

            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question"]
            )

            # 为问答链指定唯一输出键'answer'
            return LLMChain(llm=self.llm, prompt=prompt, output_key="answer")

        except Exception as e:
            logger.error(f"创建问答链失败: {str(e)}")
            return None

    def create_summarization_chain(self) -> LLMChain:
        """创建摘要链，指定输出键为'summary'"""
        try:
            prompt_template = """请为以下公平竞争审查相关文档生成简洁的摘要：

文档内容：
{context}

请提取关键信息，包括：
1. 主要政策内容
2. 重要条款
3. 实施要求
4. 注意事项

摘要："""

            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["context"]
            )

            # 为摘要链指定唯一输出键'summary'
            return LLMChain(llm=self.llm, prompt=prompt, output_key="summary")

        except Exception as e:
            logger.error(f"创建摘要链失败: {str(e)}")
            return None

    def create_analysis_chain(self) -> LLMChain:
        """创建分析链，指定输出键为'analysis'"""
        try:
            prompt_template = """请对以下公平竞争审查相关内容进行深度分析：

内容：
{answer}

请从以下角度进行分析：
1. 合规性评估
2. 风险点识别
3. 建议措施
4. 相关法规依据

分析结果："""

            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["answer"]
            )

            # 为分析链指定唯一输出键'analysis'
            return LLMChain(llm=self.llm, prompt=prompt, output_key="analysis")

        except Exception as e:
            logger.error(f"创建分析链失败: {str(e)}")
            return None

    def create_retrieval_qa_chain(self, vectorstore=None) -> RetrievalQA:
        """创建检索问答链"""
        try:
            if not vectorstore:
                logger.warning("未提供向量存储，无法创建检索问答链")
                return None

            # 创建提示词模板
            prompt_template = """使用以下上下文信息回答问题。如果上下文中没有相关信息，请说明。

上下文：
{context}

问题：{question}

回答："""

            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question"]
            )

            # 创建检索问答链
            chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
                chain_type_kwargs={"prompt": prompt},
                return_source_documents=True
            )

            logger.info("检索问答链创建成功")
            return chain

        except Exception as e:
            logger.error(f"创建检索问答链失败: {str(e)}")
            return None

    def create_conversational_retrieval_chain(self, vectorstore=None, memory=None) -> ConversationalRetrievalChain:
        """创建对话检索链"""
        try:
            if not vectorstore:
                logger.warning("未提供向量存储，无法创建对话检索链")
                return None

            # 创建提示词模板
            prompt_template = """使用以下上下文信息回答问题。如果上下文中没有相关信息，请说明。

上下文：
{context}

问题：{question}

回答："""

            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question"]
            )

            # 创建对话检索链
            chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
                memory=memory,
                combine_docs_chain_kwargs={"prompt": prompt},
                return_source_documents=True
            )

            logger.info("对话检索链创建成功")
            return chain

        except Exception as e:
            logger.error(f"创建对话检索链失败: {str(e)}")
            return None

    def create_sequential_chain(self) -> SequentialChain:
        """创建顺序链"""
        try:
            # 创建各个子链
            qa_chain = self.create_qa_chain()
            summary_chain = self.create_summarization_chain()
            analysis_chain = self.create_analysis_chain()

            if not all([qa_chain, summary_chain, analysis_chain]):
                logger.error("子链创建失败，无法创建顺序链")
                return None

            # 创建顺序链，确保输入输出匹配
            sequential_chain = SequentialChain(
                chains=[qa_chain, summary_chain, analysis_chain],
                input_variables=["context", "question"],
                output_variables=["answer", "summary", "analysis"],
                verbose=True
            )

            logger.info("顺序链创建成功")
            return sequential_chain

        except Exception as e:
            logger.error(f"创建顺序链失败: {str(e)}")
            return None

    def create_transform_chain(self) -> TransformChain:
        """创建转换链"""
        try:
            def transform_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
                """转换输入"""
                query = inputs.get("query", "")

                # 执行检索
                retrieval_result = self.retrieval_tool._run(query, top_k=5)
                retrieval_data = json.loads(retrieval_result)

                # 提取内容
                context = ""
                if retrieval_data.get("status") == "success":
                    documents = retrieval_data.get("data", [])
                    context = "\n\n".join([
                        f"文档 {i+1}: {doc['content'][:300]}..."
                        for i, doc in enumerate(documents[:3])
                    ])

                return {
                    "context": context,
                    "question": query,
                    "retrieval_status": retrieval_data.get("status", "failed")
                }

            chain = TransformChain(
                input_variables=["query"],
                output_variables=["context", "question", "retrieval_status"],
                transform=transform_inputs
            )

            logger.info("转换链创建成功")
            return chain

        except Exception as e:
            logger.error(f"创建转换链失败: {str(e)}")
            return None

    def create_combined_chain(self) -> SequentialChain:
        """创建组合链（检索+问答+摘要+分析）"""
        try:
            # 创建转换链（检索）
            transform_chain = self.create_transform_chain()
            if not transform_chain:
                logger.error("转换链创建失败，无法创建组合链")
                return None

            # 创建问答链
            qa_chain = self.create_qa_chain()
            if not qa_chain:
                logger.error("问答链创建失败，无法创建组合链")
                return None

            # 创建摘要链
            summary_chain = self.create_summarization_chain()
            if not summary_chain:
                logger.error("摘要链创建失败，无法创建组合链")
                return None

            # 创建分析链
            analysis_chain = self.create_analysis_chain()
            if not analysis_chain:
                logger.error("分析链创建失败，无法创建组合链")
                return None

            # 创建组合链，确保每个链的输出键唯一
            combined_chain = SequentialChain(
                chains=[
                    transform_chain,
                    qa_chain,
                    summary_chain,
                    analysis_chain
                ],
                input_variables=["query"],
                # 明确指定所有输出变量，确保与各链的output_key匹配
                output_variables=["context", "question", "retrieval_status",
                                 "answer", "summary", "analysis"],
                verbose=True
            )

            logger.info("组合链创建成功")
            return combined_chain

        except Exception as e:
            logger.error(f"创建组合链失败: {str(e)}")
            return None

    def process_query(self, query: str, chain_type: str = "combined") -> Dict[str, Any]:
        """处理查询"""
        try:
            if chain_type == "qa":
                chain = self.create_qa_chain()
                if chain:
                    # 先检索
                    retrieval_result = self.retrieval_tool._run(query, top_k=5)
                    retrieval_data = json.loads(retrieval_result)

                    if retrieval_data.get("status") == "success":
                        context = "\n\n".join([
                            doc['content'][:300] + "..."
                            for doc in retrieval_data.get("data", [])[:3]
                        ])

                        result = chain.invoke({"context": context, "question": query})
                        return {
                            "status": "success",
                            "chain_type": chain_type,
                            "answer": result.get("answer", ""),  # 使用指定的输出键
                            "context": context
                        }
                    else:
                        return {
                            "status": "error",
                            "error": "检索失败",
                            "chain_type": chain_type
                        }

            elif chain_type == "combined":
                chain = self.create_combined_chain()
                if chain:
                    result = chain.invoke({"query": query})
                    return {
                        "status": "success",
                        "chain_type": chain_type,
                        "query": query,
                        "context": result.get("context", ""),
                        "answer": result.get("answer", ""),
                        "summary": result.get("summary", ""),
                        "analysis": result.get("analysis", ""),
                        "retrieval_status": result.get("retrieval_status", "unknown")
                    }

            else:
                return {
                    "status": "error",
                    "error": f"不支持的链类型: {chain_type}",
                    "chain_type": chain_type
                }

            return {
                "status": "error",
                "error": "链创建失败",
                "chain_type": chain_type
            }

        except Exception as e:
            logger.error(f"处理查询失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "chain_type": chain_type
            }


class ChainManager:
    """链管理器"""

    def __init__(self):
        self.chains: Dict[str, Any] = {}
        self.default_config = ChainConfig()  # 默认使用火山引擎配置

    def create_chain(self, name: str, chain_type: str, config: ChainConfig = None) -> Any:
        """创建链"""
        try:
            fair_competition_chain = FairCompetitionChain(config or self.default_config)

            if chain_type == "qa":
                chain = fair_competition_chain.create_qa_chain()
            elif chain_type == "summary":
                chain = fair_competition_chain.create_summarization_chain()
            elif chain_type == "analysis":
                chain = fair_competition_chain.create_analysis_chain()
            elif chain_type == "sequential":
                chain = fair_competition_chain.create_sequential_chain()
            elif chain_type == "transform":
                chain = fair_competition_chain.create_transform_chain()
            elif chain_type == "combined":
                chain = fair_competition_chain.create_combined_chain()
            else:
                raise ValueError(f"不支持的链类型: {chain_type}")

            if chain:
                self.chains[name] = {
                    "chain": chain,
                    "chain_type": chain_type,
                    "fair_competition_chain": fair_competition_chain
                }
                logger.info(f"链 '{name}' 创建成功 - 类型: {chain_type}")
                return chain
            else:
                raise ValueError(f"链创建失败: {chain_type}")

        except Exception as e:
            logger.error(f"创建链失败: {str(e)}")
            raise

    def get_chain(self, name: str) -> Optional[Any]:
        """获取链"""
        chain_info = self.chains.get(name)
        return chain_info["chain"] if chain_info else None

    def list_chains(self) -> List[str]:
        """列出所有链"""
        return list(self.chains.keys())

    def delete_chain(self, name: str) -> bool:
        """删除链"""
        if name in self.chains:
            del self.chains[name]
            logger.info(f"链 '{name}' 已删除")
            return True
        return False

    def process_with_chain(self, chain_name: str, query: str) -> Dict[str, Any]:
        """使用指定链处理查询"""
        try:
            chain_info = self.chains.get(chain_name)
            if not chain_info:
                return {
                    "status": "error",
                    "error": f"链 '{chain_name}' 不存在"
                }

            fair_competition_chain = chain_info["fair_competition_chain"]
            chain_type = chain_info["chain_type"]

            return fair_competition_chain.process_query(query, chain_type)

        except Exception as e:
            logger.error(f"使用链处理查询失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }


def create_chain_manager() -> ChainManager:
    """创建链管理器"""
    return ChainManager()


def create_fair_competition_chain(config: ChainConfig = None) -> FairCompetitionChain:
    """创建公平竞争审查链"""
    return FairCompetitionChain(config)


if __name__ == "__main__":
    # 测试链系统
    print("=== LangChain链系统测试 ===")

    # 创建火山引擎配置
    api_key = os.getenv("VOLC_ARK_API_KEY")
    if not api_key:
        raise RuntimeError("请先在环境变量 VOLC_ARK_API_KEY 中配置你的火山引擎密钥再运行本示例。")

    config = ChainConfig(
        llm_provider="volcengine_ark",
        llm_model="deepseek-r1-250528",
        temperature=0.1,
        volc_ark_api_key=api_key,
        volc_ark_base_url="https://ark.cn-beijing.volces.com/api/v3"
    )
    
    # 创建链
    chain = create_fair_competition_chain(config)
    
    # 测试问答链
    print("\n测试问答链:")
    qa_chain = chain.create_qa_chain()
    if qa_chain:
        print("问答链创建成功")
    
    # 测试组合链
    print("\n测试组合链:")
    combined_chain = chain.create_combined_chain()
    if combined_chain:
        print("组合链创建成功")
        
        # 测试处理查询
        result = chain.process_query("公平竞争审查的基本原则是什么？", "combined")
        print(f"处理结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # 测试链管理器
    print("\n测试链管理器:")
    manager = create_chain_manager()
    
    # 创建多个链
    manager.create_chain("qa_chain", "qa", config)
    manager.create_chain("summary_chain", "summary", config)
    manager.create_chain("combined_chain", "combined", config)
    
    print(f"创建的链: {manager.list_chains()}")
    
    # 测试链处理
    result = manager.process_with_chain("combined_chain", "什么是公平竞争审查？")
    print(f"链处理结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
