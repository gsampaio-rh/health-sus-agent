"""Agent configuration — LLM provider, REPL limits, output paths.

Supports Anthropic, OpenAI, and any OpenAI-compatible API (Ollama, vLLM,
LM Studio) via base_url override.
"""

from __future__ import annotations

from typing import Literal

from langchain_core.language_models import BaseChatModel
from pydantic_settings import BaseSettings

_DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-20250514",
    "openai": "gpt-4o",
}


class AgentConfig(BaseSettings):
    model_config = {"env_prefix": "AGENT_"}

    llm_provider: Literal["anthropic", "openai"] = "anthropic"
    llm_model: str = ""
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_temperature: float = 0.0
    llm_max_tokens: int = 4096
    llm_timeout_seconds: int = 120

    repl_timeout_seconds: int = 120
    repl_max_output_chars: int = 50_000

    @property
    def resolved_model(self) -> str:
        return self.llm_model or _DEFAULT_MODELS[self.llm_provider]


def get_llm(config: AgentConfig | None = None) -> BaseChatModel:
    """Build a LangChain chat model from config."""
    if config is None:
        config = AgentConfig()

    kwargs: dict = {
        "model": config.resolved_model,
        "temperature": config.llm_temperature,
        "max_tokens": config.llm_max_tokens,
    }

    if config.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        if config.llm_api_key:
            kwargs["anthropic_api_key"] = config.llm_api_key
        return ChatAnthropic(**kwargs)

    # openai — covers OpenAI proper + any compatible API (Ollama, vLLM, etc.)
    from langchain_openai import ChatOpenAI

    if config.llm_base_url:
        kwargs["base_url"] = config.llm_base_url
    if config.llm_api_key:
        kwargs["api_key"] = config.llm_api_key
    kwargs["timeout"] = config.llm_timeout_seconds
    kwargs["request_timeout"] = config.llm_timeout_seconds
    return ChatOpenAI(**kwargs)
