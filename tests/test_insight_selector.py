from app.services.insight_selector import select_top_insights


def test_not_significant_insight_is_not_selected():
    insights = [
        {
            "insight_type": "group_difference",
            "title": "Salary difference between departments",
            "source_columns": ["Salary", "Department"],
            "score": 0.90,
            "verification": {
                "status": "not_significant",
            },
        },
        {
            "insight_type": "correlation",
            "title": "Age and Salary relationship",
            "source_columns": ["Age", "Salary"],
            "score": 0.80,
            "verification": {
                "status": "verified",
            },
        },
    ]

    selected = select_top_insights(insights)

    assert len(selected) == 1
    assert selected[0]["insight_type"] == "correlation"
