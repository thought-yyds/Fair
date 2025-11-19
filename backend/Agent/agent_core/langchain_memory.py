"""
基于LangChain的记忆系统
提供多种记忆管理策略
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime

# LangChain记忆组件
from langchain.memory import (
    ConversationBufferMemory,
    ConversationSummaryMemory,
    ConversationBufferWindowMemory,
    ConversationSummaryBufferMemory,
    ConversationTokenBufferMemory,
    VectorStoreRetrieverMemory
)
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 统一配置
from config.settings import MemoryConfig

# LangChain LLM
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatTongyi

logger = logging.getLogger(__name__)


class LangChainMemoryManager:
    """LangChain记忆管理器"""
    
    def __init__(self, config: MemoryConfig = None):
        self.config = config or MemoryConfig()
        self.memory = self._initialize_memory()
        self.llm = self._initialize_llm()
        
        logger.info(f"LangChain记忆管理器初始化完成 - 类型: {self.config.memory_type}")
    
    def _initialize_llm(self):
        """初始化LLM"""
        try:
            if self.config.llm_provider == "volcengine_ark":
                # 使用火山方舟
                from langchain_community.llms import VolcEngineMaasLLM
                return VolcEngineMaasLLM(
                    model=self.config.llm_model,
                    temperature=0.1
                )
            elif self.config.llm_provider == "openai":
                return ChatOpenAI(
                    model=self.config.llm_model,
                    temperature=0.1
                )
            elif self.config.llm_provider == "tongyi":
                return ChatTongyi(
                    model_name=self.config.llm_model,
                    temperature=0.1
                )
            else:
                # 默认使用火山方舟
                from langchain_community.llms import VolcEngineMaasLLM
                return VolcEngineMaasLLM(
                    model=self.config.llm_model,
                    temperature=0.1
                )
        except Exception as e:
            logger.error(f"LLM初始化失败: {str(e)}")
            return None
    
    def _initialize_memory(self):
        """初始化记忆系统"""
        try:
            if self.config.memory_type == "buffer":
                return ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True,
                    output_key="output"
                )
            
            elif self.config.memory_type == "summary":
                if not self.llm:
                    logger.warning("LLM未初始化，回退到buffer memory")
                    return ConversationBufferMemory(
                        memory_key="chat_history",
                        return_messages=True,
                        output_key="output"
                    )
                return ConversationSummaryMemory(
                    llm=self.llm,
                    memory_key="chat_history",
                    return_messages=True,
                    output_key="output"
                )
            
            elif self.config.memory_type == "window":
                return ConversationBufferWindowMemory(
                    k=self.config.window_size,
                    memory_key="chat_history",
                    return_messages=True,
                    output_key="output"
                )
            
            elif self.config.memory_type == "summary_buffer":
                if not self.llm:
                    logger.warning("LLM未初始化，回退到buffer memory")
                    return ConversationBufferMemory(
                        memory_key="chat_history",
                        return_messages=True,
                        output_key="output"
                    )
                return ConversationSummaryBufferMemory(
                    llm=self.llm,
                    max_token_limit=self.config.max_token_limit,
                    memory_key="chat_history",
                    return_messages=True,
                    output_key="output"
                )
            
            elif self.config.memory_type == "token_buffer":
                if not self.llm:
                    logger.warning("LLM未初始化，回退到buffer memory")
                    return ConversationBufferMemory(
                        memory_key="chat_history",
                        return_messages=True,
                        output_key="output"
                    )
                return ConversationTokenBufferMemory(
                    llm=self.llm,
                    max_token_limit=self.config.max_token_limit,
                    memory_key="chat_history",
                    return_messages=True,
                    output_key="output"
                )
            
            elif self.config.memory_type == "vector":
                return self._create_vector_memory()
            
            else:
                logger.warning(f"未知的记忆类型: {self.config.memory_type}，使用buffer memory")
                return ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True,
                    output_key="output"
                )
                
        except Exception as e:
            logger.error(f"记忆系统初始化失败: {str(e)}")
            # 回退到基础buffer memory
            return ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="output"
            )
    
    def _create_vector_memory(self):
        """创建向量记忆"""
        try:
            # 创建嵌入模型
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            # 创建向量存储
            vectorstore = FAISS.from_texts(
                texts=["初始记忆"],
                embedding=embeddings
            )
            
            # 创建检索器
            retriever = vectorstore.as_retriever(
                search_kwargs={"k": 5}
            )
            
            return VectorStoreRetrieverMemory(
                retriever=retriever,
                memory_key="chat_history",
                return_messages=True,
                output_key="output"
            )
            
        except Exception as e:
            logger.error(f"向量记忆创建失败: {str(e)}")
            return ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="output"
            )
    
    def add_message(self, role: str, content: str):
        """添加消息到记忆"""
        try:
            if role == "human":
                message = HumanMessage(content=content)
            elif role == "assistant":
                message = AIMessage(content=content)
            elif role == "system":
                message = SystemMessage(content=content)
            else:
                logger.warning(f"未知的角色类型: {role}")
                return
            
            # 添加到记忆
            if hasattr(self.memory, 'chat_memory'):
                self.memory.chat_memory.add_message(message)
            elif hasattr(self.memory, 'save_context'):
                # 对于某些记忆类型，需要特殊处理
                self.memory.save_context(
                    {"input": content if role == "human" else ""},
                    {"output": content if role == "assistant" else ""}
                )
            
            logger.debug(f"已添加消息到记忆: {role} - {content[:50]}...")
            
        except Exception as e:
            logger.error(f"添加消息到记忆失败: {str(e)}")
    
    def get_memory_variables(self) -> Dict[str, Any]:
        """获取记忆变量"""
        try:
            if hasattr(self.memory, 'memory_variables'):
                return self.memory.memory_variables
            else:
                return {"chat_history": []}
        except Exception as e:
            logger.error(f"获取记忆变量失败: {str(e)}")
            return {"chat_history": []}
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """加载记忆变量"""
        try:
            if hasattr(self.memory, 'load_memory_variables'):
                return self.memory.load_memory_variables(inputs)
            else:
                return {"chat_history": []}
        except Exception as e:
            logger.error(f"加载记忆变量失败: {str(e)}")
            return {"chat_history": []}
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]):
        """保存上下文"""
        try:
            if hasattr(self.memory, 'save_context'):
                self.memory.save_context(inputs, outputs)
            else:
                # 手动保存
                human_input = inputs.get("input", "")
                ai_output = outputs.get("output", "")
                if human_input:
                    self.add_message("human", human_input)
                if ai_output:
                    self.add_message("assistant", ai_output)
            
            logger.debug("上下文已保存到记忆")
            
        except Exception as e:
            logger.error(f"保存上下文失败: {str(e)}")
    
    def clear_memory(self):
        """清除记忆"""
        try:
            if hasattr(self.memory, 'clear'):
                self.memory.clear()
            elif hasattr(self.memory, 'chat_memory'):
                self.memory.chat_memory.clear()
            
            logger.info("记忆已清除")
            
        except Exception as e:
            logger.error(f"清除记忆失败: {str(e)}")
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """获取对话历史"""
        try:
            if hasattr(self.memory, 'chat_memory'):
                messages = self.memory.chat_memory.messages
                history = []
                
                for msg in messages:
                    if isinstance(msg, HumanMessage):
                        history.append({
                            "role": "human",
                            "content": msg.content,
                            "timestamp": datetime.now().isoformat()
                        })
                    elif isinstance(msg, AIMessage):
                        history.append({
                            "role": "assistant", 
                            "content": msg.content,
                            "timestamp": datetime.now().isoformat()
                        })
                    elif isinstance(msg, SystemMessage):
                        history.append({
                            "role": "system",
                            "content": msg.content,
                            "timestamp": datetime.now().isoformat()
                        })
                
                return history
            else:
                return []
                
        except Exception as e:
            logger.error(f"获取对话历史失败: {str(e)}")
            return []
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """获取记忆摘要"""
        try:
            history = self.get_conversation_history()
            
            summary = {
                "memory_type": self.config.memory_type,
                "total_messages": len(history),
                "human_messages": len([h for h in history if h["role"] == "human"]),
                "assistant_messages": len([h for h in history if h["role"] == "assistant"]),
                "system_messages": len([h for h in history if h["role"] == "system"]),
                "config": {
                    "window_size": self.config.window_size,
                    "max_token_limit": self.config.max_token_limit,
                    "summary_threshold": self.config.summary_threshold
                }
            }
            
            # 如果有LLM，尝试生成内容摘要
            if self.llm and history:
                try:
                    recent_messages = history[-5:]  # 最近5条消息
                    content_summary = self._generate_content_summary(recent_messages)
                    summary["recent_summary"] = content_summary
                except Exception as e:
                    logger.warning(f"生成内容摘要失败: {str(e)}")
            
            return summary
            
        except Exception as e:
            logger.error(f"获取记忆摘要失败: {str(e)}")
            return {"error": str(e)}
    
    def _generate_content_summary(self, messages: List[Dict]) -> str:
        """生成内容摘要"""
        try:
            if not self.llm:
                return "无法生成摘要（LLM未初始化）"
            
            # 构建摘要提示
            content = "\n".join([
                f"{msg['role']}: {msg['content'][:100]}..."
                for msg in messages
            ])
            
            prompt = f"""请为以下对话生成简洁的摘要：

