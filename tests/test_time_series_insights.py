from app.services.confidence_engine import (
    apply_confidence,
)
from app.services.insight_discovery import (
    discover_insights,
)
from app.services.insight_explainer import (
    build_verified_evidence_context,
)
from app.services.insight_scorer import (
    score_insights,
)
from app.services.insight_verifier import (
    verify_insights,
)
from app.services.time_series_metrics import (
    calculate_time_series_metrics,
)


def make_time_series():
    return {
        "type": "time_series",
        "measure": "Revenue",
        "date": "Date",
        "data": [
            {
                "Date": "2026-01-01",
                "Revenue": 100.0,
            },
            {
                "Date": "2026-02-01",
                "Revenue": 120.0,
            },
            {
                "Date": "2026-03-01",
                "Revenue": 140.0,
            },
            {
                "Date": "2026-04-01",
                "Revenue": 160.0,
            },
        ],
        "sample_size": 4,
        "method": "sorted_time_series",
    }


def test_time_series_metrics_are_deterministic():
    result = make_time_series()

    first = (
        calculate_time_series_metrics(
            result["data"],
            result["measure"],
            result["date"],
        )
    )

    second = (
        calculate_time_series_metrics(
            result["data"],
            result["measure"],
            result["date"],
        )
    )

    assert first == second

    assert (
        first["trend_direction"]
        == "rising"
    )

    assert (
        first["absolute_change"]
        == 60.0
    )

    assert (
        first["percentage_change"]
        == 60.0
    )

    assert (
        first["peak_value"]
        == 160.0
    )

    assert (
        first["trough_value"]
        == 100.0
    )

    assert (
        first["latest_moving_average"]
        == 140.0
    )


def test_time_series_insight_is_discovered():
    result = make_time_series()

    insights = discover_insights(
        [result]
    )

    assert len(insights) == 1

    insight = insights[0]

    assert (
        insight["insight_type"]
        == "time_series_trend"
    )

    assert (
        insight["evidence"][
            "trend_direction"
        ]
        == "rising"
    )

    assert (
        insight["source_columns"]
        == [
            "Revenue",
            "Date",
        ]
    )


def test_time_series_insight_is_verified():
    result = make_time_series()

    insight = discover_insights(
        [result]
    )[0]

    verified = verify_insights(
        [insight],
        [result],
    )[0]

    assert (
        verified[
            "verification"
        ]["status"]
        == "verified"
    )

    assert (
        verified[
            "verification"
        ]["sample_size"]
        == 4
    )


def test_time_series_tampering_is_rejected():
    result = make_time_series()

    insight = discover_insights(
        [result]
    )[0]

    insight["evidence"][
        "last_value"
    ] = 999999.0

    verified = verify_insights(
        [insight],
        [result],
    )[0]

    assert (
        verified[
            "verification"
        ]["status"]
        == "failed"
    )


def test_short_time_series_is_not_discovered():
    result = make_time_series()

    result["data"] = (
        result["data"][:2]
    )

    result["sample_size"] = 2

    insights = discover_insights(
        [result]
    )

    assert insights == []


def test_verified_time_series_gets_confidence_and_score():
    result = make_time_series()

    insight = discover_insights(
        [result]
    )[0]

    verified = verify_insights(
        [insight],
        [result],
    )

    confidence = apply_confidence(
        verified
    )

    scored = score_insights(
        confidence
    )

    assert (
        scored[0][
            "confidence"
        ]["score"]
        > 0
    )

    assert (
        scored[0]["score"]
        > 0
    )


def test_time_series_calculation_stays_out_of_llm_boundary():
    result = make_time_series()

    insight = discover_insights(
        [result]
    )[0]

    verified = verify_insights(
        [insight],
        [result],
    )[0]

    context = (
        build_verified_evidence_context(
            verified
        )
    )

    assert (
        "calculation"
        not in context
    )

    assert (
        context[
            "insight_type"
        ]
        == "time_series_trend"
    )

    assert (
        context[
            "evidence"
        ]["trend_direction"]
        == "rising"
    )
