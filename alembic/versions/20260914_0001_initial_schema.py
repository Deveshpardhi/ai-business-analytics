"""Create the initial analytics schema.

Revision ID: 20260914_0001
Revises: None
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260914_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "dataset_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "dataset_id",
            "version_number",
            name="uq_dataset_versions_dataset_id_version_number",
        ),
    )
    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("dataset_version_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("validation_result", sa.JSON(), nullable=False),
        sa.Column("pii_result", sa.JSON(), nullable=False),
        sa.Column("profile_result", sa.JSON(), nullable=False),
        sa.Column("semantic_result", sa.JSON(), nullable=False),
        sa.Column("plan_result", sa.JSON(), nullable=False),
        sa.Column("analysis_results", sa.JSON(), nullable=False),
        sa.Column("discovered_insights", sa.JSON(), nullable=False),
        sa.Column("verified_insights", sa.JSON(), nullable=False),
        sa.Column("confidence_insights", sa.JSON(), nullable=False),
        sa.Column("scored_insights", sa.JSON(), nullable=False),
        sa.Column("explained_insights", sa.JSON(), nullable=False),
        sa.Column("ranked_insights", sa.JSON(), nullable=False),
        sa.Column("recommended_insights", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["dataset_version_id"], ["dataset_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("analysis_runs")
    op.drop_table("dataset_versions")
    op.drop_table("datasets")
