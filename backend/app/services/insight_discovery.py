from app.schemas.insight import InsightContract
from app.services.time_series_metrics import (
    calculate_time_series_metrics,
)

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

        elif analysis_type == "time_series":
            insight = (
                discover_time_series_insight(
                    result
                )
            )

            if insight:
                insights.append(
                    validate_insight(
                        insight
                    )
                )

        elif analysis_type == "descriptive_statistics":
            insight = discover_outlier_insight(result)

            if insight:
                insights.append(validate_insight(insight))

    return insights

def _build_group_visualization(
    groups,
    measure,
    dimension,
    max_groups=12,
):
    """
    Build deterministic group-comparison chart data.

    For large category sets, preserve the highest and lowest
    groups by mean rather than sending every category to the UI.
    """
    valid_groups = [
        group
        for group in groups
        if group.get("mean") is not None
    ]

    total_groups = len(valid_groups)

    if total_groups <= max_groups:
        selected_groups = valid_groups
    else:
        top_count = max_groups // 2
        bottom_count = (
            max_groups - top_count
        )

        selected_groups = (
            valid_groups[:top_count]
            + valid_groups[-bottom_count:]
        )

    chart_groups = []

    for group in selected_groups:
        raw_label = group.get(
            dimension
        )

        label = (
            "Missing"
            if raw_label is None
            else str(raw_label)
        )

        chart_groups.append(
            {
                "label": label,
                "mean": group.get(
                    "mean"
                ),
                "count": group.get(
                    "count"
                ),
                "median": group.get(
                    "median"
                ),
                "min": group.get(
                    "min"
                ),
                "max": group.get(
                    "max"
                ),
            }
        )

    return {
        "type": "group_bar",
        "measure": measure,
        "dimension": dimension,
        "groups": chart_groups,
        "total_groups": total_groups,
        "displayed_groups": len(
            chart_groups
        ),
        "sampled": (
            total_groups > max_groups
        ),
    }

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
            "comparison": (
            "highest_group_mean - "
            "lowest_group_mean"
            ),
        "absolute_difference": (
            highest_mean - lowest_mean
        ),
        "percentage_difference": (
            percentage_difference
        ),
        "visualization": (
            _build_group_visualization(
                groups,
                measure,
                dimension,
            )
        ),
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

def discover_time_series_insight(
    result: dict,
) -> dict | None:
    measure = result.get(
        "measure"
    )

    date_column = result.get(
        "date"
    )

    data = result.get(
        "data",
        [],
    )

    if (
        not measure
        or not date_column
        or not data
    ):
        return None

    metrics = (
        calculate_time_series_metrics(
            data,
            measure,
            date_column,
        )
    )

    if (
        metrics.get("status")
        != "completed"
    ):
        return None

    direction = metrics[
        "trend_direction"
    ]

    title_direction = (
        "stable"
        if direction == "flat"
        else direction
    )

    evidence = {
        "trend_direction": (
            direction
        ),
        "trend_strength": (
            metrics[
                "trend_strength"
            ]
        ),
        "first_date": (
            metrics[
                "first_date"
            ]
        ),
        "first_value": (
            metrics[
                "first_value"
            ]
        ),
        "last_date": (
            metrics[
                "last_date"
            ]
        ),
        "last_value": (
            metrics[
                "last_value"
            ]
        ),
        "absolute_change": (
            metrics[
                "absolute_change"
            ]
        ),
        "percentage_change": (
            metrics[
                "percentage_change"
            ]
        ),
        "latest_period_change": (
            metrics[
                "latest_period_change"
            ]
        ),
        "latest_period_percentage_change": (
            metrics[
                "latest_period_percentage_change"
            ]
        ),
        "peak_date": (
            metrics[
                "peak_date"
            ]
        ),
        "peak_value": (
            metrics[
                "peak_value"
            ]
        ),
        "trough_date": (
            metrics[
                "trough_date"
            ]
        ),
        "trough_value": (
            metrics[
                "trough_value"
            ]
        ),
        "sample_size": (
            metrics[
                "sample_size"
            ]
        ),
        "r_squared": (
            metrics[
                "r_squared"
            ]
        ),
        "moving_average_window": (
            metrics[
                "moving_average_window"
            ]
        ),
        "latest_moving_average": (
            metrics[
                "latest_moving_average"
            ]
        ),
    }

    return {
        "insight_type": (
            "time_series_trend"
        ),
        "title": (
            f"{measure} shows a "
            f"{title_direction} trend "
            f"over {date_column}"
        ),
        "evidence": evidence,
        "calculation": {
            "method": (
                "linear trend over "
                "chronologically sorted "
                "observations"
            ),
            "slope_per_observation": (
                metrics[
                    "slope_per_observation"
                ]
            ),
            "r_squared": (
                metrics[
                    "r_squared"
                ]
            ),
        },
        "confidence": {
            "level": (
                "pending_verification"
            ),
        },
        "source_columns": [
            measure,
            date_column,
        ],
        "method": (
            "deterministic_time_series_trend"
        ),
        "limitations": [
            (
                "Historical trend direction "
                "does not forecast future "
                "performance."
            ),
            (
                "Trend regression uses "
                "chronological observation "
                "order and does not model "
                "unequal time intervals."
            ),
            (
                "Short time series can make "
                "trend estimates less reliable."
            ),
        ],
    }

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