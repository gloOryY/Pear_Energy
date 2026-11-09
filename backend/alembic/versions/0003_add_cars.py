"""add car catalog and user cars

Revision ID: 0003_add_car_catalog_and_user_cars
Revises: 0002_add_station_fields
Create Date: 2026-11-09 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0003_add_cars"
down_revision: Union[str, None] = "0002_add_station_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "car_catalog",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("make", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("battery_capacity_kwh", sa.Float(), nullable=False),
        sa.Column("max_ac_power_kw", sa.Float(), server_default="11.0", nullable=False),
        sa.Column("max_dc_power_kw", sa.Float(), server_default="120.0", nullable=False),
        sa.Column("connector_type", sa.String(length=32), server_default="GB/T", nullable=False),
    )
    op.create_index("ix_car_catalog_id", "car_catalog", ["id"])
    op.create_index("ix_car_catalog_make", "car_catalog", ["make"])
    op.create_index("ix_car_catalog_model", "car_catalog", ["model"])

    op.create_table(
        "user_cars",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("catalog_car_id", sa.Integer(), sa.ForeignKey("car_catalog.id", ondelete="SET NULL"), nullable=True),
        sa.Column("make", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("battery_capacity_kwh", sa.Float(), nullable=False),
        sa.Column("max_ac_power_kw", sa.Float(), server_default="11.0", nullable=False),
        sa.Column("max_dc_power_kw", sa.Float(), server_default="120.0", nullable=False),
        sa.Column("connector_type", sa.String(length=32), server_default="GB/T", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_custom", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_cars_id", "user_cars", ["id"])
    op.create_index("ix_user_cars_user_id", "user_cars", ["user_id"])


def downgrade() -> None:
    op.drop_table("user_cars")
    op.drop_table("car_catalog")
