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