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


def upgrade():
    from app.db.base import Base
    from app.models import __all__  # noqa: F401, F403
    Base.metadata.create_all(bind=op.get_bind())


def downgrade():
    from app.db.base import Base
    from app.models import __all__  # noqa: F401, F403
    Base.metadata.drop_all(bind=op.get_bind())
