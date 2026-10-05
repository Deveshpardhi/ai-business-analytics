import os
from types import SimpleNamespace

import pytest

from app.services.llm_client import (
    AzureOpenAIExplanationProvider,
    GeminiExplanationProvider,
    LLMConfigurationError,
    generate_explanation,
    get_configured_provider,
)


class FakeGeminiModels:
    def __init__(self):
        self.calls = []

    def generate_content(
        self,
        model,
        contents,
    ):
        self.calls.append(
            {
                "model": model,
                "contents": contents,
            }
        )

        return SimpleNamespace(
            text="Verified explanation"
        )


class FakeGeminiClient:
    def __init__(self):
        self.models = FakeGeminiModels()


def test_get_configured_provider_returns_gemini_provider(
    monkeypatch,
):
    monkeypatch.setenv(
        "LLM_PROVIDER",
        "gemini",
    )

    monkeypatch.setenv(
        "LLM_MODEL",
        "gemini-3.6-flash",
    )

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    provider = get_configured_provider()

    assert isinstance(
        provider,
        GeminiExplanationProvider,
    )

    assert (
        provider.model
        == "gemini-3.6-flash"
    )

    assert (
        provider.api_key
        == "test-key"
    )


def test_get_configured_provider_requires_gemini_api_key(
    monkeypatch,
):
    monkeypatch.setenv(
        "LLM_PROVIDER",
        "gemini",
    )

    monkeypatch.setenv(
        "LLM_MODEL",
        "gemini-3.6-flash",
    )

    monkeypatch.delenv(
        "GEMINI_API_KEY",
        raising=False,
    )

    with pytest.raises(
        LLMConfigurationError,
        match="GEMINI_API_KEY is required",
    ):
        get_configured_provider()


def test_gemini_provider_generates_expected_response():
    fake_client = FakeGeminiClient()

    def fake_client_factory(
        api_key,
    ):
        assert api_key == "test-key"

        return fake_client

    provider = GeminiExplanationProvider(
        api_key="test-key",
        model="gemini-3.6-flash",
        client_factory=fake_client_factory,
    )

    prompt = {
        "instruction": (
            "Explain clearly and preserve numbers."
        ),
        "verified_evidence": {
            "insight_type": "correlation",
            "title": "Age and Salary",
            "source_columns": [
                "Age",
                "Salary",
            ],
            "method": "pearson_correlation",
            "evidence": {
                "correlation": 0.9,
                "sample_size": 10,
            },
            "verification": {
                "status": "verified",
            },
            "limitations": [],
        },
    }

    result = provider.generate(
        prompt
    )

    assert result == {
        "text": "Verified explanation",
    }

    assert len(
        fake_client.models.calls
    ) == 1

    call = (
        fake_client.models.calls[0]
    )

    assert (
        call["model"]
        == "gemini-3.6-flash"
    )

    assert (
        "Explain clearly and preserve numbers."
        in call["contents"]
    )

    assert (
        '"correlation": 0.9'
        in call["contents"]
    )

    assert (
        '"sample_size": 10'
        in call["contents"]
    )


def test_generate_explanation_uses_configured_gemini_provider(
    monkeypatch,
):
    fake_client = FakeGeminiClient()

    def fake_client_factory(
        api_key,
    ):
        return fake_client

    monkeypatch.setenv(
        "LLM_PROVIDER",
        "gemini",
    )

    monkeypatch.setenv(
        "LLM_MODEL",
        "gemini-3.6-flash",
    )

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    provider = get_configured_provider(
        client_factory=fake_client_factory,
    )

    prompt = {
        "instruction": "Explain.",
        "verified_evidence": {
            "insight_type": "correlation",
            "title": "Test",
            "source_columns": [
                "A",
                "B",
            ],
            "method": "pearson_correlation",
            "evidence": {
                "correlation": 0.8,
            },
            "verification": {
                "status": "verified",
            },
            "limitations": [],
        },
    }

    result = provider.generate(
        prompt
    )

    assert result == {
        "text": "Verified explanation",
    }


def test_generate_explanation_still_supports_injected_llm_function():
    prompt = {
        "instruction": "Explain.",
        "verified_evidence": {},
    }

    result = generate_explanation(
        prompt,
        lambda received_prompt: {
            "text": (
                "Injected explanation"
            )
        },
    )

    assert result == {
        "text": "Injected explanation",
    }


def test_get_configured_provider_still_supports_azure_openai(
    monkeypatch,
):
    monkeypatch.setenv(
        "LLM_PROVIDER",
        "azure_openai",
    )

    monkeypatch.setenv(
        "LLM_MODEL",
        "gpt-4o-mini",
    )

    monkeypatch.setenv(
        "AZURE_OPENAI_API_KEY",
        "azure-test-key",
    )

    monkeypatch.setenv(
        "AZURE_OPENAI_ENDPOINT",
        "https://example.openai.azure.com/",
    )

    provider = get_configured_provider()

    assert isinstance(
        provider,
        AzureOpenAIExplanationProvider,
    )

    assert (
        provider.api_key
        == "azure-test-key"
    )

    assert (
        provider.endpoint
        == "https://example.openai.azure.com/"
    )

    assert (
        provider.model
        == "gpt-4o-mini"
    )


def test_get_configured_provider_requires_model(
    monkeypatch,
):
    monkeypatch.setenv(
        "LLM_PROVIDER",
        "gemini",
    )

    monkeypatch.delenv(
        "LLM_MODEL",
        raising=False,
    )

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    with pytest.raises(
        LLMConfigurationError,
        match="LLM_MODEL is required",
    ):
        get_configured_provider()


def test_get_configured_provider_rejects_unknown_provider(
    monkeypatch,
):
    monkeypatch.setenv(
        "LLM_PROVIDER",
        "unknown",
    )

    monkeypatch.setenv(
        "LLM_MODEL",
        "test-model",
    )

    with pytest.raises(
        LLMConfigurationError,
        match=(
            "LLM_PROVIDER must be set to "
            "'azure_openai' or 'gemini'"
        ),
    ):
        get_configured_provider()