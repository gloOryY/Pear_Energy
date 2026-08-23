"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2025-01-01
"""
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Схема создаётся через Base.metadata.create_all (см. ниже).
    # Для прода замените на `alembic revision --autogenerate -m ...`
    from app.db.base import Base
    from app.models import *  # noqa: F401,F403
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    from app.db.base import Base
    from app.models import *  # noqa: F401,F403
    Base.metadata.drop_all(bind=op.get_bind())
