import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentConfig:
    llm_provider: str
    llm_model: str
    temperature: float = 0.1
    memory_type: str = "buffer"
    verbose: bool = False
    volc_ark_api_key: Optional[str] = None
    volc_ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"


@dataclass
class MemoryConfig:
    """Configuration for LangChain memory usage and LLM backend."""
    # memory
    memory_type: str = "buffer"  # buffer|summary|window|summary_buffer|token_buffer|vector
    window_size: int = 10
    max_token_limit: int = 2000
    summary_threshold: int = 5

    # llm backend
    llm_provider: str = "volcengine_ark"  # volcengine_ark|openai|tongyi
    llm_model: str = "generalv3"


@dataclass
class ChainConfig:
    """Configuration for chain creation and LLM behavior used in chains."""
    # llm backend
    llm_provider: str = "volcengine_ark"  # volcengine_ark|openai|tongyi
    llm_model: str = "doubao-seed-1-6-250615"
    temperature: float = 0.1
    max_tokens: int = 2048

    # volc ark
    volc_ark_api_key: Optional[str] = None
    volc_ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"

    # text splitter
    chunk_size: int = 1000
    chunk_overlap: int = 100


@dataclass
class LLMSettings:
    volc_ark_api_key: Optional[str] = None


@dataclass
class Settings:
    llm: LLMSettings

    # Provide default chain config derived from env-based settings
    def get_chain_config(self) -> ChainConfig:
        return ChainConfig(
            volc_ark_api_key=self.llm.volc_ark_api_key
        )
    
    # Provide LLM config for agent initialization
    def get_llm_config(self) -> dict:
        return {
            "provider": "volcengine_ark",
            "model": "doubao-seed-1-6-250615",
            "api_key": self.llm.volc_ark_api_key,
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "temperature": 0.1,
            "max_tokens": 2048
        }
    
    # Provide agent config for agent initialization
    def get_agent_config(self) -> AgentConfig:
        return AgentConfig(
            llm_provider="volcengine_ark",
            llm_model="doubao-seed-1-6-250615",
            temperature=0.1,
            memory_type="buffer",
            verbose=True,
            volc_ark_api_key=self.llm.volc_ark_api_key
        )


def get_settings() -> Settings:
    """Load minimal settings from environment variables.

    Expected env vars:
      - VOLC_ARK_API_KEY (preferred)
      - VOLC_ARK_APIKEY (fallback)
      - VOLCENGINE_ARK_API_KEY (fallback)
    """
    api_key = (
        os.getenv("VOLC_ARK_API_KEY")
        or os.getenv("VOLC_ARK_APIKEY")
        or os.getenv("VOLCENGINE_ARK_API_KEY")
    )
    if not api_key:
        raise RuntimeError(
            "Missing VOLC_ARK_API_KEY (or compatible) environment variable. "
            "Configure your Ark API key via environment variables before running the Agent."
        )
    return Settings(llm=LLMSettings(volc_ark_api_key=api_key))


