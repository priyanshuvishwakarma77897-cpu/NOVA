
import hashlib
import secrets

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.auth_session import AuthSession


def generate_session_token() -> str:
    """Generate a cryptographically secure session token."""
    return secrets.token_urlsafe(48)


def hash_session_token(token: str) -> str:
    """Hash a session token before database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(
    db: Session,
    user_id: int,
) -> tuple[str, AuthSession]:
    """Create a new authenticated session."""

    token = generate_session_token()
    token_hash = hash_session_token(token)

    now = datetime.now(timezone.utc)

    session = AuthSession(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=now + timedelta(
            hours=settings.SESSION_TTL_HOURS
        ),
    )

    db.add(session)
    db.flush()

    return token, session


def get_active_session(
    db: Session,
    token: str,
) -> AuthSession | None:
    """Return an active session if its token is valid."""

    token_hash = hash_session_token(token)

    session = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == token_hash
        )
    )

    if session is None:
        return None

    now = datetime.now(timezone.utc)

    if session.revoked_at is not None:
        return None

    if session.expires_at <= now:
        return None

    session.last_used_at = now
    db.flush()

    return session


def revoke_session(
    db: Session,
    token: str,
) -> bool:
    """Revoke an active session."""

    session = get_active_session(db, token)

    if session is None:
        return False

    session.revoked_at = datetime.now(timezone.utc)
    db.flush()

    return True
