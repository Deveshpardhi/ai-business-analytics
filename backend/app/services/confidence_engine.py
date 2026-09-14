def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(value, maximum))


def sample_size_score(sample_size: int | None) -> float:
    if sample_size is None:
        return 0.0

    if sample_size < 5:
        return 0.2
    if sample_size < 10:
        return 0.4
    if sample_size < 30:
        return 0.6
    if sample_size < 100:
        return 0.8

    return 1.0


def p_value_score(p_value: float | None) -> float:
    if p_value is None:
        return 0.0

    if p_value < 0.001:
        return 1.0
    if p_value < 0.01:
        return 0.9
    if p_value < 0.05:
        return 0.75
    if p_value < 0.10:
        return 0.4

    return 0.0


def correlation_strength_score(correlation: float | None) -> float:
    if correlation is None:
        return 0.0

    return clamp(abs(correlation))


def calculate_confidence(insight: dict) -> dict:
    insight_type = insight.get("insight_type")
    verification = insight.get("verification", {})

    verification_status = verification.get("status")

    # Failed or insufficient insights cannot have meaningful confidence.
    if verification_status in {"failed", "insufficient_data"}:
        return {
            "level": "low",
            "score": 0.0,
            "reason": verification_status,
        }

    if insight_type == "correlation":
        return calculate_correlation_confidence(insight)

    if insight_type == "group_difference":
        return calculate_group_confidence(insight)

    if insight_type == "outlier":
        return calculate_outlier_confidence(insight)

    return {
        "level": "low",
        "score": 0.0,
        "reason": "Unsupported insight type",
    }


def calculate_correlation_confidence(insight: dict) -> dict:
    evidence = insight.get("evidence", {})
    verification = insight.get("verification", {})

    correlation = evidence.get("correlation")
    p_value = verification.get("p_value", evidence.get("p_value"))
    sample_size = verification.get(
        "sample_size",
        evidence.get("sample_size"),
    )

    strength_score = correlation_strength_score(correlation)
    significance_score = p_value_score(p_value)
    sample_score = sample_size_score(sample_size)

    verification_score = (
        1.0
        if verification.get("status") == "verified"
        else 0.0
    )

    score = (
        strength_score * 0.30
        + significance_score * 0.30
        + sample_score * 0.20
        + verification_score * 0.20
    )

    score = round(clamp(score), 4)

    return {
        "level": confidence_level(score),
        "score": score,
        "factors": {
            "effect_strength": round(strength_score, 4),
            "statistical_significance": round(significance_score, 4),
            "sample_size": round(sample_score, 4),
            "verification": round(verification_score, 4),
        },
        "p_value": p_value,
        "sample_size": sample_size,
        "alpha": 0.05,
    }


def calculate_group_confidence(insight: dict) -> dict:
    evidence = insight.get("evidence", {})
    verification = insight.get("verification", {})

    p_value = verification.get(
        "p_value",
        evidence.get("p_value"),
    )

    group_sizes = verification.get("group_sizes", {})

    if group_sizes:
        minimum_group_size = min(group_sizes.values())
    else:
        minimum_group_size = 0

    significance_score = p_value_score(p_value)
    sample_score = sample_size_score(minimum_group_size)

    percentage_difference = evidence.get("percentage_difference")

    if percentage_difference is None:
        effect_score = 0.0
    else:
        effect_score = clamp(abs(percentage_difference) / 100)

    verification_score = (
        1.0
        if verification.get("status") in {"verified", "not_significant"}
        else 0.0
    )

    score = (
        effect_score * 0.30
        + significance_score * 0.25
        + sample_score * 0.25
        + verification_score * 0.20
    )

    score = round(clamp(score), 4)

    return {
        "level": confidence_level(score),
        "score": score,
        "factors": {
            "effect_strength": round(effect_score, 4),
            "statistical_significance": round(significance_score, 4),
            "minimum_group_sample_size": round(sample_score, 4),
            "verification": round(verification_score, 4),
        },
        "p_value": p_value,
        "minimum_group_size": minimum_group_size,
        "alpha": 0.05,
    }


def calculate_outlier_confidence(insight: dict) -> dict:
    verification = insight.get("verification", {})
    evidence = insight.get("evidence", {})

    verification_score = (
        1.0
        if verification.get("status") == "verified"
        else 0.0
    )

    outlier_count = evidence.get("outlier_count", 0)

    detection_score = 1.0 if outlier_count > 0 else 0.0

    score = (
        detection_score * 0.60
        + verification_score * 0.40
    )

    score = round(clamp(score), 4)

    return {
        "level": confidence_level(score),
        "score": score,
        "factors": {
            "deterministic_detection": detection_score,
            "verification": verification_score,
        },
        "method": "IQR",
        "interpretation": (
            "High confidence that the value satisfies the IQR "
            "outlier rule; this does not establish that the value "
            "is a business error."
        ),
    }


def confidence_level(score: float) -> str:
    if score >= 0.80:
        return "high"

    if score >= 0.60:
        return "medium"

    return "low"


def apply_confidence(insights: list[dict]) -> list[dict]:
    results = []

    for insight in insights:
        confidence = calculate_confidence(insight)

        results.append({
            **insight,
            "confidence": confidence,
        })

    return results