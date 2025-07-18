"""Fix swapped unique constraint names between likes and views.

Revision ID: b7a3db3e8ac5
Revises: c7b6f4c77462
Create Date: 2025-07-17 17:56:15.813887
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "b7a3db3e8ac5"
down_revision: Union[str, Sequence[str], None] = "c7b6f4c77462"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _constraint_exists(bind, table_name: str, constraint_name: str) -> bool:
    insp = inspect(bind)
    for uc in insp.get_unique_constraints(table_name):
        if uc["name"] == constraint_name:
            return True
    return False


def upgrade() -> None:
    """Rename/swap constraints so they match the model definitions."""
    bind = op.get_bind()

    # likes table: should have uq_likes_user_blog
    if _constraint_exists(bind, "likes", "uq_views_user_blog"):
        op.drop_constraint("uq_views_user_blog", "likes", type_="unique")
    if not _constraint_exists(bind, "likes", "uq_likes_user_blog"):
        op.create_unique_constraint("uq_likes_user_blog", "likes", ["user_id", "blog_id"])

    # views table: should have uq_views_user_blog
    if _constraint_exists(bind, "views", "uq_likes_user_blog"):
        op.drop_constraint("uq_likes_user_blog", "views", type_="unique")
    if not _constraint_exists(bind, "views", "uq_views_user_blog"):
        op.create_unique_constraint("uq_views_user_blog", "views", ["user_id", "blog_id"])


def downgrade() -> None:
    """Reverse upgrade: restore swapped names."""
    bind = op.get_bind()

    # views table back to uq_likes_user_blog
    if _constraint_exists(bind, "views", "uq_views_user_blog"):
        op.drop_constraint("uq_views_user_blog", "views", type_="unique")
    if not _constraint_exists(bind, "views", "uq_likes_user_blog"):
        op.create_unique_constraint("uq_likes_user_blog", "views", ["user_id", "blog_id"])

    # likes table back to uq_views_user_blog
    if _constraint_exists(bind, "likes", "uq_likes_user_blog"):
        op.drop_constraint("uq_likes_user_blog", "likes", type_="unique")
    if not _constraint_exists(bind, "likes", "uq_views_user_blog"):
        op.create_unique_constraint("uq_views_user_blog", "likes", ["user_id", "blog_id"])
