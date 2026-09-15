from app.services.insight_verifier import verify_insight
from app.schemas.insight import InsightContract


def test_valid_correlation_is_verified():
    insight = {
        "insight_type": "correlation",
        "title": "Age and Salary relationship",
        "source_columns": ["Age", "Salary"],
        "method": "pearson_correlation",
        "evidence": {
            "correlation": 0.9,
            "p_value": 0.01,
            "sample_size": 10,
        },
        "calculation": {},
        "verification": {},
        "confidence": {},
        "limitations": [],
    }

    analysis_result = {
        "type": "correlation",
        "columns": ["Age", "Salary"],
        "correlation": 0.9,
        "p_value": 0.01,
        "sample_size": 10,
        "method": "pearson_correlation",
    }

    result = verify_insight(insight, analysis_result)

    assert result["verification"]["status"] == "verified"


def test_correlation_missing_p_value_fails():
    insight = {
        "insight_type": "correlation",
        "title": "Age and Salary relationship",
        "source_columns": ["Age", "Salary"],
        "method": "pearson_correlation",
        "evidence": {
            "correlation": 0.9,
            "sample_size": 10,
        },
        "calculation": {},
        "verification": {},
        "confidence": {},
        "limitations": [],
    }

    analysis_result = {
        "type": "correlation",
        "columns": ["Age", "Salary"],
        "correlation": 0.9,
        "p_value": None,
        "sample_size": 10,
        "method": "pearson_correlation",
    }

    result = verify_insight(insight, analysis_result)

    assert result["verification"]["status"] == "failed"


def test_correlation_small_sample_is_insufficient():
    insight = {
        "insight_type": "correlation",
        "title": "Age and Salary relationship",
        "source_columns": ["Age", "Salary"],
        "method": "pearson_correlation",
        "evidence": {
            "correlation": 0.9,
            "p_value": 0.01,
            "sample_size": 2,
        },
        "calculation": {},
        "verification": {},
        "confidence": {},
        "limitations": [],
    }

    analysis_result = {
        "type": "correlation",
        "columns": ["Age", "Salary"],
        "correlation": 0.9,
        "p_value": 0.01,
        "sample_size": 2,
        "method": "pearson_correlation",
    }

    result = verify_insight(insight, analysis_result)

    assert result["verification"]["status"] == "insufficient_data"


def test_group_difference_with_small_group_is_insufficient():
    insight = {
        "insight_type": "group_difference",
        "title": "IT has highest salary",
        "source_columns": ["Salary", "Department"],
        "method": "group_mean_comparison",
        "evidence": {
            "highest_group": "IT",
            "highest_value": 70000,
            "lowest_group": "Finance",
            "lowest_value": 50000,
        },
        "calculation": {},
        "verification": {},
        "confidence": {},
        "limitations": [],
    }

    analysis_result = {
        "type": "group_comparison",
        "measure": "Salary",
        "dimension": "Department",
        "groups": [
            {"Department": "IT", "count": 3, "mean": 70000},
            {"Department": "Finance", "count": 2, "mean": 50000},
        ],
        "statistical_test": {
            "test": "one_way_anova",
            "status": "insufficient_data",
            "group_sizes": {
                "IT": 3,
                "Finance": 2,
            },
            "minimum_group_size": 3,
        },
    }

    result = verify_insight(insight, analysis_result)

    assert result["verification"]["status"] == "insufficient_data"


def test_unsupported_insight_type_fails():
    insight = {
        "insight_type": "unknown_type",
        "title": "Unknown insight",
        "source_columns": [],
        "method": "unknown",
        "evidence": {},
        "calculation": {},
        "verification": {},
        "confidence": {},
        "limitations": [],
    }

    result = verify_insight(insight, {})

    assert result["verification"]["status"] == "failed"


def test_verified_insight_matches_contract():
    insight = {
        "insight_type": "correlation",
        "title": "Age and Salary relationship",
        "source_columns": ["Age", "Salary"],
        "method": "pearson_correlation",
        "evidence": {
            "correlation": 0.9,
            "p_value": 0.01,
            "sample_size": 10,
        },
        "calculation": {},
        "verification": {},
        "confidence": {},
        "limitations": [],
    }

    analysis_result = {
        "type": "correlation",
        "columns": ["Age", "Salary"],
        "correlation": 0.9,
        "p_value": 0.01,
        "sample_size": 10,
        "method": "pearson_correlation",
    }

    result = verify_insight(insight, analysis_result)

    validated = InsightContract(**result)

    assert validated.insight_type == "correlation"
    assert validated.verification["status"] == "verified"

def test_correlation_with_three_samples_is_verified():
    from app.services.insight_verifier import verify_insight

    insight = {
        "insight_type": "correlation",
        "title": "Age and Salary relationship",
        "source_columns": ["Age", "Salary"],
        "method": "pearson_correlation",
        "evidence": {
            "correlation": 0.95,
            "sample_size": 3,
        },
        "calculation": {},
        "verification": {
            "p_value": 0.049,
        },
        "confidence": {},
        "limitations": [],
    }

    result = verify_insight(
        insight,
        {
            "type": "correlation",
            "correlation": 0.95,
            "p_value": 0.049,
            "sample_size": 3,
            "columns": ["Age", "Salary"],
            "method": "pearson_correlation",
        },
    )

    assert result["verification"]["status"] == "verified"

