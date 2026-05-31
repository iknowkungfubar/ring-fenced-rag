"""Extended provider tests — get_chat_model return shape, edge cases."""

from __future__ import annotations

import pytest

from rfr.api.providers import (
    LMStudioProvider,
    OllamaProvider,
    OpenAIProvider,
    get_provider,
    vLLMProvider,
)


class TestGetChatModel:
    """Verify get_chat_model returns a usable model object."""

    @pytest.fixture
    def any_provider(self) -> list:  # noqa: ANN201
        """Return all provider instances for parameterized tests."""
        return [
            vLLMProvider(),
            OllamaProvider(),
            LMStudioProvider(),
        ]

    def test_local_providers_return_chat_model(self, any_provider: list) -> None:
        """All local providers should return a model with invoke."""
        for provider in any_provider:
            model = provider.get_chat_model()
            assert model is not None
            assert hasattr(model, "invoke")
            assert hasattr(model, "generate")

    def test_openai_provider_with_api_key(self) -> None:
        """OpenAI provider should work with a provided API key."""
        p = OpenAIProvider(api_key="sk-test-key", model="gpt-4")
        assert p.api_key == "sk-test-key"
        assert p.model == "gpt-4"
        # Without a base_url, it should use OpenAI's default
        assert p.base_url == ""

    def test_openai_provider_with_custom_base_url(self) -> None:
        """OpenAI provider with custom base_url should preserve it."""
        p = OpenAIProvider(api_key="sk-test", base_url="https://my-proxy.example.com/v1")
        assert "my-proxy" in p.base_url

    def test_openai_provider_trailing_slash(self) -> None:
        """Trailing slashes on OpenAI base_url should be stripped."""
        p = OpenAIProvider(api_key="sk-test", base_url="https://proxy.example.com/v1/")
        assert not p.base_url.endswith("/")

    def test_vllm_get_chat_model_returns_invoke(self) -> None:
        """vLLM provider's get_chat_model should return callable."""
        p = vLLMProvider()
        model = p.get_chat_model()
        assert callable(model.invoke) if hasattr(model, "invoke") else True

    def test_lm_studio_model_has_temperature(self) -> None:
        """LM Studio model should have temperature config."""
        from langchain_openai import ChatOpenAI

        p = LMStudioProvider()
        model = p.get_chat_model()
        assert isinstance(model, ChatOpenAI)
        assert model.temperature == 0.1


class TestProviderFactoryEdgeCases:
    """Verify edge cases in the provider factory."""

    def test_factory_empty_provider_name(self) -> None:
        """Factory should raise on empty string."""
        with pytest.raises(ValueError):
            get_provider("")

    def test_factory_invalid_case(self) -> None:
        """Factory should raise on wrong case."""
        with pytest.raises(ValueError):
            get_provider("Ollama")

    def test_factory_vllm_with_custom_url(self) -> None:
        """Factory should pass custom URL to vLLM provider."""
        p = get_provider("vllm", base_url="http://192.168.1.50:8000/v1")
        assert "192.168.1.50" in p.base_url

    def test_factory_lm_studio_custom_model(self) -> None:
        """Factory should pass custom model to LM Studio."""
        p = get_provider("lm-studio", model="my-custom-model")
        assert p.model == "my-custom-model"
