from app.services.recommendation_engine import (
    recommend_insight,
    mock_recommendation_llm,
)


def make_correlation_insight():
    return {
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


def test_correlation_recommendation_is_generated():
    result = recommend_insight(
        make_correlation_insight(),
        mock_recommendation_llm,
    )

    assert result["status"] == "generated"
    assert "Age" in result["recommendation"]["action"]
    assert "Salary" in result["recommendation"]["action"]


def test_correlation_recommendation_does_not_claim_causation():
    result = recommend_insight(
        make_correlation_insight(),
        mock_recommendation_llm,
    )

    reason = result["recommendation"]["reason"]

    assert "causation" in reason
