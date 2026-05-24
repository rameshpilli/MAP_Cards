"""Database models for MAPrompt Cards."""

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from server.db.base import Base


class Card(Base):
    """A prompt card in the marketplace."""

    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(500), nullable=False)
    author = Column(String(100), nullable=False)
    author_url = Column(String(500), default="")
    category = Column(String(50), nullable=False, index=True)
    tags = Column(JSON, default=list)
    platforms = Column(JSON, default=list)
    prompt = Column(Text, nullable=False)
    variables = Column(JSON, default=list)
    version = Column(String(20), default="1.0.0")
    license = Column(String(50), default="MIT")
    download_count = Column(Integer, default=0)
    avg_rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    trending_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Download(Base):
    """Tracks card downloads."""

    __tablename__ = "downloads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_name = Column(String(100), nullable=False, index=True)
    downloaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ip_hash = Column(String(64), default="anonymous")


class Rating(Base):
    """User ratings for cards."""

    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_name = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=False)
    stars = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("card_name", "user_id", name="uq_card_user_rating"),
    )
