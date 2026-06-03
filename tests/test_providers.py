"""Tests for LLM provider adapters, including LM Studio support."""

from __future__ import annotations

import pytest

from rfr.api.providers import (
    LLMProvider,
    LMStudioProvider,
    OllamaProvider,
    OpenAIProvider,
    get_provider,
    vLLMProvider,
)


class TestProviderDefaults:
    """Verify each provider has sensible default endpoints and models."""

    def test_vllm_defaults(self) -> None:
        """vLLM provider should default to localhost:8000."""
        p = vLLMProvider()
        assert "8000" in p.base_url
        assert "Llama" in p.model or "llama" in p.model.lower()

    def test_ollama_defaults(self) -> None:
        """Ollama provider should default to localhost:11434."""
        p = OllamaProvider()
        assert "11434" in p.base_url
        assert p.model

    def test_lm_studio_defaults(self) -> None:
        """LM Studio provider should default to localhost:1234."""
        p = LMStudioProvider()
        assert "1234" in p.base_url
        assert p.model == "local-model"

    def test_openai_defaults(self) -> None:
        """OpenAI provider should default to gpt-4o-mini."""
        p = OpenAIProvider()
        assert "gpt-4o" in p.model

    def test_custom_base_url(self) -> None:
        """Custom base URLs should be accepted."""
        p = LMStudioProvider(base_url="http://192.168.1.100:1234/v1")
        assert "192.168.1.100" in p.base_url

    def test_custom_model(self) -> None:
        """Custom model names should be accepted."""
        p = LMStudioProvider(model="my-custom-model")
        assert p.model == "my-custom-model"

    def test_trailing_slash_stripped(self) -> None:
        """Trailing slashes on base_url should be stripped."""
        p = LMStudioProvider(base_url="http://localhost:1234/v1/")
        assert not p.base_url.endswith("/")


class TestProviderFactory:
    """Verify the get_provider factory function works correctly."""

    def test_vllm_factory(self) -> None:
        """Factory should return vLLMProvider for 'vllm'."""
        p = get_provider("vllm")
        assert isinstance(p, vLLMProvider)

    def test_ollama_factory(self) -> None:
        """Factory should return OllamaProvider for 'ollama'."""
        p = get_provider("ollama")
        assert isinstance(p, OllamaProvider)

    def test_lm_studio_factory(self) -> None:
        """Factory should return LMStudioProvider for 'lm-studio'."""
        p = get_provider("lm-studio")
        assert isinstance(p, LMStudioProvider)

    def test_openai_factory(self) -> None:
        """Factory should return OpenAIProvider for 'openai'."""
        p = get_provider("openai", api_key="test-key")
        assert isinstance(p, OpenAIProvider)

    def test_custom_factory(self) -> None:
        """Factory should return OpenAIProvider for 'custom'."""
        p = get_provider("custom", api_key="test-key")
        assert isinstance(p, OpenAIProvider)

    def test_invalid_provider_raises(self) -> None:
        """Factory should raise ValueError for unknown providers."""
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_provider("nonexistent")

    def test_factory_passes_base_url(self) -> None:
        """Factory should pass base_url to the provider."""
        p = get_provider("lm-studio", base_url="http://192.168.1.50:1234/v1")
        assert "192.168.1.50" in p.base_url

    def test_factory_passes_model(self) -> None:
        """Factory should pass model to the provider."""
        p = get_provider("ollama", model="llama3.2:1b")
        assert p.model == "llama3.2:1b"


class TestLmStudioProvider:
    """LM Studio-specific tests."""

    def test_default_port_is_1234(self) -> None:
        """LM Studio's default port should be 1234."""
        p = LMStudioProvider()
        assert ":1234" in p.base_url

    def test_default_model_is_local_model(self) -> None:
        """LM Studio's default model should indicate local loading."""
        p = LMStudioProvider()
        assert p.model == "local-model"

    def test_is_provider_subclass(self) -> None:
        """LMStudioProvider should be a proper LLMProvider."""
        p = LMStudioProvider()
        assert isinstance(p, LLMProvider)

    def test_get_chat_model_returns_instance(self) -> None:
        """get_chat_model should return a chat model instance."""
        p = LMStudioProvider()
        model = p.get_chat_model()
        # Can't test the exact type without langchain_openai installed,
        # but we can check it's not None and has expected attributes
        assert model is not None
        assert hasattr(model, "invoke")


class TestOpenAIProvider:
    """OpenAI provider-specific tests."""

    def test_empty_api_key_raises_no_error(self) -> None:
        """OpenAI provider should accept empty API key (catches setup errors)."""
        p = OpenAIProvider(api_key="")
        assert p.api_key == ""

    def test_custom_base_url(self) -> None:
        """OpenAI provider should accept custom base_url."""
        p = OpenAIProvider(api_key="sk-test", base_url="https://my-proxy.example.com/v1")
        assert "my-proxy" in p.base_url
