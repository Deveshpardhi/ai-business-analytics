import json

import pytest

from app.services.llm_client import (
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


def test_openai_provider_reads_environment_and_sends_only_verified_evidence(
    monkeypatch,
):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
    fake_client = FakeOpenAIClient()

    provider = get_configured_provider(
        client_factory=lambda api_key: fake_client,
    )
    result = provider.generate(make_prompt())

    assert provider.model == "test-model"
    assert result == {"text": "Correlation is 0.9."}
    assert fake_client.responses.request["model"] == "test-model"
    assert fake_client.responses.request["store"] is False
    assert fake_client.responses.request["instructions"] == (
        "Explain only the supplied evidence."
    )
    assert json.loads(fake_client.responses.request["input"]) == (
        make_prompt()["verified_evidence"]
    )


def test_missing_openai_credentials_are_rejected_before_client_creation(
    monkeypatch,
):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(LLMConfigurationError, match="OPENAI_API_KEY"):
        get_configured_provider()


def test_unknown_provider_is_rejected(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "unsupported")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")

    with pytest.raises(LLMConfigurationError, match="LLM_PROVIDER"):
        get_configured_provider()
