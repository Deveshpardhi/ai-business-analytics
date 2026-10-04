from pathlib import Path

import pandas as pd
import pytest

from app.security.pii_detector import analyze_pii
from app.services.analytics_executor import execute_analysis
from app.services.analytics_planner import build_analytics_plan
from app.services.semantic_detector import infer_semantics


from tests.evaluation.golden_large_factory import (
    ROW_COUNT,
    build_large_golden_dataset,
)

@pytest.fixture(scope="module")
def large_golden_file(tmp_path_factory):
    directory = tmp_path_factory.mktemp(
        "large_golden"
    )

    file_path = (
        directory
        / "golden_large_business_100k.csv"
    )

    df = build_large_golden_dataset()
    df.to_csv(file_path, index=False)

    return file_path


def test_large_golden_dataset_contract(
    large_golden_file,
):
    df = pd.read_csv(
        large_golden_file
    )

    assert df.shape == (
        100_000,
        20,
    )

    assert df["TransactionID"].is_unique

    assert df["TransactionID"].iloc[0] == 1
    assert df["TransactionID"].iloc[-1] == 100_000

    assert (
        df["TransactionDate"].min()
        >= "2023-01-01"
    )

    assert (
        df["TransactionDate"].max()
        <= "2025-12-31"
    )

    assert int(
        df.isna().sum().sum()
    ) == 1500


def test_large_golden_semantics_and_plan(
    large_golden_file,
):
    pii = analyze_pii(
        str(large_golden_file)
    )

    assert pii["pii_detected"] is False
    assert pii["protected_columns"] == {}

    semantics = infer_semantics(
        str(large_golden_file),
        pii["protected_columns"],
    )

    assert (
        semantics["columns"]["TransactionID"]["role"]
        == "identifier"
    )

    assert (
        semantics["columns"]["CustomerID"]["role"]
        == "identifier"
    )

    assert (
        semantics["columns"]["TransactionDate"]["role"]
        == "date"
    )

    assert (
        semantics["columns"]["Revenue"]["role"]
        == "measure"
    )

    assert (
        semantics["columns"]["Department"]["role"]
        == "dimension"
    )

    profile = {
        "rows": ROW_COUNT,
        "columns": 20,
    }

    plan = build_analytics_plan(
        profile,
        semantics,
    )

    assert "TransactionID" in plan["identifiers"]
    assert "CustomerID" in plan["identifiers"]

    assert "TransactionID" not in plan["measures"]
    assert "CustomerID" not in plan["measures"]

    for analysis in plan["analyses"]:
        assert "TransactionID" not in str(analysis)
        assert "CustomerID" not in str(analysis)


def test_large_golden_anova_underflow(
    large_golden_file,
):
    result = execute_analysis(
        str(large_golden_file),
        {
            "type": "group_comparison",
            "measure": "UnitPrice",
            "dimension": "Department",
        },
    )

    test = result["statistical_test"]

    assert result["type"] == "group_comparison"
    assert test["test"] == "one_way_anova"

    assert test["sample_size"] == 100_000
    assert test["group_count"] == 4

    assert test["p_value"] == 0.0
    assert test["p_value_underflow"] is True

    assert test["statistic"] > 1000


def test_large_golden_revenue_cost_correlation(
    large_golden_file,
):
    result = execute_analysis(
        str(large_golden_file),
        {
            "type": "correlation",
            "columns": [
                "Revenue",
                "Cost",
            ],
        },
    )

    assert result["status"] == "completed"
    assert result["sample_size"] == 100_000

    assert result["correlation"] > 0.99

    assert result["p_value"] == 0.0


def test_large_golden_time_series(
    large_golden_file,
):
    result = execute_analysis(
        str(large_golden_file),
        {
            "type": "time_series",
            "measure": "Revenue",
            "date": "TransactionDate",
        },
    )

    assert result["sample_size"] == 100_000

    assert (
        result["data"][0]["TransactionDate"]
        >= "2023-01-01"
    )

    assert (
        result["data"][-1]["TransactionDate"]
        <= "2025-12-31"
    )


def test_large_golden_is_reproducible():
    first = build_large_golden_dataset()
    second = build_large_golden_dataset()

    pd.testing.assert_frame_equal(
        first,
        second,
    )