from app.services.insight_discovery import (
    discover_group_insights,
)
from app.services.insight_explainer import (
    build_verified_evidence_context,
)


def make_group_result():
    return {
        "type": "group_comparison",
        "measure": "Salary",
        "dimension": "Department",
        "groups": [
            {
                "Department": "Marketing",
                "count": 4,
                "mean": 82000.0,
                "median": 81000.0,
                "min": 76000,
                "max": 90000,
            },
            {
                "Department": "Sales",
                "count": 4,
                "mean": 68000.0,
                "median": 67000.0,
                "min": 62000,
                "max": 75000,
            },
            {
                "Department": "HR",
                "count": 4,
                "mean": 47000.0,
                "median": 46500.0,
                "min": 43000,
                "max": 52000,
            },
        ],
        "statistical_test": {
            "test": "one_way_anova",
            "statistic": 20.0,
            "p_value": 0.001,
            "sample_size": 12,
            "group_count": 3,
        },
    }


def test_group_insight_contains_bar_visualization():
    result = make_group_result()

    insights = discover_group_insights(
        result
    )

    assert len(insights) == 1

    visualization = (
        insights[0]["calculation"][
            "visualization"
        ]
    )

    assert (
        visualization["type"]
        == "group_bar"
    )

    assert (
        visualization["measure"]
        == "Salary"
    )

    assert (
        visualization["dimension"]
        == "Department"
    )

    assert (
        visualization["total_groups"]
        == 3
    )

    assert (
        visualization[
            "displayed_groups"
        ]
        == 3
    )

    assert (
        visualization["sampled"]
        is False
    )

    assert (
        visualization["groups"][0]
        ["label"]
        == "Marketing"
    )

    assert (
        visualization["groups"][0]
        ["mean"]
        == 82000.0
    )


def test_group_visualization_preserves_aggregates():
    result = make_group_result()

    visualization = (
        discover_group_insights(
            result
        )[0]["calculation"][
            "visualization"
        ]
    )

    marketing = (
        visualization["groups"][0]
    )

    assert marketing == {
        "label": "Marketing",
        "mean": 82000.0,
        "count": 4,
        "median": 81000.0,
        "min": 76000,
        "max": 90000,
    }


def test_large_group_visualization_is_capped_deterministically():
    groups = []

    for index in range(20):
        groups.append(
            {
                "Department": (
                    f"Group {index:02d}"
                ),
                "count": 5,
                "mean": float(
                    20000 - index * 500
                ),
                "median": float(
                    20000 - index * 500
                ),
                "min": (
                    19000 - index * 500
                ),
                "max": (
                    21000 - index * 500
                ),
            }
        )

    result = {
        "type": "group_comparison",
        "measure": "Revenue",
        "dimension": "Department",
        "groups": groups,
        "statistical_test": None,
    }

    first = discover_group_insights(
        result
    )[0]

    second = discover_group_insights(
        result
    )[0]

    first_visualization = (
        first["calculation"][
            "visualization"
        ]
    )

    second_visualization = (
        second["calculation"][
            "visualization"
        ]
    )

    assert (
        first_visualization[
            "total_groups"
        ]
        == 20
    )

    assert (
        first_visualization[
            "displayed_groups"
        ]
        == 12
    )

    assert (
        first_visualization[
            "sampled"
        ]
        is True
    )

    assert (
        first_visualization["groups"]
        ==
        second_visualization["groups"]
    )

    labels = [
        group["label"]
        for group in first_visualization[
            "groups"
        ]
    ]

    assert "Group 00" in labels
    assert "Group 19" in labels


def test_group_visualization_does_not_cross_llm_boundary():
    result = make_group_result()

    insight = (
        discover_group_insights(
            result
        )[0]
    )

    insight["verification"] = {
        "status": "verified"
    }

    context = (
        build_verified_evidence_context(
            insight
        )
    )

    assert (
        "calculation"
        not in context
    )

    assert (
        "visualization"
        not in context["evidence"]
    )