"""enforce single account

Revision ID: 7b4f792bfc78
Revises: 44e3d408cc23
Create Date: 2026-11-22 12:45:41.162314

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b4f792bfc78'
down_revision: Union[str, Sequence[str], None] = '44e3d408cc23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow at most one user account."""
    op.execute("""
        CREATE UNIQUE INDEX uq_users_single_account
        ON users ((TRUE))
    """)


def downgrade() -> None:
    """Remove the single-account restriction."""
    op.execute("""
        DROP INDEX uq_users_single_account
    """)
