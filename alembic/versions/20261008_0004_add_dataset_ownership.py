"""Add dataset ownership.

Revision ID: 20261008_0004
Revises: 20261008_0003
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261008_0004"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "20261008_0003"

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


def upgrade() -> None:
    with op.batch_alter_table(
        "datasets"
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "user_id",
                sa.Uuid(),
                nullable=True,
            )
        )

        batch_op.create_foreign_key(
            "fk_datasets_user_id_users",
            "users",
            ["user_id"],
            ["id"],
        )

        batch_op.create_index(
            "ix_datasets_user_id",
            ["user_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table(
        "datasets"
    ) as batch_op:
        batch_op.drop_index(
            "ix_datasets_user_id"
        )

        batch_op.drop_constraint(
            "fk_datasets_user_id_users",
            type_="foreignkey",
        )

        batch_op.drop_column(
            "user_id"
        )
