from app.services.insight_explainer import explain_insight
from app.services.numeric_guardrail import extract_numbers


def make_insight():
    return {
        "insight_type": "correlation",
        "evidence": {
            "column_a": "Age",
            "column_b": "Salary",
            "correlation": 0.9062919244242602,
            "p_value": 0.00030088019266998647,
            "sample_size": 10,
        },
        "verification": {
            "status": "verified",
        },
    }


def test_extract_numbers_from_decimal_text():
    numbers = extract_numbers(
        "correlation = 0.9062919244242602"
    )

    assert numbers == [0.9062919244242602]


def test_valid_explanation_is_approved():
    def good_llm(prompt):
        return {
            "text": (
                "Age and Salary have a strong positive relationship. "
                "The correlation is 0.9062919244242602. "
                "The sample contains 10 observations."
            )
        }

    result = explain_insight(
        make_insight(),
        good_llm,
    )

    assert result["status"] == "approved"
    assert result["validation"]["valid"] is True
    assert result["validation"]["unsupported_numbers"] == []


def test_invented_number_is_rejected():
    def bad_llm(prompt):
        return {
            "text": (
                "Age and Salary have a strong relationship. "
                "The correlation is 0.9062919244242602. "
                "The expected salary increase is 25%."
            )
        }

    result = explain_insight(
        make_insight(),
        bad_llm,
    )

    assert result["status"] == "rejected"
    assert result["validation"]["valid"] is False
    assert 25.0 in result["validation"]["unsupported_numbers"]


def test_modified_authoritative_number_is_rejected():
    def rounding_llm(prompt):
        return {
            "text": "The correlation is 0.90 across 10 observations."
        }

    result = explain_insight(make_insight(), rounding_llm)

    assert result["status"] == "rejected"
    assert 0.90 in result["validation"]["unsupported_numbers"]


def test_only_whitelisted_verified_evidence_is_sent_to_llm():
    insight = {
        "insight_type": "correlation",
        "title": "Age and Salary move together",
        "source_columns": ["Age", "Salary"],
        "method": "pearson_correlation",
        "evidence": {"correlation": 0.9, "sample_size": 10},
        "verification": {"status": "verified"},
        "limitations": ["Correlation does not establish causation."],
        "calculation": {"internal_value": 999},
        "confidence": {"score": 0.95},
        "lineage": {"dataset_id": "dataset-secret"},
        "raw_dataset": [{"Email": "person@example.com"}],
        "explanation": {"text": "old explanation"},
        "recommendation": {"action": "old recommendation"},
    }
    captured = {}

    def capturing_llm(prompt):
        captured.update(prompt)
        prompt["verified_evidence"]["evidence"]["correlation"] = 123
        return {"text": "The correlation is 0.9 across 10 observations."}

    result = explain_insight(insight, capturing_llm)

    assert result["status"] == "approved"
    assert set(captured["verified_evidence"]) == {
        "insight_type",
        "title",
        "source_columns",
        "method",
        "evidence",
        "verification",
        "limitations",
    }
    assert "raw_dataset" not in captured["verified_evidence"]
    assert "person@example.com" not in str(captured["verified_evidence"])
    assert insight["evidence"]["correlation"] == 0.9


def test_unverified_insight_never_calls_llm():
    called = False
    insight = make_insight()
    insight["verification"] = {"status": "failed"}

    def llm_should_not_run(prompt):
        nonlocal called
        called = True
        return {"text": "This should not be generated."}

    result = explain_insight(insight, llm_should_not_run)

    assert result["status"] == "rejected"
    assert result["validation"]["reason"] == "insight_not_verified"
    assert called is False


def test_malformed_llm_response_is_rejected():
    result = explain_insight(make_insight(), lambda prompt: {"body": "Missing text"})

    assert result["status"] == "rejected"
    assert result["validation"]["reason"] == "invalid_response"


def test_llm_failure_is_reported_without_raising():
    def unavailable_llm(prompt):
        raise RuntimeError("provider timeout")

    result = explain_insight(make_insight(), unavailable_llm)

    assert result == {
        "status": "unavailable",
        "explanation": None,
        "validation": {
            "valid": False,
            "reason": "llm_unavailable",
            "unsupported_numbers": [],
        },
    }


def test_missing_provider_credentials_return_unavailable(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = explain_insight(make_insight())

    assert result["status"] == "unavailable"
    assert result["validation"]["reason"] == "llm_unavailable"


def test_configured_provider_exception_returns_unavailable(monkeypatch):
    from app.services import llm_client
    from app.services.llm_client import OpenAIExplanationProvider

    class FailingResponses:
        def create(self, **kwargs):
            raise RuntimeError("provider timeout")

    class FailingClient:
        responses = FailingResponses()

    provider = OpenAIExplanationProvider(
        api_key="test-api-key",
        model="test-model",
        client_factory=lambda api_key: FailingClient(),
    )
    monkeypatch.setattr(llm_client, "get_configured_provider", lambda: provider)

    result = explain_insight(make_insight())

    assert result["status"] == "unavailable"
    assert result["validation"]["reason"] == "llm_unavailable"


def test_correlation_explanation_uses_source_columns():
    from app.services.insight_explainer import explain_insight, mock_llm

    insight = {
        "insight_type": "correlation",
        "source_columns": ["Age", "Salary"],
        "evidence": {
            "correlation": 0.90629192442426,
            "p_value": 0.000300880192669986,
            "sample_size": 10,
        },
        "verification": {
            "status": "verified",
        },
    }

    result = explain_insight(
        insight,
        mock_llm,
    )

    text = result["explanation"]["text"]

    assert "Age" in text
    assert "Salary" in text
    assert "None" not in text

def test_extract_numbers_from_scientific_notation():
    from app.services.numeric_guardrail import extract_numbers

    result = extract_numbers("p-value is 1.3699559531952885e-19")

    assert result == [1.3699559531952885e-19]
