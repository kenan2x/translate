from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Integer, Date, Enum as SAEnum, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PeriodType(str, enum.Enum):
    DAILY = "daily"
    MONTHLY = "monthly"


class QuotaUsage(Base):
    __tablename__ = "quota_usage"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    pages_used: Mapped[int] = mapped_column(Integer, default=0)
    period_type: Mapped[PeriodType] = mapped_column(SAEnum(PeriodType))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
