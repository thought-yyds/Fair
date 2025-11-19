"""
Agent核心模块
包含LangChain Agent框架的核心组件
"""

# LangChain Agent组件
from .agent import LangChainAgent, LangChainAgentManager, create_langchain_agent, create_agent_manager
from .langchain_memory import LangChainMemoryManager, MemoryConfig
from .langchain_chains import ChainManager, FairCompetitionChain, create_chain_manager, create_fair_competition_chain

__all__ = [
    'LangChainAgent',
    'LangChainAgentManager',
    'create_langchain_agent',
    'create_agent_manager',
    'LangChainMemoryManager',
    'MemoryConfig',
    'ChainManager',
    'FairCompetitionChain',
    'create_chain_manager',
    'create_fair_competition_chain',
]
