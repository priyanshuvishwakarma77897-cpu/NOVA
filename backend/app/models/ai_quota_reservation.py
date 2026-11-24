from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database.base import Base


class AIQuotaReservation(Base):
    __tablename__ = "ai_quota_reservations"

    id: Mapped[int] = mapped_column(primary_key=True)

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    estimated_input_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    reserved_output_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    actual_input_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    actual_output_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="reserved",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )