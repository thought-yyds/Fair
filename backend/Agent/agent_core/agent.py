"""
基于LangChain的公平竞争审查Agent核心
支持多种LLM提供商，统一配置管理
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union

# LangChain核心组件
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import BaseTool, StructuredTool
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import CallbackManager

# LangChain LLM组件
from langchain_community.llms import OpenAI
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatTongyi
from langchain.llms.base import BaseLLM

# LangChain工具和记忆
from langchain.tools import Tool
from langchain.memory import ConversationBufferWindowMemory

# 自定义工具
from agent_tools.langchain_tools import FairCompetitionRetrievalTool, DocumentAnalysisTool

# 统一配置
from config.settings import get_settings

logger = logging.getLogger(__name__)


class LangChainAgent:
    """基于LangChain的公平竞争审查Agent"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.settings = get_settings()
        self.config = config or self.settings.get_agent_config()
        self.llm_config = self.settings.get_llm_config()
        
        # 初始化组件
        self.llm = self._initialize_llm()
        self.tools = self._initialize_tools()
        self.memory = self._initialize_memory()
        self.prompt = self._create_prompt()
        self.agent = self._create_agent()
        self.agent_executor = self._create_agent_executor()

        logger.info(f"LangChain Agent初始化完成 - 模型: doubao-seed-1-6-250615")

    def _initialize_llm(self):
        """初始化LLM"""
        try:
            llm_config = {**self.llm_config}
            api_key = llm_config.get("api_key")
            if not api_key:
                raise ValueError("VOLC_ARK_API_KEY 未配置，无法初始化LLM")

            logger.info(
                "LLM配置: provider=%s model=%s temperature=%s max_tokens=%s",
                llm_config.get("provider"),
                llm_config.get("model"),
                llm_config.get("temperature"),
                llm_config.get("max_tokens"),
            )
            
            if llm_config["provider"] == "volcengine_ark":
                # 使用火山引擎原生API
                try:
                    from volcengine.ark import Ark
                    
                    # 初始化火山引擎ARK客户端
                    ark = Ark(
                        api_key=api_key,
                        region="cn-beijing"  # 根据你的区域设置
                    )
                    
                    # 创建自定义的LangChain兼容类
                    class VolcengineArkLLM(BaseLLM):
                        def __init__(self, ark_client, model_name, **kwargs):
                            super().__init__(**kwargs)
                            self.ark_client = ark_client
                            self.model_name = model_name
                            
                        def _call(self, prompt, stop=None, run_manager=None, **kwargs):
                            try:
                                response = self.ark_client.chat.completions.create(
                                    model=self.model_name,
                                    messages=[{"role": "user", "content": prompt}],
                                    temperature=kwargs.get("temperature", 0.1),
                                    max_tokens=kwargs.get("max_tokens", 2048)
                                )
                                return response.choices[0].message.content
                            except Exception as e:
                                logger.error(f"火山引擎API调用失败: {e}")
                                raise
                        
                        @property
                        def _llm_type(self):
                            return "volcengine_ark"
                    
                    return VolcengineArkLLM(
                        ark_client=ark,
                        model_name=llm_config["model"],
                        temperature=llm_config["temperature"],
                        max_tokens=llm_config["max_tokens"]
                    )
                    
                except ImportError:
                    logger.error("未安装volcengine SDK，请运行: pip install volcengine")
                    raise
                except Exception as e:
                    logger.error(f"火山引擎初始化失败: {e}")
                    raise
            elif llm_config["provider"] == "openai":
                return ChatOpenAI(
                        model=llm_config["model"],
                        api_key=api_key,
                    base_url=llm_config.get("base_url"),
                    temperature=llm_config["temperature"],
                    max_tokens=llm_config["max_tokens"],
                    streaming=True,  # 启用流式输出
                    verbose=getattr(self.config, "verbose", True)
                )
            elif llm_config["provider"] == "tongyi":
                return ChatTongyi(
                        model_name=llm_config["model"],
                        api_key=api_key,
                    temperature=llm_config["temperature"],
                    max_tokens=llm_config["max_tokens"],
                    streaming=True  # 启用流式输出
                )
            else:
                raise ValueError(f"不支持的LLM提供商: {llm_config['provider']}")

        except Exception as e:
            logger.error(f"LLM初始化失败: {str(e)}")
            raise ValueError(f"LLM初始化失败: {str(e)}")

    def _initialize_tools(self) -> List[BaseTool]:
        """初始化工具"""
        try:
            tools = []
            
            # 公平竞争审查检索工具
            retrieval_tool = FairCompetitionRetrievalTool()
            tools.append(retrieval_tool)
            
            # 文档分析工具
            analysis_tool = DocumentAnalysisTool()
            tools.append(analysis_tool)
            
            logger.info(f"工具初始化完成，共 {len(tools)} 个工具")
            return tools
            
        except Exception as e:
            logger.error(f"工具初始化失败: {str(e)}")
            return []

    def _initialize_memory(self):
        """初始化记忆"""
        try:
            memory_config = self.settings.get_memory_config()
            
            if memory_config["memory_type"] == "buffer":
                return ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True
                )
            elif memory_config["memory_type"] == "summary":
                return ConversationSummaryMemory(
                    llm=self.llm,
                    memory_key="chat_history",
                    return_messages=True
                )
            elif memory_config["memory_type"] == "window":
                return ConversationBufferWindowMemory(
                    k=memory_config["window_size"],
                    memory_key="chat_history",
                    return_messages=True
                )
            else:
                logger.warning(f"不支持的记忆类型: {memory_config['memory_type']}，使用默认buffer")
                return ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True
                )
                
        except Exception as e:
            logger.error(f"记忆初始化失败: {str(e)}")
            return ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )

    def _create_prompt(self) -> ChatPromptTemplate:
        """创建提示词模板"""
        try:
            system_message = """你是公平竞争审查领域的专业AI助手。你具备以下能力：

1. 专业知识：深度理解公平竞争审查相关法律法规
2. 检索能力：能够从政策文档中检索相关信息
3. 分析能力：能够分析政策合规性和风险点
4. 记忆能力：能够记住对话历史，提供连贯的回答

请根据用户的问题，使用合适的工具来获取信息，并提供准确、专业的回答。
如果问题涉及公平竞争审查，请优先使用检索工具获取相关政策信息。"""

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_message),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            logger.info("提示词模板创建成功")
            return prompt
            
        except Exception as e:
            logger.error(f"提示词模板创建失败: {str(e)}")
            raise ValueError(f"提示词模板创建失败: {str(e)}")

    def _create_agent(self):
        """创建Agent"""
        try:
            agent = create_openai_tools_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=self.prompt
            )
            
            logger.info("Agent创建成功")
            return agent
            
        except Exception as e:
            logger.error(f"Agent创建失败: {str(e)}")
            raise ValueError(f"Agent创建失败: {str(e)}")

    def _create_agent_executor(self) -> AgentExecutor:
        """创建Agent执行器"""
        try:
            executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                memory=self.memory,
                verbose=getattr(self.config, "verbose", True),
                max_iterations=getattr(self.config, "max_iterations", 5),
                handle_parsing_errors=True,
                return_intermediate_steps=True
            )
            
            logger.info("Agent执行器创建成功")
            return executor
            
        except Exception as e:
            logger.error(f"Agent执行器创建失败: {str(e)}")
            raise ValueError(f"Agent执行器创建失败: {str(e)}")

    def chat(self, user_input: str) -> str:
        """与Agent对话"""
        try:
            if not user_input.strip():
                return "请输入有效的问题"
            
            # 执行Agent
            result = self.agent_executor.invoke({
                "input": user_input
            })
            
            # 提取回答
            response = result.get("output", "抱歉，我无法回答这个问题。")
            
            logger.info(f"用户输入: {user_input[:50]}...")
            logger.info(f"Agent回答: {response[:50]}...")
            
            return response
            
        except Exception as e:
            logger.error(f"对话处理失败: {str(e)}")
            return f"处理失败: {str(e)}"

    def chat_stream(self, user_input: str):
        """与Agent对话 - 流式输出"""
        import time
        import sys
        
        try:
            if not user_input.strip():
                yield "请输入有效的问题"
                return
            
            logger.info(f"开始流式对话: {user_input[:50]}...")
            
            # 流式执行Agent
            full_response = ""
            for chunk in self.agent_executor.stream({
                "input": user_input
            }):
                if "output" in chunk:
                    # 输出内容
                    content = chunk["output"]
                    if content:
                        # 逐字符输出，模拟打字机效果
                        for char in content:
                            full_response += char
                            yield char
                            time.sleep(0.02)  # 控制输出速度
                        yield "\n"  # 换行
                        
                elif "actions" in chunk:
                    # 工具调用信息
                    actions = chunk["actions"]
                    for action in actions:
                        if hasattr(action, 'tool') and hasattr(action, 'tool_input'):
                            tool_msg = f"\n🔧 正在使用工具: {action.tool}\n"
                            for char in tool_msg:
                                yield char
                                time.sleep(0.01)
                                
                elif "steps" in chunk:
                    # 中间步骤
                    steps = chunk["steps"]
                    for step in steps:
                        if hasattr(step, 'observation'):
                            step_msg = f"\n📋 工具结果: {step.observation[:100]}...\n"
                            for char in step_msg:
                                yield char
                                time.sleep(0.01)
            
        except Exception as e:
            logger.error(f"流式对话处理失败: {str(e)}")
            error_msg = f"处理失败: {str(e)}"
            for char in error_msg:
                yield char
                time.sleep(0.02)

    def chat_stream_advanced(self, user_input: str):
        """高级流式输出 - 直接使用LLM流式响应"""
        import time
        import asyncio
        from langchain.schema import HumanMessage
        
        try:
            if not user_input.strip():
                yield "请输入有效的问题"
                return
            
            logger.info(f"开始高级流式对话: {user_input[:50]}...")
            
            # 构建消息
            messages = [HumanMessage(content=user_input)]
            
            # 如果有记忆，添加历史消息
            if hasattr(self.memory, 'chat_memory') and self.memory.chat_memory.messages:
                messages = self.memory.chat_memory.messages + messages
            
            # 直接使用LLM的流式响应
            response_text = ""
            for chunk in self.llm.stream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    content = chunk.content
                    response_text += content
                    
                    # 逐字符输出
                    for char in content:
                        yield char
                        time.sleep(0.03)  # 稍微慢一点，更真实
            
            # 保存到记忆
            if hasattr(self.memory, 'chat_memory'):
                self.memory.chat_memory.add_user_message(user_input)
                self.memory.chat_memory.add_ai_message(response_text)
            
            logger.info(f"流式对话完成，响应长度: {len(response_text)}")
            
        except Exception as e:
            logger.error(f"高级流式对话处理失败: {str(e)}")
            error_msg = f"处理失败: {str(e)}"
            for char in error_msg:
                yield char
                time.sleep(0.02)

    def get_memory_status(self) -> Dict[str, Any]:
        """获取记忆状态"""
        try:
            if hasattr(self.memory, 'chat_memory'):
                messages = self.memory.chat_memory.messages
                return {
                    "memory_type": "buffer",
                    "message_count": len(messages),
                    "recent_messages": [
                        {
                            "type": type(msg).__name__,
                            "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                        }
                        for msg in messages[-5:]  # 最近5条消息
                    ]
                }
            else:
                return {
                    "memory_type": "buffer",
                    "message_count": 0,
                    "recent_messages": []
                }
        except Exception as e:
            logger.error(f"获取记忆状态失败: {str(e)}")
            return {"error": str(e)}

    def clear_memory(self) -> bool:
        """清空记忆"""
        try:
            if hasattr(self.memory, 'clear'):
                self.memory.clear()
                logger.info("记忆已清空")
                return True
            else:
                logger.warning("当前记忆类型不支持清空操作")
                return False
        except Exception as e:
            logger.error(f"清空记忆失败: {str(e)}")
            return False

    def get_agent_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        try:
            return {
                "name": getattr(self.config, "name", "FairCompetitionAgent"),
                "llm_provider": "volcengine_ark",
                "llm_model": "doubao-seed-1-6-250615",
                "tools_count": len(self.tools),
                "memory_type": "buffer",
                "max_iterations": getattr(self.config, "max_iterations", 5),
                "verbose": getattr(self.config, "verbose", True)
            }
        except Exception as e:
            logger.error(f"获取Agent状态失败: {str(e)}")
            return {"error": str(e)}


class LangChainAgentManager:
    """LangChain Agent管理器"""
    
    def __init__(self):
        self.agents: Dict[str, LangChainAgent] = {}
        self.settings = get_settings()
    
    def create_agent(self, name: str, config: Optional[Dict[str, Any]] = None) -> LangChainAgent:
        """创建Agent"""
        try:
            agent = LangChainAgent(config)
            self.agents[name] = agent
            logger.info(f"Agent '{name}' 创建成功")
            return agent
        except Exception as e:
            logger.error(f"创建Agent '{name}' 失败: {str(e)}")
            raise
    
    def get_agent(self, name: str) -> Optional[LangChainAgent]:
        """获取Agent"""
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """列出所有Agent"""
        return list(self.agents.keys())
    
    def delete_agent(self, name: str) -> bool:
        """删除Agent"""
        if name in self.agents:
            del self.agents[name]
            logger.info(f"Agent '{name}' 已删除")
            return True
        return False
    
    def chat_with_agent(self, agent_name: str, user_input: str) -> str:
        """与指定Agent对话"""
        agent = self.get_agent(agent_name)
        if not agent:
            return f"Agent '{agent_name}' 不存在"
        
        return agent.chat(user_input)


def create_langchain_agent(config: Optional[Dict[str, Any]] = None) -> LangChainAgent:
    """创建LangChain Agent"""
    return LangChainAgent(config)


def create_agent_manager() -> LangChainAgentManager:
    """创建Agent管理器"""
    return LangChainAgentManager()


if __name__ == "__main__":
    # 测试Agent
    print("=== LangChain Agent测试 ===")
    
    try:
        # 创建Agent
        agent = create_langchain_agent()
        
        # 测试状态
        status = agent.get_agent_status()
        print(f"Agent状态: {status}")
        
        # 测试对话
        response = agent.chat("你好，你能帮我做什么？")
        print(f"Agent回答: {response}")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
