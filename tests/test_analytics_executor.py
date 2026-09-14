import polars as pl

from app.services.analytics_executor import time_series


def test_time_series_sorts_by_date():
    df = pl.DataFrame(
        {
            "JoiningDate": [
                "2025-01-03",
                "2025-01-01",
                "2025-01-02",
            ],
            "Salary": [
                50000,
                60000,
                55000,
            ],
        }
    )

    result = time_series(
        df,
        "Salary",
        "JoiningDate",
    )

    assert result["type"] == "time_series"
    assert result["measure"] == "Salary"
    assert result["date"] == "JoiningDate"
    assert result["sample_size"] == 3

    assert result["data"] == [
        {
            "JoiningDate": "2025-01-01",
            "Salary": 60000,
        },
        {
            "JoiningDate": "2025-01-02",
            "Salary": 55000,
        },
        {
            "JoiningDate": "2025-01-03",
            "Salary": 50000,
        },
    ]
