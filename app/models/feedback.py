from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, Boolean
from datetime import datetime, timezone
from sqlalchemy import UniqueConstraint
from .base import Base


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True)
    blog_id = Column(Integer, ForeignKey("blogs.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    comment = Column(Text, nullable=False)
    is_listed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))


class View(Base):
    __tablename__ = "views"

    id = Column(Integer, primary_key=True)
    blog_id = Column(Integer, ForeignKey("blogs.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint('user_id', 'blog_id', name='uq_likes_user_blog'),)


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True)
    blog_id = Column(Integer, ForeignKey("blogs.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    is_like = Column(Boolean, nullable=False)  # True = like, False = dislike
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint('user_id', 'blog_id', name='uq_views_user_blog'),)

