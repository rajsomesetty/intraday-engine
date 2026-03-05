"""add_intraday_drawdown_fields

Revision ID: <PUT_GENERATED_REVISION_ID_HERE>
Revises: <PUT_PREVIOUS_REVISION_ID_HERE>
Create Date: 2026-03-03

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "<PUT_GENERATED_REVISION_ID_HERE>"
down_revision = "<PUT_PREVIOUS_REVISION_ID_HERE>"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "account",
        sa.Column(
            "intraday_peak_equity",
            sa.Numeric(),
            nullable=False,
            server_default="50000"
        ),
    )

    op.add_column(
        "account",
        sa.Column(
            "current_equity",
            sa.Numeric(),
            nullable=False,
            server_default="50000"
        ),
    )

    op.add_column(
        "account",
        sa.Column(
            "is_trading_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true")
        ),
    )

    # Initialize peak and equity from total_capital
    op.execute("""
        UPDATE account
        SET intraday_peak_equity = total_capital,
            current_equity = total_capital
    """)


def downgrade():
    op.drop_column("account", "is_trading_enabled")
    op.drop_column("account", "current_equity")
    op.drop_column("account", "intraday_peak_equity")