def test_correlation_with_wrong_value_fails_numeric_consistency():
    insight = {
        "insight_type": "correlation",
        "title": "Age and Salary relationship",
        "source_columns": ["Age", "Salary"],
        "method": "pearson_correlation",
        "evidence": {
            "correlation": 0.80,
            "p_value": 0.01,
            "sample_size": 10,
        },
        "calculation": {},
        "verification": {},
        "confidence": {},
        "limitations": [],
    }

    analysis_result = {
        "type": "correlation",
        "correlation": 0.90,
        "p_value": 0.01,
        "sample_size": 10,
        "columns": ["Age", "Salary"],
        "method": "pearson_correlation",
    }

    result = verify_insight(insight, analysis_result)

    assert result["verification"]["status"] == "failed"
    assert any(
        mismatch["field"] == "correlation"
        for mismatch in result["verification"]["mismatches"]
    )


def test_correlation_with_wrong_p_value_fails_numeric_consistency():
    insight = {
        "insight_type": "correlation",
        "title": "Age and Salary relationship",
        "source_columns": ["Age", "Salary"],
        "method": "pearson_correlation",
        "evidence": {
            "correlation": 0.90,
            "p_value": 0.20,
            "sample_size": 10,
        },
        "calculation": {},
        "verification": {},
        "confidence": {},
        "limitations": [],
    }

    analysis_result = {
        "type": "correlation",
        "correlation": 0.90,
        "p_value": 0.01,
        "sample_size": 10,
        "columns": ["Age", "Salary"],
        "method": "pearson_correlation",
    }

    result = verify_insight(insight, analysis_result)

    assert result["verification"]["status"] == "failed"
    assert any(
        mismatch["field"] == "p_value"
        for mismatch in result["verification"]["mismatches"]
    )


def test_group_difference_with_wrong_highest_value_fails():
    insight = {
        "insight_type": "group_difference",
        "title": "IT has the highest salary",
        "source_columns": ["Salary", "Department"],
        "method": "group_mean_comparison",
        "evidence": {
            "highest_group": "IT",
            "highest_value": 75000,
            "lowest_group": "Finance",
            "lowest_value": 50000,
            "absolute_difference": 20000,
            "percentage_difference": 40.0,
            "statistical_test": "one_way_anova",
            "statistic": 10.0,
            "p_value": 0.01,
        },
        "calculation": {},
        "verification": {},
        "confidence": {},
        "limitations": [],
    }

    analysis_result = {
        "type": "group_comparison",
        "measure": "Salary",
        "dimension": "Department",
        "groups": [
            {
                "Department": "IT",
                "count": 3,
                "mean": 70000,
            },
            {
                "Department": "Finance",
                "count": 3,
                "mean": 50000,
            },
        ],
        "statistical_test": {
            "test": "one_way_anova",
            "statistic": 10.0,
            "p_value": 0.01,
        },
    }

    result = verify_insight(insight, analysis_result)

    assert result["verification"]["status"] == "failed"
    assert any(
        mismatch["field"] == "highest_value"
        for mismatch in result["verification"]["mismatches"]
    )


def test_group_difference_with_wrong_percentage_fails():
    insight = {
        "insight_type": "group_difference",
        "title": "IT has the highest salary",
        "source_columns": ["Salary", "Department"],
        "method": "group_mean_comparison",
        "evidence": {
            "highest_group": "IT",
            "highest_value": 70000,
            "lowest_group": "Finance",
            "lowest_value": 50000,
            "absolute_difference": 20000,
            "percentage_difference": 50.0,
            "statistical_test": "one_way_anova",
            "statistic": 10.0,
            "p_value": 0.01,
        },
        "calculation": {},
        "verification": {},
        "confidence": {},
        "limitations": [],
    }

    analysis_result = {
        "type": "group_comparison",
        "measure": "Salary",
        "dimension": "Department",
        "groups": [
            {
                "Department": "IT",
                "count": 3,
                "mean": 70000,
            },
            {
                "Department": "Finance",
                "count": 3,
                "mean": 50000,
            },
        ],
        "statistical_test": {
            "test": "one_way_anova",
            "statistic": 10.0,
            "p_value": 0.01,
        },
    }

    result = verify_insight(insight, analysis_result)

    assert result["verification"]["status"] == "failed"
    assert any(
        mismatch["field"] == "percentage_difference"
        for mismatch in result["verification"]["mismatches"]
    )


def test_group_difference_with_wrong_group_fails():
    insight = {
        "insight_type": "group_difference",
        "title": "Marketing has the highest salary",
        "source_columns": ["Salary", "Department"],
        "method": "group_mean_comparison",
        "evidence": {
            "highest_group": "Marketing",
            "highest_value": 70000,
            "lowest_group": "Finance",
            "lowest_value": 50000,
            "absolute_difference": 20000,
            "percentage_difference": 40.0,
            "statistical_test": "one_way_anova",
            "statistic": 10.0,
            "p_value": 0.01,
        },
        "calculation": {},
        "verification": {},
        "confidence": {},
        "limitations": [],
    }

    analysis_result = {
        "type": "group_comparison",
        "measure": "Salary",
        "dimension": "Department",
        "groups": [
            {
                "Department": "IT",
                "count": 3,
                "mean": 70000,
            },
            {
                "Department": "Finance",
                "count": 3,
                "mean": 50000,
            },
        ],
        "statistical_test": {
            "test": "one_way_anova",
            "statistic": 10.0,
            "p_value": 0.01,
        },
    }

    result = verify_insight(insight, analysis_result)

    assert result["verification"]["status"] == "failed"
    assert any(
        mismatch["field"] == "highest_group"
        for mismatch in result["verification"]["mismatches"]
    )