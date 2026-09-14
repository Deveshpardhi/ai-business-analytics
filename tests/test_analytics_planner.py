from app.services.analytics_planner import build_analytics_plan


def test_identifier_is_excluded_from_correlation_candidates():
    profile = {
        "rows": 30,
        "columns": 4,
    }

    semantics = {
        "columns": {
            "EmployeeID": {
                "role": "identifier",
                "dtype": "int64",
            },
            "Age": {
                "role": "numeric",
                "dtype": "int64",
            },
            "Salary": {
                "role": "measure",
                "dtype": "int64",
            },
            "Department": {
                "role": "dimension",
                "dtype": "str",
            },
        }
    }

    plan = build_analytics_plan(profile, semantics)

    correlation_columns = [
        analysis["columns"]
        for analysis in plan["analyses"]
        if analysis["type"] == "correlation"
    ]

    assert ["Age", "Salary"] in correlation_columns
    assert all("EmployeeID" not in columns for columns in correlation_columns)