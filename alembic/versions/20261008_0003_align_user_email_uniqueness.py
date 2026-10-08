"""Align user email uniqueness with ORM metadata.

Revision ID: 20261008_0003
Revises: 20261008_0002
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20261008_0003"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "20261008_0002"

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
    # 0002 created both a unique constraint
    # and a unique index for users.email.
    #
    # The ORM metadata represents uniqueness
    # through the unique index, so the redundant
    # unique constraint is removed.
    #
    # batch_alter_table keeps this migration
    # compatible with both PostgreSQL and SQLite.
    with op.batch_alter_table(
        "users"
    ) as batch_op:
        batch_op.drop_constraint(
            "uq_users_email",
            type_="unique",
        )


def downgrade() -> None:
    with op.batch_alter_table(
        "users"
    ) as batch_op:
        batch_op.create_unique_constraint(
            "uq_users_email",
            ["email"],
        )
