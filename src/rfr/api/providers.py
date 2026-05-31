"""LLM provider adapters for vLLM, Ollama, LM Studio, OpenAI-compatible APIs.

Each provider wraps a specific LLM backend and returns a LangChain-compatible
ChatOpenAI instance pointed at the right endpoint. All providers use the
OpenAI-compatible protocol, so the same client library works for all.
"""

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

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        model: str = "meta-llama/Meta-Llama-3-8B-Instruct",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def get_chat_model(self) -> Any:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self.model,
            base_url=self.base_url,
            api_key="not-needed",
            temperature=0.1,
            max_tokens=1024,
        )


class OllamaProvider(LLMProvider):
    """Ollama OpenAI-compatible provider."""

    def __init__(
        self, base_url: str = "http://localhost:11434/v1", model: str = "llama3.2:3b"
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def get_chat_model(self) -> Any:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self.model,
            base_url=self.base_url,
            api_key="not-needed",
            temperature=0.1,
            max_tokens=1024,
        )


class LMStudioProvider(LLMProvider):
    """LM Studio OpenAI-compatible provider."""

    def __init__(
        self, base_url: str = "http://localhost:1234/v1", model: str = "local-model"
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def get_chat_model(self) -> Any:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self.model or "local-model",
            base_url=self.base_url,
            api_key="not-needed",
            temperature=0.1,
            max_tokens=1024,
        )


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: str = "", model: str = "gpt-4o-mini", base_url: str = "") -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/") if base_url else ""

    def get_chat_model(self) -> Any:
        from langchain_openai import ChatOpenAI

        kwargs: dict[str, Any] = {
            "model": self.model,
            "api_key": self.api_key,
            "temperature": 0.1,
            "max_tokens": 1024,
        }
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return ChatOpenAI(**kwargs)


def get_provider(
    provider_name: str,
    base_url: str = "",
    model: str = "",
    api_key: str = "",
) -> LLMProvider:
    """Factory: return the correct provider instance by name.

    Args:
        provider_name: One of 'vllm', 'ollama', 'lm-studio', 'openai', 'custom'.
        base_url: Base URL for the API endpoint.
        model: Model name to use.
        api_key: API key (required for openai, optional for others).

    Returns:
        An LLMProvider instance.

    Raises:
        ValueError: If provider_name is unknown.
    """
    providers: dict[str, type[LLMProvider]] = {
        "vllm": vLLMProvider,
        "ollama": OllamaProvider,
        "lm-studio": LMStudioProvider,
        "openai": OpenAIProvider,
        "custom": OpenAIProvider,
    }
    cls = providers.get(provider_name)
    if cls is None:
        valid = ", ".join(sorted(providers))
        msg = f"Unknown LLM provider '{provider_name}'. Valid: {valid}"
        raise ValueError(msg)

    if cls is OpenAIProvider:
        return cls(api_key=api_key, model=model, base_url=base_url)
    # All local providers accept (base_url, model) signatures
    return cls(base_url=base_url, model=model)  # type: ignore[call-arg]
