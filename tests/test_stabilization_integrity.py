from sqlalchemy import UniqueConstraint

from app.models.dataset import DatasetVersion
from app.services.analysis_pipeline import determine_analysis_run_status


def test_dataset_version_has_database_uniqueness_constraint():
    constraints = {
        tuple(constraint.columns.keys())
        for constraint in DatasetVersion.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert ("dataset_id", "version_number") in constraints


def test_analysis_run_is_partial_when_any_planned_analysis_fails():
    assert determine_analysis_run_status([
        {"type": "correlation"},
        {"type": "group_comparison", "status": "failed"},
    ]) == "partially_completed"


def test_analysis_run_is_completed_when_all_planned_analyses_succeed():
    assert determine_analysis_run_status([
        {"type": "correlation"},
        {"type": "group_comparison"},
    ]) == "completed"
