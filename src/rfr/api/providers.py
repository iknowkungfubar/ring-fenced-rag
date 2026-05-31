"""LLM provider adapters for vLLM, Ollama, LM Studio, and OpenAI-compatible APIs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract base for LLM provider adapters."""

    @abstractmethod
    def get_chat_model(self) -> Any:
        """Return a LangChain-compatible chat model instance."""
        ...


class vLLMProvider(LLMProvider):
    """vLLM OpenAI-compatible provider."""

    def __init__(self, base_url: str = "http://localhost:8000/v1", model: str = "") -> None:
        self.base_url = base_url
        self.model = model

    def get_chat_model(self) -> Any:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self.model or "meta-llama/Meta-Llama-3-8B-Instruct",
            base_url=self.base_url,
            api_key="not-needed",
            temperature=0.1,
            max_tokens=1024,
        )


class OllamaProvider(LLMProvider):
    """Ollama OpenAI-compatible provider."""

    def __init__(self, base_url: str = "http://localhost:11434/v1", model: str = "") -> None:
        self.base_url = base_url
        self.model = model

    def get_chat_model(self) -> Any:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self.model or "llama3.2:3b",
            base_url=self.base_url,
            api_key="not-needed",
            temperature=0.1,
            max_tokens=1024,
        )


class OpenAIProvider(LLMProvider):
    """OpenAI API provider (requires explicit opt-in — data leaves your network)."""

    def __init__(self, api_key: str = "", model: str = "") -> None:
        self.api_key = api_key
        self.model = model

    def get_chat_model(self) -> Any:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self.model or "gpt-4o-mini",
            api_key=self.api_key,
            temperature=0.1,
            max_tokens=1024,
        )