{content}

摘要："""
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.error(f"生成内容摘要失败: {str(e)}")
            return f"摘要生成失败: {str(e)}"
    
    def export_memory(self, file_path: str):
        """导出记忆到文件"""
        try:
            history = self.get_conversation_history()
            summary = self.get_memory_summary()
            
            export_data = {
                "export_time": datetime.now().isoformat(),
                "memory_config": {
                    "memory_type": self.config.memory_type,
                    "window_size": self.config.window_size,
                    "max_token_limit": self.config.max_token_limit,
                    "summary_threshold": self.config.summary_threshold
                },
                "memory_summary": summary,
                "conversation_history": history
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"记忆已导出到: {file_path}")
            
        except Exception as e:
            logger.error(f"导出记忆失败: {str(e)}")
    
    def import_memory(self, file_path: str):
        """从文件导入记忆"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 清除现有记忆
            self.clear_memory()
            
            # 导入对话历史
            history = import_data.get("conversation_history", [])
            for msg in history:
                self.add_message(msg["role"], msg["content"])
            
            logger.info(f"记忆已从 {file_path} 导入")
            
        except Exception as e:
            logger.error(f"导入记忆失败: {str(e)}")


def create_memory_manager(config: MemoryConfig = None) -> LangChainMemoryManager:
    """创建记忆管理器"""
    return LangChainMemoryManager(config)


