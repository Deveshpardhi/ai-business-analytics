import json

import pytest

from app.services.llm_client import (
    AzureOpenAIExplanationProvider,
    LLMConfigurationError,
    get_configured_provider,
)


def make_prompt():
    return {
        "instruction": "Explain only the supplied evidence.",
        "verified_evidence": {
            "insight_type": "correlation",
            "title": "Age and Salary move together",
            "source_columns": ["Age", "Salary"],
            "method": "pearson_correlation",
            "evidence": {"correlation": 0.9, "sample_size": 10},
            "verification": {"status": "verified"},
            "limitations": ["Correlation does not establish causation."],
        },
    }


class FakeResponses:
    def __init__(self):
        self.request = None

    def create(self, **kwargs):
        self.request = kwargs
        return type("Response", (), {"output_text": "Correlation is 0.9."})()


class FakeOpenAIClient:
    def __init__(self):
        self.responses = FakeResponses()


def test_azure_provider_reads_environment_and_sends_only_verified_evidence(
    monkeypatch,
):
    monkeypatch.setenv("LLM_PROVIDER", "azure_openai")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-api-key")
    monkeypatch.setenv(
        "AZURE_OPENAI_ENDPOINT",
        "https://example.openai.azure.com",
    )

    fake_client = FakeOpenAIClient()

    provider = get_configured_provider(
        client_factory=lambda api_key, endpoint: fake_client,
    )

    result = provider.generate(make_prompt())

    assert isinstance(provider, AzureOpenAIExplanationProvider)
    assert provider.model == "test-model"
    assert provider.endpoint == "https://example.openai.azure.com"
    assert result == {"text": "Correlation is 0.9."}

    assert fake_client.responses.request["model"] == "test-model"
    assert fake_client.responses.request["store"] is False
    assert fake_client.responses.request["instructions"] == (
        "Explain only the supplied evidence."
    )

    assert json.loads(fake_client.responses.request["input"]) == (
        make_prompt()["verified_evidence"]
    )


def test_missing_azure_credentials_are_rejected_before_client_creation(
    monkeypatch,
):
    monkeypatch.setenv("LLM_PROVIDER", "azure_openai")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.setenv(
        "AZURE_OPENAI_ENDPOINT",
        "https://example.openai.azure.com",
    )

    with pytest.raises(
        LLMConfigurationError,
        match="AZURE_OPENAI_API_KEY",
    ):
        get_configured_provider()


def test_missing_azure_endpoint_is_rejected(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "azure_openai")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-api-key")
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)

    with pytest.raises(
        LLMConfigurationError,
        match="AZURE_OPENAI_ENDPOINT",
    ):
        get_configured_provider()


def test_unknown_provider_is_rejected(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "unsupported")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    with pytest.raises(LLMConfigurationError, match="LLM_PROVIDER"):
        get_configured_provider()
