"""
Base SQLAlchemy Model
Optimized for high-frequency trading operations
"""
from datetime import datetime
from sqlalchemy import Column, DateTime, BigInteger
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models with common fields"""
    pass


class TimestampMixin:
    """Mixin for timestamp fields with nanosecond precision awareness"""
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True  # Critical for time-series queries
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class SequenceMixin:
    """Mixin for sequence tracking - essential for order matching"""
    sequence_id = Column(
        BigInteger,
        autoincrement=True,
        nullable=False,
        index=True
    )