def create_memory_config(
    memory_type: str = "buffer",
    window_size: int = 10,
    max_token_limit: int = 2000
) -> MemoryConfig:
    """创建记忆配置"""
    return MemoryConfig(
        memory_type=memory_type,
        window_size=window_size,
        max_token_limit=max_token_limit
    )


if __name__ == "__main__":
    # 测试记忆管理器
    print("=== LangChain记忆管理器测试 ===")
    
    # 创建配置
    config = create_memory_config(
        memory_type="buffer",
        window_size=5
    )
    
    # 创建记忆管理器
    memory_manager = create_memory_manager(config)
    
    # 添加一些测试消息
    memory_manager.add_message("human", "你好，请介绍一下公平竞争审查")
    memory_manager.add_message("assistant", "公平竞争审查是指对涉及市场主体经济活动的政策措施进行审查，确保其不会产生排除、限制竞争的效果。")
    memory_manager.add_message("human", "审查的基本原则有哪些？")
    memory_manager.add_message("assistant", "审查的基本原则包括：1. 市场优先原则；2. 公平竞争原则；3. 依法审查原则；4. 分类审查原则。")
    
    # 获取记忆摘要
    summary = memory_manager.get_memory_summary()
    print("记忆摘要:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    
    # 获取对话历史
    history = memory_manager.get_conversation_history()
    print(f"\n对话历史 ({len(history)} 条消息):")
    for i, msg in enumerate(history, 1):
        print(f"{i}. {msg['role']}: {msg['content'][:50]}...")
    
    # 测试导出/导入
    export_path = "test_memory_export.json"
    memory_manager.export_memory(export_path)
    print(f"\n记忆已导出到: {export_path}")
    
    # 清除记忆
    memory_manager.clear_memory()
    print("记忆已清除")
    
    # 重新导入
    memory_manager.import_memory(export_path)
    print("记忆已重新导入")
    
    # 验证导入结果
    new_history = memory_manager.get_conversation_history()
    print(f"重新导入后的对话历史: {len(new_history)} 条消息")
