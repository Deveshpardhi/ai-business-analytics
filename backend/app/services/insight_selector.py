def insight_key(insight: dict) -> tuple:
    insight_type = insight.get("insight_type")
    source_columns = tuple(
        insight.get("source_columns", [])
    )

    return (
        insight_type,
        source_columns,
    )


def deduplicate_insights(
    insights: list[dict],
) -> list[dict]:
    seen = set()
    unique_insights = []

    for insight in insights:
        key = insight_key(insight)

        if key in seen:
            continue

        seen.add(key)
        unique_insights.append(insight)

    return unique_insights


def select_top_insights(
    insights: list[dict],
    top_n: int = 10,
) -> list[dict]:
    rankable = [
        insight
        for insight in insights
            if insight.get("verification", {}).get("status") == "verified"
    ]

    unique_insights = deduplicate_insights(
        rankable
    )

    ranked = sorted(
        unique_insights,
        key=lambda insight: insight.get(
            "score",
            0.0,
        ),
        reverse=True,
    )

    return ranked[:top_n]