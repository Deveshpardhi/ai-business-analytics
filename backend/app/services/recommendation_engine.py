def build_recommendation_prompt(insight):
    return {
        "role": "system",
        "instruction": (
            "Generate a practical business recommendation from the provided "
            "verified insight. Use only the evidence provided. "
            "Do not invent or calculate numbers. "
            "Do not make causal claims unless causation is explicitly established. "
            "If the insight is only correlational, recommend investigation, "
            "monitoring, or further analysis rather than claiming causation."
        ),
        "insight": insight,
    }


def recommend_insight(insight, llm_function):
    prompt = build_recommendation_prompt(insight)

    recommendation = llm_function(prompt)

    return {
        "status": "generated",
        "recommendation": recommendation,
    }

def mock_recommendation_llm(prompt):
    insight = prompt["insight"]

    insight_type = insight.get("insight_type")

    if insight_type == "correlation":
        source_columns = insight.get("source_columns", [])

        column_a = source_columns[0] if len(source_columns) > 0 else "first variable"
        column_b = source_columns[1] if len(source_columns) > 1 else "second variable"

        return {
            "action": (
                f"Investigate the relationship between {column_a} and "
                f"{column_b} before making policy or operational changes."
            ),
            "reason": (
                "The analysis identified a statistically supported relationship, "
                "but correlation alone does not establish causation."
            ),
            "priority": "medium",
        }

    if insight_type == "group_difference":
        evidence = insight.get("evidence", {})

        highest_group = evidence.get("highest_group")
        lowest_group = evidence.get("lowest_group")

        return {
            "action": (
                f"Investigate why {highest_group} differs from "
                f"{lowest_group} and determine whether the difference "
                f"requires operational action."
            ),
            "reason": (
                "A measurable difference between groups was identified "
                "and should be investigated before taking action."
            ),
            "priority": "medium",
        }

    if insight_type == "outlier":
        return {
            "action": (
                "Review the identified outlier records to determine whether "
                "they represent legitimate business events or data-quality issues."
            ),
            "reason": (
                "The analysis detected values that fall outside the expected "
                "IQR-based range."
            ),
            "priority": "medium",
        }

    if (insight_type== "time_series_trend"):
        evidence = insight.get(
            "evidence",
            {},
        )

        source_columns = (
            insight.get(
                "source_columns",
                [],
            )
        )

        measure = (
            source_columns[0]
            if source_columns
            else "the measure"
        )

        direction = evidence.get(
            "trend_direction",
            "observed",
        )

        return {
            "action": (
                f"Monitor {measure} and "
                f"investigate the business "
                f"drivers behind the "
                f"{direction} historical trend "
                f"before making forecasts or "
                f"operational changes."
            ),
            "reason": (
                "The trend was calculated "
                "and verified from historical "
                "observations, but historical "
                "movement alone does not "
                "establish future performance "
                "or causation."
            ),
            "priority": "medium",
        }

    return {
        "action": "Review this insight and determine whether further investigation is required.",
        "reason": "The insight passed the available deterministic analysis checks.",
        "priority": "low",
    }
