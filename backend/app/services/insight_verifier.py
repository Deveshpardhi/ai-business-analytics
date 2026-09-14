from app.schemas.insight import InsightContract


def validate_insight(insight: dict) -> dict:
    validated = InsightContract(**insight)
    return validated.model_dump()


def verify_insight(insight: dict, analysis_result: dict) -> dict:
    insight = validate_insight(insight)

    insight_type = insight["insight_type"]

    if insight_type == "correlation":
        return validate_insight(
            verify_correlation(insight, analysis_result)
        )

    if insight_type == "group_difference":
        return validate_insight(
            verify_group_difference(insight, analysis_result)
        )

    if insight_type == "outlier":
        return validate_insight(
            verify_outlier_insight(insight, [analysis_result])
        )

    return validate_insight({
        **insight,
        "verification": {
            "status": "failed",
            "reason": "Unsupported insight type",
        },
    })


def verify_correlation(
    insight: dict,
    analysis_result: dict,
) -> dict:
    correlation = insight["evidence"].get("correlation")
    p_value = analysis_result.get("p_value")
    sample_size = analysis_result.get("sample_size")

    if sample_size is None:
        return {
            **insight,
            "verification": {
                "status": "insufficient_data",
                "reason": "Sample size is required for verification.",
            },
        }

    if sample_size < 3:
        return {
            **insight,
            "verification": {
                "status": "insufficient_data",
                "sample_size": sample_size,
                "reason": (
                    "At least 3 observations are required "
                    "for Pearson correlation testing."
                ),
            },
        }

    if correlation is None:
        return {
            **insight,
            "verification": {
                "status": "failed",
                "sample_size": sample_size,
                "reason": "Correlation value is missing.",
            },
        }

    if p_value is None:
        return {
            **insight,
            "verification": {
                "status": "failed",
                "sample_size": sample_size,
                "correlation": correlation,
                "reason": "P-value is missing.",
            },
        }

    alpha = 0.05

    if p_value < alpha:
        status = "verified"
        significance = "statistically_significant"
    else:
        status = "not_significant"
        significance = "not_statistically_significant"

    return {
        **insight,
        "verification": {
            "status": status,
            "sample_size": sample_size,
            "correlation": correlation,
            "p_value": p_value,
            "alpha": alpha,
            "significance": significance,
            "method": "pearson_correlation_test",
        },
    }


def verify_group_difference(
    insight: dict,
    analysis_result: dict,
) -> dict:
    groups = analysis_result.get("groups", [])
    statistical_test = analysis_result.get("statistical_test")

    if len(groups) < 2:
        return {
            **insight,
            "verification": {
                "status": "insufficient_data",
                "reason": "At least two groups are required.",
            },
        }

    dimension = analysis_result.get("dimension", "group")

    group_sizes = {
        group.get(dimension, "unknown"): group.get("count", 0)
        for group in groups
    }

    minimum_group_size = min(group_sizes.values())

    if minimum_group_size < 3:
        return {
            **insight,
            "verification": {
                "status": "insufficient_data",
                "reason": (
                    "Each group must contain at least three observations "
                    "for a reliable group comparison."
                ),
                "group_sizes": group_sizes,
                "minimum_group_size": minimum_group_size,
                "required_minimum_group_size": 3,
            },
        }

    if statistical_test is None:
        return {
            **insight,
            "verification": {
                "status": "failed",
                "reason": "No statistical test was provided.",
                "group_sizes": group_sizes,
            },
        }

    p_value = statistical_test.get("p_value")
    statistic = statistical_test.get("statistic")
    alpha = 0.05

    if p_value is None:
        return {
            **insight,
            "verification": {
                "status": "failed",
                "reason": "Statistical test is missing p-value.",
                "group_sizes": group_sizes,
            },
        }

    if p_value < alpha:
        status = "verified"
        significance = "statistically_significant"
    else:
        status = "not_significant"
        significance = "not_statistically_significant"

    return {
        **insight,
        "verification": {
            "status": status,
            "group_sizes": group_sizes,
            "minimum_group_size": minimum_group_size,
            "test": statistical_test.get("test"),
            "statistic": statistic,
            "p_value": p_value,
            "alpha": alpha,
            "significance": significance,
        },
    }


def verify_outlier_insight(
    insight: dict,
    analysis_results: list[dict],
) -> dict:
    evidence = insight.get("evidence", {})
    outliers = evidence.get("outliers", [])

    source_columns = insight.get("source_columns", [])

    if not source_columns:
        return {
            **insight,
            "verification": {
                "status": "failed",
                "reason": "No source column found for outlier insight.",
            },
        }

    measure = source_columns[0]

    for result in analysis_results:
        if result.get("type") != "descriptive_statistics":
            continue

        if result.get("measure") != measure:
            continue

        expected_outliers = result.get("outliers", [])

        if outliers == expected_outliers:
            return {
                **insight,
                "verification": {
                    "status": "verified",
                    "method": "iqr_outlier_detection",
                    "measure": measure,
                    "outlier_count": len(expected_outliers),
                    "outliers": expected_outliers,
                    "lower_bound": result.get("outlier_lower_bound"),
                    "upper_bound": result.get("outlier_upper_bound"),
                },
            }

        return {
            **insight,
            "verification": {
                "status": "failed",
                "reason": (
                    "Reported outliers do not match "
                    "the deterministic analysis result."
                ),
                "expected_outliers": expected_outliers,
                "reported_outliers": outliers,
            },
        }

    return {
        **insight,
        "verification": {
            "status": "failed",
            "reason": "No matching descriptive statistics result found.",
        },
    }


def verify_insights(
    insights: list[dict],
    analysis_results: list[dict],
) -> list[dict]:
    """
    Verify discovered insights against their corresponding
    deterministic analysis results.

    Every insight is returned. Verification status is attached
    rather than removing unverified insights.
    """

    results = []

    for insight in insights:
        insight = validate_insight(insight)
        insight_type = insight.get("insight_type")

        if insight_type == "outlier":
            verified_insight = verify_outlier_insight(
                insight,
                analysis_results,
            )
            results.append(validate_insight(verified_insight))
            continue

        matching_result = None

        for result in analysis_results:
            result_type = result.get("type")

            if insight_type == "group_difference":
                if result_type != "group_comparison":
                    continue

                source_columns = insight.get("source_columns", [])

                if len(source_columns) < 2:
                    continue

                if (
                    result.get("measure") == source_columns[0]
                    and result.get("dimension") == source_columns[1]
                ):
                    matching_result = result
                    break

            elif insight_type == "correlation":
                if result_type != "correlation":
                    continue

                if result.get("columns") == insight.get("source_columns"):
                    matching_result = result
                    break

        if matching_result:
            verified_insight = verify_insight(
                insight,
                matching_result,
            )
            results.append(validate_insight(verified_insight))

        else:
            results.append(
                validate_insight({
                    **insight,
                    "verification": {
                        "status": "failed",
                        "reason": "No matching analysis result found.",
                    },
                })
            )

    return results