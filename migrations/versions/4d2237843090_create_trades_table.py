"""create trades table

Revision ID: 4d2237843090
Revises: 
Create Date: 2026-02-23 19:23:30.230267

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4d2237843090"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trades",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_idempotency_key", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("entry_price", sa.Float(), nullable=True),
        sa.Column("exit_price", sa.Float(), nullable=True),
        sa.Column("pnl", sa.Float(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "order_idempotency_key",
            name="uq_order_idempotency_key"
        ),
    )

    op.create_index(
        op.f("ix_trades_id"),
        "trades",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_trades_symbol"),
        "trades",
        ["symbol"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_trades_symbol"), table_name="trades")
    op.drop_index(op.f("ix_trades_id"), table_name="trades")
    op.drop_table("trades")
