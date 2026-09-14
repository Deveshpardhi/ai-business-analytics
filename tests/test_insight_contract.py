from app.schemas.insight import InsightContract


def test_valid_insight_contract():
    insight = InsightContract(
        insight_type="correlation",
        title="Age and Salary have a strong positive relationship",
        source_columns=["Age", "Salary"],
        method="pearson_correlation",
        evidence={
            "correlation": 0.9062919244242602,
            "p_value": 0.00030088019266998647,
            "sample_size": 10,
        },
        calculation={
            "formula": "Pearson correlation coefficient",
            "value": 0.9062919244242602,
        },
        verification={
            "status": "verified",
        },
        confidence={
            "level": "high",
            "score": 0.8919,
        },
        limitations=[
            "Correlation does not imply causation.",
        ],
    )

    assert insight.insight_type == "correlation"
    assert insight.source_columns == ["Age", "Salary"]
    assert insight.verification["status"] == "verified"
