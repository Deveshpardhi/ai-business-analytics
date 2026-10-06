def score_insight(insight: dict) -> dict:
    insight_type = insight["insight_type"]

    if insight_type == "group_difference":
        return score_group_difference(insight)

    if insight_type == "correlation":
        return score_correlation(insight)

    if insight_type == "outlier":
        return score_outlier(insight)

    if (insight_type== "time_series_trend"):
        return (
            score_time_series_trend(
                insight
            )
        )

    return {
        **insight,
        "score": 0.0,
        "score_components": {},
    }


def get_verification_score(insight: dict) -> float:
    verification = insight.get("verification", {})
    status = verification.get("status")

    if status == "verified":
        return 1.0

    if status == "not_significant":
        return 0.0

    if status == "insufficient_data":
        return 0.0

    if status == "failed":
        return 0.0

    return 0.0

def is_rankable_insight(insight: dict) -> bool:
    verification = insight.get("verification", {})
    status = verification.get("status")
    return status == "verified"

def score_group_difference(insight: dict) -> dict:
    evidence = insight["evidence"]

    percentage_difference = evidence.get(
        "percentage_difference"
    )

    magnitude_score = (
        0.0
        if percentage_difference is None
        else min(
            abs(percentage_difference) / 100,
            1.0,
        )
    )

    business_impact_score = magnitude_score

    verification_score = get_verification_score(
        insight
    )

    confidence_score = get_confidence_score(
        insight
    )

    novelty_score = 0.5

    score = (
        magnitude_score * 0.30
        + business_impact_score * 0.15
        + verification_score * 0.20
        + confidence_score * 0.25
        + novelty_score * 0.10
    )

    return {
        **insight,
        "score": round(score, 4),
        "score_components": {
            "magnitude": round(
                magnitude_score,
                4,
            ),
            "business_impact": round(
                business_impact_score,
                4,
            ),
            "verification": round(
                verification_score,
                4,
            ),
            "confidence": round(
                confidence_score,
                4,
            ),
            "novelty": round(
                novelty_score,
                4,
            ),
        },
    }


def score_correlation(insight: dict) -> dict:
    evidence = insight["evidence"]

    correlation = evidence.get("correlation")

    strength_score = (
        0.0
        if correlation is None
        else abs(correlation)
    )

    business_impact_score = strength_score

    verification_score = get_verification_score(
        insight
    )

    confidence_score = get_confidence_score(
        insight
    )

    novelty_score = 0.5

    score = (
        strength_score * 0.30
        + business_impact_score * 0.15
        + verification_score * 0.20
        + confidence_score * 0.25
        + novelty_score * 0.10
    )

    return {
        **insight,
        "score": round(score, 4),
        "score_components": {
            "statistical_strength": round(
                strength_score,
                4,
            ),
            "business_impact": round(
                business_impact_score,
                4,
            ),
            "verification": round(
                verification_score,
                4,
            ),
            "confidence": round(
                confidence_score,
                4,
            ),
            "novelty": round(
                novelty_score,
                4,
            ),
        },
    }

def score_time_series_trend(
    insight: dict,
) -> dict:
    evidence = insight[
        "evidence"
    ]

    percentage_change = (
        evidence.get(
            "percentage_change"
        )
    )

    r_squared = evidence.get(
        "r_squared",
        0.0,
    )

    magnitude_score = (
        0.0
        if percentage_change is None
        else min(
            abs(
                percentage_change
            )
            / 100,
            1.0,
        )
    )

    trend_score = min(
        max(
            float(
                r_squared or 0.0
            ),
            0.0,
        ),
        1.0,
    )

    verification_score = (
        get_verification_score(
            insight
        )
    )

    confidence_score = (
        get_confidence_score(
            insight
        )
    )

    business_impact_score = (
        magnitude_score
    )

    novelty_score = 0.5

    score = (
        magnitude_score * 0.25
        + trend_score * 0.20
        + business_impact_score * 0.15
        + verification_score * 0.15
        + confidence_score * 0.20
        + novelty_score * 0.05
    )

    return {
        **insight,
        "score": round(
            score,
            4,
        ),
        "score_components": {
            "magnitude": round(
                magnitude_score,
                4,
            ),
            "trend_fit": round(
                trend_score,
                4,
            ),
            "business_impact": round(
                business_impact_score,
                4,
            ),
            "verification": round(
                verification_score,
                4,
            ),
            "confidence": round(
                confidence_score,
                4,
            ),
            "novelty": round(
                novelty_score,
                4,
            ),
        },
    }

def score_outlier(insight: dict) -> dict:
    evidence = insight["evidence"]

    outlier_count = evidence.get(
        "outlier_count",
        0,
    )

    if outlier_count == 0:
        magnitude_score = 0.0
    elif outlier_count == 1:
        magnitude_score = 0.70
    elif outlier_count <= 3:
        magnitude_score = 0.75
    else:
        magnitude_score = 0.80

    business_impact_score = magnitude_score

    verification_score = get_verification_score(
        insight
    )

    confidence_score = get_confidence_score(
        insight
    )

    novelty_score = 0.5

    score = (
        magnitude_score * 0.30
        + business_impact_score * 0.15
        + verification_score * 0.20
        + confidence_score * 0.25
        + novelty_score * 0.10
    )

    return {
        **insight,
        "score": round(score, 4),
        "score_components": {
            "magnitude": round(
                magnitude_score,
                4,
            ),
            "business_impact": round(
                business_impact_score,
                4,
            ),
            "verification": round(
                verification_score,
                4,
            ),
            "confidence": round(
                confidence_score,
                4,
            ),
            "novelty": round(
                novelty_score,
                4,
            ),
        },
    }


def score_insights(insights: list[dict]) -> list[dict]:
    """
    Calculate a deterministic score for every verified insight.
    """
    return [
        score_insight(insight)
        for insight in insights
    ]


def rank_insights(scored_insights: list[dict]) -> list[dict]:
    """
    Rank only insights that have sufficient evidence
    for ranking.
    """

    rankable_insights = [
        insight
        for insight in scored_insights
        if is_rankable_insight(insight)
    ]

    return sorted(
        rankable_insights,
        key=lambda x: x["score"],
        reverse=True,
    )

def get_confidence_score(insight: dict) -> float:
    confidence = insight.get("confidence", {})
    return float(confidence.get("score", 0.0))