from typing import Any


def build_analytics_plan(
    profile: dict,
    semantics: dict,
) -> dict:
    """
    Build a deterministic analytics plan from
    dataset profile and semantic metadata.
    """

    columns = semantics["columns"]

    measures = []
    dimensions = []
    dates = []
    identifiers = []

    for column_name, metadata in columns.items():
        role = metadata["role"]

        if role == "measure":
            measures.append(column_name)

        elif role == "dimension":
            dimensions.append(column_name)

        elif role == "date":
            dates.append(column_name)

        elif role == "identifier":
            identifiers.append(column_name)

    analyses: list[dict[str, Any]] = []

    # --------------------------------------------------
    # 1. Overall measure statistics
    # --------------------------------------------------

    for measure in measures:
        analyses.append(
            {
                "type": "descriptive_statistics",
                "measure": measure,
                "description": (
                    f"Calculate descriptive statistics "
                    f"for {measure}."
                ),
            }
        )

    # --------------------------------------------------
    # 2. Measure by dimension
    # --------------------------------------------------

    for measure in measures:
        for dimension in dimensions:
            analyses.append(
                {
                    "type": "group_comparison",
                    "measure": measure,
                    "dimension": dimension,
                    "description": (
                        f"Compare {measure} across "
                        f"{dimension}."
                    ),
                }
            )

    # --------------------------------------------------
    # 3. Time-series analysis
    # --------------------------------------------------

    for measure in measures:
        for date in dates:
            analyses.append(
                {
                    "type": "time_series",
                    "measure": measure,
                    "date": date,
                    "description": (
                        f"Analyze {measure} over time "
                        f"using {date}."
                    ),
                }
            )

    # --------------------------------------------------
    # 4. Numeric relationships
    # --------------------------------------------------

    numeric_columns = []

    for column_name, metadata in columns.items():
        if (
            metadata["dtype"].startswith(("int", "float"))
            and metadata["role"] in {"measure", "numeric"}
        ):
            numeric_columns.append(column_name)

    for i in range(len(numeric_columns)):
        for j in range(i + 1, len(numeric_columns)):
            first = numeric_columns[i]
            second = numeric_columns[j]

            analyses.append(
                {
                    "type": "correlation",
                    "columns": [first, second],
                    "description": (
                        f"Analyze the relationship "
                        f"between {first} and {second}."
                    ),
                }
            )

    return {
        "dataset_rows": profile["rows"],
        "dataset_columns": profile["columns"],
        "measures": measures,
        "dimensions": dimensions,
        "dates": dates,
        "identifiers": identifiers,
        "analyses": analyses,
    }
