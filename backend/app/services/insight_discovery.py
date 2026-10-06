from app.schemas.insight import InsightContract


def validate_insight(insight: dict) -> dict:
    validated = InsightContract(**insight)
    return validated.model_dump()


def discover_insights(analysis_results: list[dict]) -> list[dict]:
    insights = []

    for result in analysis_results:
        analysis_type = result.get("type")

        if analysis_type == "group_comparison":
            discovered = discover_group_insights(result)

            for insight in discovered:
                insights.append(validate_insight(insight))

        elif analysis_type == "correlation":
            insight = discover_correlation_insight(result)

            if insight:
                insights.append(validate_insight(insight))

        elif analysis_type == "descriptive_statistics":
            insight = discover_outlier_insight(result)

            if insight:
                insights.append(validate_insight(insight))

    return insights


def discover_group_insights(result: dict) -> list[dict]:
    groups = result.get("groups", [])

    if len(groups) < 2:
        return []

    measure = result["measure"]
    dimension = result["dimension"]

    highest = max(groups, key=lambda x: x["mean"])
    lowest = min(groups, key=lambda x: x["mean"])

    highest_mean = highest["mean"]
    lowest_mean = lowest["mean"]

    if lowest_mean == 0:
        percentage_difference = None
    else:
        percentage_difference = (
            (highest_mean - lowest_mean)
            / abs(lowest_mean)
        ) * 100

    statistical_test = result.get("statistical_test")

    evidence = {
        "highest_group": highest[dimension],
        "highest_value": highest_mean,
        "lowest_group": lowest[dimension],
        "lowest_value": lowest_mean,
        "absolute_difference": highest_mean - lowest_mean,
        "percentage_difference": percentage_difference,
    }

    if statistical_test:
        evidence["statistical_test"] = statistical_test.get("test")
        evidence["statistic"] = statistical_test.get("statistic")
        evidence["p_value"] = statistical_test.get("p_value")

    return [{
        "insight_type": "group_difference",
        "title": f"{highest[dimension]} has the highest average {measure}",
        "evidence": evidence,
        "calculation": {
            "comparison": "highest_group_mean - lowest_group_mean",
            "absolute_difference": highest_mean - lowest_mean,
            "percentage_difference": percentage_difference,
        },
        "confidence": {
            "level": "pending_verification",
            "p_value": (
                statistical_test.get("p_value")
                if statistical_test
                else None
            ),
            "alpha": 0.05,
        },
        "source_columns": [measure, dimension],
        "method": "group_mean_comparison",
        "limitations": [
            "Group-level differences may be affected by sample size.",
            "A difference in averages does not establish causation.",
            "Statistical significance requires sufficient observations per group.",
        ],
    }]


def discover_correlation_insight(result: dict) -> dict | None:
    correlation = result.get("correlation")

    if correlation is None:
        return None

    strength = abs(correlation)

    if strength >= 0.8:
        strength_label = "strong"
    elif strength >= 0.5:
        strength_label = "moderate"
    elif strength >= 0.3:
        strength_label = "weak"
    else:
        return None

    direction = "positive" if correlation > 0 else "negative"

    p_value = result.get("p_value")
    sample_size = result.get("sample_size")

    evidence = {
        "correlation": correlation,
        "strength": strength_label,
        "direction": direction,
        "p_value": p_value,
        "sample_size": sample_size,
    }

    return {
        "insight_type": "correlation",
        "title": (
            f"{result['columns'][0]} and "
            f"{result['columns'][1]} have a "
            f"{strength_label} {direction} relationship"
        ),
        "evidence": evidence,
        "calculation": {
            "formula": (
                "Pearson correlation coefficient"
            ),
            "value": correlation,
            "visualization": result.get(
                "visualization"
            ),
        },
        "confidence": {
            "level": (
                "high"
                if p_value is not None and p_value < 0.05
                else "low"
            ),
            "p_value": p_value,
            "alpha": 0.05,
            "sample_size": sample_size,
        },
        "source_columns": result["columns"],
        "method": "pearson_correlation",
        "limitations": [
            "Correlation does not imply causation.",
            "Pearson correlation measures linear relationships.",
            "Small sample sizes can reduce reliability.",
        ],
    }


def discover_outlier_insight(result: dict) -> dict | None:
    outliers = result.get("outliers")

    if not outliers:
        return None

    measure = result.get("measure")

    if not measure:
        return None

    return {
        "insight_type": "outlier",
        "title": f"Potential outliers detected in {measure}",
        "evidence": {
            "outliers": outliers,
            "outlier_count": len(outliers),
            "lower_bound": result.get("outlier_lower_bound"),
            "upper_bound": result.get("outlier_upper_bound"),
        },
        "calculation": {
            "method": "IQR",
            "q1": result.get("q1"),
            "q3": result.get("q3"),
            "iqr": result.get("iqr"),
            "lower_bound": result.get("outlier_lower_bound"),
            "upper_bound": result.get("outlier_upper_bound"),
        },
        "confidence": {
            "level": "high",
            "method": "deterministic_iqr_rule",
        },
        "source_columns": [measure],
        "method": "iqr_outlier_detection",
        "limitations": [
            "An outlier is not necessarily an error.",
            "Outliers may represent legitimate business events.",
            "IQR-based detection does not determine the cause of an outlier.",
        ],
    }