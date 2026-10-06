import polars as pl

from app.services.analytics_executor import correlation
from app.services.insight_discovery import discover_insights
from app.services.insight_explainer import (
    build_verified_evidence_context,
)
from app.services.insight_verifier import verify_insight


def test_correlation_returns_exact_scatter_points():
    df = pl.DataFrame(
        {
            "Age": [20, 30, 40, 50],
            "Salary": [30000, 45000, 60000, 75000],
        }
    )

    result = correlation(df, "Age", "Salary")

    assert result["visualization"] == {
        "type": "scatter",
        "x_column": "Age",
        "y_column": "Salary",
        "points": [
            {"x": 20, "y": 30000},
            {"x": 30, "y": 45000},
            {"x": 40, "y": 60000},
            {"x": 50, "y": 75000},
        ],
        "total_points": 4,
        "displayed_points": 4,
        "sampled": False,
    }


def test_scatter_uses_the_same_complete_pairs_as_correlation():
    df = pl.DataFrame(
        {
            "Age": [20, None, 40, 50, 60],
            "Salary": [30000, 45000, None, 75000, 90000],
        }
    )

    result = correlation(df, "Age", "Salary")

    assert result["sample_size"] == 3
    assert result["visualization"] == {
        "type": "scatter",
        "x_column": "Age",
        "y_column": "Salary",
        "points": [
            {"x": 20, "y": 30000},
            {"x": 50, "y": 75000},
            {"x": 60, "y": 90000},
        ],
        "total_points": 3,
        "displayed_points": 3,
        "sampled": False,
    }


def test_scatter_sampling_is_deterministic_and_capped_at_200_points():
    df = pl.DataFrame(
        {
            "Age": list(range(401)),
            "Salary": [value * 1000 for value in range(401)],
        }
    )

    first_result = correlation(df, "Age", "Salary")
    second_result = correlation(df, "Age", "Salary")
    visualization = first_result["visualization"]

    assert visualization == second_result["visualization"]
    assert visualization["total_points"] == 401
    assert visualization["displayed_points"] == 200
    assert visualization["sampled"] is True
    assert len(visualization["points"]) == 200
    assert visualization["points"][0] == {"x": 0, "y": 0}
    assert visualization["points"][-1] == {
        "x": 400,
        "y": 400000,
    }


def test_visualization_stays_in_calculation_and_out_of_llm_context():
    df = pl.DataFrame(
        {
            "Age": [20, 30, 40, 50],
            "Salary": [30000, 45000, 60000, 75000],
        }
    )
    result = correlation(df, "Age", "Salary")
    insight = discover_insights([result])[0]

    assert "visualization" not in insight["evidence"]
    assert insight["calculation"]["visualization"] == result[
        "visualization"
    ]

    verified = verify_insight(insight, result)
    context = build_verified_evidence_context(verified)

    assert verified["verification"]["status"] == "verified"
    assert "calculation" not in context
    assert "visualization" not in context
