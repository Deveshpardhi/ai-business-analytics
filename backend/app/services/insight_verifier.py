from math import isclose

from app.schemas.insight import InsightContract


NUMERIC_TOLERANCE = 1e-6


def validate_insight(insight: dict) -> dict:
    validated = InsightContract(**insight)
    return validated.model_dump()


def _numbers_match(
    claimed: float | int | None,
    actual: float | int | None,
) -> bool:
    if claimed is None or actual is None:
        return claimed == actual

    try:
        return isclose(
            float(claimed),
            float(actual),
            rel_tol=NUMERIC_TOLERANCE,
            abs_tol=NUMERIC_TOLERANCE,
        )
    except (TypeError, ValueError):
        return False


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
    evidence = insight.get("evidence", {})

    claimed_correlation = evidence.get("correlation")
    claimed_p_value = evidence.get("p_value")

    if claimed_p_value is None:
        claimed_p_value = insight.get("verification", {}).get("p_value")

    claimed_sample_size = evidence.get("sample_size")

    actual_correlation = analysis_result.get("correlation")
    actual_p_value = analysis_result.get("p_value")
    actual_sample_size = analysis_result.get("sample_size")

    if actual_sample_size is None:
        return {
            **insight,
            "verification": {
                "status": "insufficient_data",
                "reason": "Sample size is required for verification.",
            },
        }

    if actual_sample_size < 3:
        return {
            **insight,
            "verification": {
                "status": "insufficient_data",
                "sample_size": actual_sample_size,
                "reason": (
                    "At least 3 observations are required "
                    "for Pearson correlation testing."
                ),
            },
        }

    if claimed_correlation is None:
        return {
            **insight,
            "verification": {
                "status": "failed",
                "sample_size": actual_sample_size,
                "reason": "Correlation value is missing.",
            },
        }

    if claimed_p_value is None:
        return {
            **insight,
            "verification": {
                "status": "failed",
                "sample_size": actual_sample_size,
                "correlation": claimed_correlation,
                "reason": "P-value is missing.",
            },
        }

    if claimed_sample_size is None:
        return {
            **insight,
            "verification": {
                "status": "failed",
                "sample_size": actual_sample_size,
                "reason": "Sample size is missing from insight evidence.",
            },
        }

    mismatches = []

    if not _numbers_match(
        claimed_correlation,
        actual_correlation,
    ):
        mismatches.append({
            "field": "correlation",
            "claimed": claimed_correlation,
            "actual": actual_correlation,
        })

    if not _numbers_match(
        claimed_p_value,
        actual_p_value,
    ):
        mismatches.append({
            "field": "p_value",
            "claimed": claimed_p_value,
            "actual": actual_p_value,
        })

    if claimed_sample_size != actual_sample_size:
        mismatches.append({
            "field": "sample_size",
            "claimed": claimed_sample_size,
            "actual": actual_sample_size,
        })

    if mismatches:
        return {
            **insight,
            "verification": {
                "status": "failed",
                "reason": (
                    "Insight numeric claims do not match "
                    "the deterministic analysis result."
                ),
                "mismatches": mismatches,
                "method": "pearson_correlation_test",
            },
        }

    alpha = 0.05

    if actual_p_value < alpha:
        status = "verified"
        significance = "statistically_significant"
    else:
        status = "not_significant"
        significance = "not_statistically_significant"

    return {
        **insight,
        "verification": {
            "status": status,
            "sample_size": actual_sample_size,
            "correlation": actual_correlation,
            "p_value": actual_p_value,
            "alpha": alpha,
            "significance": significance,
            "method": "pearson_correlation_test",
            "numeric_consistency": True,
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
    test_name = statistical_test.get("test")

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

    evidence = insight.get("evidence", {})

    claimed_highest_group = evidence.get("highest_group")
    claimed_lowest_group = evidence.get("lowest_group")
    claimed_highest_value = evidence.get("highest_value")
    claimed_lowest_value = evidence.get("lowest_value")
    claimed_absolute_difference = evidence.get("absolute_difference")
    claimed_percentage_difference = evidence.get(
        "percentage_difference"
    )
    claimed_statistical_test = evidence.get("statistical_test")
    claimed_statistic = evidence.get("statistic")
    claimed_p_value = evidence.get("p_value")

    if claimed_p_value is None:
        claimed_p_value = insight.get("verification", {}).get("p_value")

    highest_group = max(
        groups,
        key=lambda group: group.get("mean", float("-inf")),
    )

    lowest_group = min(
        groups,
        key=lambda group: group.get("mean", float("inf")),
    )

    actual_highest_group = highest_group.get(dimension)
    actual_lowest_group = lowest_group.get(dimension)

    actual_highest_value = highest_group.get("mean")
    actual_lowest_value = lowest_group.get("mean")

    if actual_highest_value is None or actual_lowest_value is None:
        return {
            **insight,
            "verification": {
                "status": "failed",
                "reason": "Group means are required for verification.",
                "group_sizes": group_sizes,
            },
        }

    actual_absolute_difference = (
        actual_highest_value - actual_lowest_value
    )

    if actual_lowest_value == 0:
        actual_percentage_difference = None
    else:
        actual_percentage_difference = (
            actual_absolute_difference
            / abs(actual_lowest_value)
        ) * 100

    mismatches = []

    if claimed_highest_group != actual_highest_group:
        mismatches.append({
            "field": "highest_group",
            "claimed": claimed_highest_group,
            "actual": actual_highest_group,
        })

    if claimed_lowest_group != actual_lowest_group:
        mismatches.append({
            "field": "lowest_group",
            "claimed": claimed_lowest_group,
            "actual": actual_lowest_group,
        })

    if not _numbers_match(
        claimed_highest_value,
        actual_highest_value,
    ):
        mismatches.append({
            "field": "highest_value",
            "claimed": claimed_highest_value,
            "actual": actual_highest_value,
        })

    if not _numbers_match(
        claimed_lowest_value,
        actual_lowest_value,
    ):
        mismatches.append({
            "field": "lowest_value",
            "claimed": claimed_lowest_value,
            "actual": actual_lowest_value,
        })

    if not _numbers_match(
        claimed_absolute_difference,
        actual_absolute_difference,
    ):
        mismatches.append({
            "field": "absolute_difference",
            "claimed": claimed_absolute_difference,
            "actual": actual_absolute_difference,
        })

    if not _numbers_match(
        claimed_percentage_difference,
        actual_percentage_difference,
    ):
        mismatches.append({
            "field": "percentage_difference",
            "claimed": claimed_percentage_difference,
            "actual": actual_percentage_difference,
        })

    if claimed_statistical_test != test_name:
        mismatches.append({
            "field": "statistical_test",
            "claimed": claimed_statistical_test,
            "actual": test_name,
        })

    if not _numbers_match(
        claimed_statistic,
        statistic,
    ):
        mismatches.append({
            "field": "statistic",
            "claimed": claimed_statistic,
            "actual": statistic,
        })

    if claimed_p_value is not None and not _numbers_match(
        claimed_p_value,
        p_value,
    ):
        mismatches.append({
            "field": "p_value",
            "claimed": claimed_p_value,
            "actual": p_value,
        })

    if mismatches:
        return {
            **insight,
            "verification": {
                "status": "failed",
                "reason": (
                    "Insight numeric or group claims do not match "
                    "the deterministic analysis result."
                ),
                "mismatches": mismatches,
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
            "test": test_name,
            "statistic": statistic,
            "p_value": p_value,
            "alpha": alpha,
            "significance": significance,
            "highest_group": actual_highest_group,
            "lowest_group": actual_lowest_group,
            "highest_value": actual_highest_value,
            "lowest_value": actual_lowest_value,
            "absolute_difference": actual_absolute_difference,
            "percentage_difference": actual_percentage_difference,
            "numeric_consistency": True,
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

                if result.get("columns") == insight.get(
                    "source_columns"
                ):
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