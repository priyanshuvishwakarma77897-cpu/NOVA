
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text

from backend.app.core.config import settings
from backend.app.database.connection import SessionLocal
from backend.app.models.ai_quota_reservation import AIQuotaReservation
from backend.app.models.ai_usage import AIUsage


class QuotaExceededError(Exception):
    """Raised when an AI request would exceed a quota threshold."""


def get_quota_limits() -> dict[str, int]:
    """Return configured Groq quota limits."""

    return {
        "rpm": settings.GROQ_RPM_LIMIT,
        "rpd": settings.GROQ_RPD_LIMIT,
        "tpm": settings.GROQ_TPM_LIMIT,
        "tpd": settings.GROQ_TPD_LIMIT,
    }


def get_quota_thresholds() -> dict[str, int]:
    """Calculate safety thresholds for configured quotas."""

    return {
        name: int(limit * settings.AI_QUOTA_THRESHOLD)
        for name, limit in get_quota_limits().items()
    }


def check_quota_limits(current_usage: dict[str, int]) -> dict:
    """Check whether projected usage exceeds safety thresholds."""

    thresholds = get_quota_thresholds()

    exceeded = {
        name: current_usage.get(name, 0) >= threshold
        for name, threshold in thresholds.items()
    }

    return {
        "allowed": not any(exceeded.values()),
        "blocked": any(exceeded.values()),
        "thresholds": thresholds,
        "exceeded": exceeded,
    }


def _get_reserved_tokens(reservation: AIQuotaReservation) -> int:
    """Return actual usage if completed, otherwise reserved usage."""

    if reservation.status == "completed":
        return (
            (reservation.actual_input_tokens or 0)
            + (reservation.actual_output_tokens or 0)
        )

    return (
        reservation.estimated_input_tokens
        + reservation.reserved_output_tokens
    )


def reserve_quota(
    provider: str,
    model: str,
    estimated_input_tokens: int,
    reserved_output_tokens: int,
) -> int:
    """
    Reserve quota before sending a request to the AI provider.

    Currently supports Groq only.
    Uses PostgreSQL advisory locking to serialize reservations.
    Daily usage uses a rolling 24-hour window.
    """

    provider = provider.lower().strip()

    if provider != "groq":
        raise ValueError(
            f"Quota policy is not configured for provider: {provider}"
        )

    if model != settings.GROQ_MODEL:
        raise ValueError("Unsupported Groq model.")

    if estimated_input_tokens < 0 or reserved_output_tokens < 1:
        raise ValueError("Invalid token reservation.")

    now = datetime.now(timezone.utc)
    minute_start = now - timedelta(minutes=1)
    day_start = now - timedelta(hours=24)

    with SessionLocal() as db:
        with db.begin():

            # Serialize quota checks across concurrent requests.
            db.execute(
                text("SELECT pg_advisory_xact_lock(782342)")
            )

            reservations = db.scalars(
                select(AIQuotaReservation).where(
                    AIQuotaReservation.provider == provider,
                    AIQuotaReservation.model == model,
                    AIQuotaReservation.created_at >= day_start,
                )
            ).all()

            minute_reservations = [
                item
                for item in reservations
                if item.created_at >= minute_start
            ]

            projected_usage = {
                "rpm": len(minute_reservations) + 1,
                "rpd": len(reservations) + 1,
                "tpm": (
                    sum(
                        _get_reserved_tokens(item)
                        for item in minute_reservations
                    )
                    + estimated_input_tokens
                    + reserved_output_tokens
                ),
                "tpd": (
                    sum(
                        _get_reserved_tokens(item)
                        for item in reservations
                    )
                    + estimated_input_tokens
                    + reserved_output_tokens
                ),
            }

            result = check_quota_limits(projected_usage)

            if not result["allowed"]:
                raise QuotaExceededError(
                    f"AI quota threshold reached: {result['exceeded']}"
                )

            reservation = AIQuotaReservation(
                provider=provider,
                model=model,
                estimated_input_tokens=estimated_input_tokens,
                reserved_output_tokens=reserved_output_tokens,
                status="reserved",
            )

            db.add(reservation)
            db.flush()

            reservation_id = reservation.id

    return reservation_id


def complete_reservation(
    reservation_id: int,
    actual_input_tokens: int,
    actual_output_tokens: int,
) -> None:
    """
    Reconcile a reservation with actual provider usage.

    Saves usage history and completes the reservation
    within the same database transaction.
    """

    if actual_input_tokens < 0 or actual_output_tokens < 0:
        raise ValueError("Actual token counts cannot be negative.")

    with SessionLocal() as db:
        with db.begin():

            db.execute(
                text("SELECT pg_advisory_xact_lock(782342)")
            )

            reservation = db.get(
                AIQuotaReservation,
                reservation_id,
            )

            if reservation is None:
                raise ValueError("Quota reservation not found.")

            if reservation.status != "reserved":
                raise ValueError("Reservation is not pending.")

            reservation.actual_input_tokens = actual_input_tokens
            reservation.actual_output_tokens = actual_output_tokens
            reservation.status = "completed"
            reservation.completed_at = datetime.now(timezone.utc)

            usage_record = AIUsage(
                provider=reservation.provider,
                model=reservation.model,
                input_tokens=actual_input_tokens,
                output_tokens=actual_output_tokens,
                request_count=1,
            )

            db.add(usage_record)


def mark_reservation_uncertain(reservation_id: int) -> None:
    """
    Retain quota when provider processing is uncertain.

    Does not automatically release reservations after
    ambiguous failures.
    """

    with SessionLocal() as db:
        with db.begin():

            db.execute(
                text("SELECT pg_advisory_xact_lock(782342)")
            )

            reservation = db.get(
                AIQuotaReservation,
                reservation_id,
            )

            if reservation is None:
                raise ValueError("Quota reservation not found.")

            if reservation.status == "reserved":
                reservation.status = "failed_uncertain"
                reservation.completed_at = datetime.now(timezone.utc)
