"""add_intraday_drawdown_fields

Revision ID: a25c13aed0e3
Revises: 856890eae8a4
Create Date: 2026-03-03 18:43:06.395388

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a25c13aed0e3'
down_revision: Union[str, None] = '856890eae8a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
