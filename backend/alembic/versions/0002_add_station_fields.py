"""add station fields

Revision ID: 0002_add_station_fields
Revises: 0001_initial
Create Date: 2026-11-02 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_station_fields"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("stations", sa.Column("image_url", sa.String(length=512), nullable=True))
    op.add_column("stations", sa.Column("tariff_start", sa.Numeric(precision=10, scale=2), server_default=sa.text("0.00"), nullable=False))
    op.add_column("stations", sa.Column("tariff_per_minute", sa.Numeric(precision=10, scale=2), server_default=sa.text("0.00"), nullable=False))

def downgrade() -> None:
    op.drop_column("stations", "tariff_per_minute")
    op.drop_column("stations", "tariff_start")
    op.drop_column("stations", "image_url")
