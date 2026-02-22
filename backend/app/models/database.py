import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


class UserDB(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=True)
    subscription_tier = Column(
        Enum("free", "pro", name="subscription_tier"), default="free", nullable=False
    )
    subscription_expires = Column(DateTime(timezone=True), nullable=True)
    daily_takes_used = Column(Integer, default=0, nullable=False)
    daily_problems_used = Column(Integer, default=0, nullable=False)
    daily_reset_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    problems = relationship("ProblemDB", back_populates="user", cascade="all, delete")


class ProblemDB(Base):
    __tablename__ = "problems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("UserDB", back_populates="problems")
    takes = relationship("TakeDB", back_populates="problem", cascade="all, delete")


class TakeDB(Base):
    __tablename__ = "takes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_id = Column(UUID(as_uuid=True), ForeignKey("problems.id"), nullable=False)
    lens_index = Column(Integer, nullable=False)
    headline = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    wise = Column(Boolean, default=True, nullable=False)
    saved = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    problem = relationship("ProblemDB", back_populates="takes")


# ── Engine & Session ───────────────────────────────────

settings = get_settings()
engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
