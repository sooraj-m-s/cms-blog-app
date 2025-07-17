from sqlalchemy import Column, Integer, String, DateTime, Boolean
from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(50), index=True)
    email = Column(String(120), unique=True, index=True)
    password = Column(String(255))
    is_blocked = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime)

