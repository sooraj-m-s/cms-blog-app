from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from app.db.base import Base


class Logout(Base):
    __tablename__ = "logouts"

    id = Column(Integer, primary_key=True)
    token = Column(String, nullable=False, unique=True)
    revoked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

