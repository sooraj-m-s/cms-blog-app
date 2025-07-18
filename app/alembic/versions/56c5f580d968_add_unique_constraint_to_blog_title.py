"""add unique constraint to blog title

Revision ID: 56c5f580d968
Revises: b7a3db3e8ac5
Create Date: 2025-07-17 23:24:04.188399

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '56c5f580d968'
down_revision: Union[str, Sequence[str], None] = 'b7a3db3e8ac5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint('uq_blog_title', 'blogs', ['title'])


def downgrade() -> None:
    op.drop_constraint('uq_blog_title', 'blogs', type_='unique')
